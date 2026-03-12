"""
GitHub crawler module.

Searches GitHub for repositories containing Mermaid flowchart/architecture diagrams,
applies rule-based and AI quality filters, renders PNG via mermaid.ink, and saves:
  dataset/<id>/diagram.mmd
  dataset/<id>/diagram.png
  dataset/<id>/context.json   ← repo context for describe.py to reuse
  dataset/metadata.json       ← incremental

Resumable: skips IDs already recorded in dataset/crawl_progress.json and
diagram hashes already in metadata.json.

Usage (via main.py):
  python main.py crawl [--target N] [--add-more N]
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

import env_config
from flowsight.config import (
    DATASET_DIR,
    REAL_METADATA,
    CRAWL_PROGRESS,
    CRAWL_LOG,
    KNOWN_DOC_PATHS,
    PATH_BLACKLIST,
    REPO_QUERIES,
    MAX_PER_REPO,
    MAX_README_CHARS,
    MAX_DOC_CHARS,
    MAX_TREE_CHARS,
    MAX_FILE_CHARS,
    MAX_SELECTED_FILES,
    TARGET_REAL,
)
from flowsight.utils import (
    log as _log,
    load_json,
    save_json,
    http_get,
    render_png,
    openrouter_chat,
    trim,
    markdown_without_codeblocks,
    image_to_data_url,
    load_progress,
    save_progress,
    now_ts,
)


# ── Module-level logger ───────────────────────────────────────────────────────

def log(msg: str) -> None:
    _log(msg, CRAWL_LOG)


# ── GitHub helpers ────────────────────────────────────────────────────────────

def _gh_headers() -> dict:
    token = env_config.get_github_token()
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "FlowSightCrawler/2.0"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def search_repos(query: str, page: int = 1, per_page: int = 30) -> list:
    for attempt in range(4):
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=_gh_headers(),
                params={"q": query, "per_page": per_page, "page": page,
                        "sort": "stars", "order": "desc"},
                timeout=25,
            )
            if r.status_code == 200:
                return r.json().get("items", [])
            if r.status_code in (403, 429):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 65))
                wait = max(reset - int(time.time()), 5) + 3
                log(f"  [rate-limit] waiting {min(wait, 90)}s …")
                time.sleep(min(wait, 90))
            else:
                log(f"  [HTTP {r.status_code}] search failed")
                time.sleep(5)
        except Exception as e:
            log(f"  [network error] {e}")
            time.sleep(5)
    return []


def download_raw(repo_full: str, branch: str, path: str) -> str | None:
    url = f"https://raw.githubusercontent.com/{repo_full}/{branch}/{path}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        log(f"  [raw error] {e}")
    return None


def fetch_docs(repo_full: str, branch: str) -> list[tuple[str, str]]:
    results = []
    for path in KNOWN_DOC_PATHS:
        content = download_raw(repo_full, branch, path)
        if content and "```mermaid" in content.lower():
            results.append((path, content))
        time.sleep(0.2)
    return results


def fetch_repo_tree(repo: str, branch: str) -> list[str]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    r = http_get(url, headers=_gh_headers(), timeout=45)
    if r is None or r.status_code != 200:
        return []
    return [item["path"] for item in r.json().get("tree", []) if item.get("type") == "blob"]


def fetch_readme(repo: str, branch: str) -> str:
    for path in ("README.md", "readme.md", "Readme.md", "README.MD"):
        content = download_raw(repo, branch, path)
        if content:
            return trim(markdown_without_codeblocks(content), MAX_README_CHARS)
    return "README not available."


def fetch_source_doc(raw_url: str) -> str:
    r = http_get(raw_url, headers={"User-Agent": "FlowSightCrawler/2.0"}, timeout=30)
    if r is None or r.status_code != 200:
        return "Source document not available."
    try:
        text = r.content.decode("utf-8")
    except UnicodeDecodeError:
        text = r.text
    return trim(markdown_without_codeblocks(text), MAX_DOC_CHARS)


def extract_local_doc_context(doc_text: str, mermaid_code: str) -> str:
    norm_target = re.sub(r"\s+", "", mermaid_code.strip())
    for m in re.finditer(r"```mermaid\s*\n([\s\S]*?)\n\s*```", doc_text, re.IGNORECASE):
        if re.sub(r"\s+", "", m.group(1).strip()) == norm_target:
            pre = doc_text[: m.start()].splitlines()[-35:]
            post = doc_text[m.end() :].splitlines()[:35]
            return trim("\n".join(pre + ["[MERMAID DIAGRAM LOCATION]"] + post), MAX_DOC_CHARS)
    return trim(doc_text, MAX_DOC_CHARS)


# ── Mermaid parsing and filtering ─────────────────────────────────────────────

def extract_mermaid_blocks(content: str) -> list[str]:
    blocks = re.findall(r"```mermaid\s*\n([\s\S]*?)\n\s*```", content, re.IGNORECASE)
    return [b.strip() for b in blocks if b.strip()]


def is_flowchart(code: str) -> bool:
    first = code.strip().split("\n")[0].strip().lower()
    return bool(re.match(r"^(graph|flowchart)(\s+(td|lr|tb|rl|bt|ltr|rtl))?[\s;(\n]", first + "\n"))


def structural_hash(code: str) -> int:
    normalized = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}|"[^"]*"', "", code, flags=re.DOTALL)
    normalized = re.sub(r"%%.*", "", normalized)
    edges = re.findall(
        r"(\b[A-Za-z_][\w]*)\s*(?:-->|==>|---|-\.->|--)\s*(?:\|[^|]*\|)?\s*(\b[A-Za-z_][\w]*)",
        normalized,
    )
    if not edges:
        return hash(code)
    return hash(tuple(sorted(f"{s}>{t}" for s, t in edges)))


def is_non_english_readme(path: str) -> bool:
    return bool(re.search(r"(?i)readme\.[a-z]{2,5}(-[a-z]{2,4})?\.md$", path))


def rule_filter(code: str, file_path: str) -> tuple[bool, str]:
    path_lower = file_path.lower()
    for kw in PATH_BLACKLIST:
        if kw in path_lower:
            return False, f"blacklisted path: {kw}"
    lines = code.strip().splitlines()
    if len(lines) < 6:
        return False, f"too few lines ({len(lines)})"
    labels = re.findall(r'[\[\(\{"\|]([^\[\]\(\)\{\}"\|]{2,60})[\]\)\}"\|]', code)
    bare = re.findall(r"(?:^|\s|-->|==>|---)([A-Za-z][A-Za-z0-9_]{1,})", code)
    all_names = labels + bare
    if len(all_names) < 4:
        return False, f"too few labels ({len(all_names)})"
    trivial = [n for n in all_names if re.match(r"^[A-Z0-9]{1,2}$", n.strip())]
    if len(trivial) > len(all_names) * 0.6:
        return False, f"high single-letter-label ratio ({len(trivial)}/{len(all_names)})"
    test_words = (
        "lorem", "ipsum", "foo", "bar", "baz", "test", "demo",
        "example", "sample", "placeholder", "dummy", "fake", "mock",
    )
    if sum(1 for w in test_words if w in code.lower()) >= 3:
        return False, "contains many test/placeholder words"
    arrows = len(re.findall(r"-->|==>|---|-\.->|==>", code))
    if arrows < 3:
        return False, f"too few edges ({arrows})"
    return True, ""


# ── AI quality check ──────────────────────────────────────────────────────────

def ai_quality_check(code: str, api_key: str, model: str) -> tuple[bool, str]:
    """
    Ask the LLM whether the Mermaid diagram has real practical value
    (genuine system architecture / business process / technical workflow / data flow)
    rather than being a tutorial example, syntax demo, test fixture, or placeholder.
    """
    prompt = (
        "Below is a Mermaid flowchart/architecture diagram. "
        "Determine whether it has **real practical value** — i.e., whether it describes "
        "a genuine system architecture, business process, technical workflow, or data flow, "
        "rather than a tutorial example, syntax demonstration, test fixture, or placeholder.\n\n"
        "All three criteria must be met to pass:\n"
        "1. Node labels are meaningful names (real components, services, or steps — not 'A', 'B', 'Node1').\n"
        "2. The overall diagram expresses clear technical or business logic.\n"
        "3. It is NOT a Mermaid syntax demo or tutorial.\n\n"
        f"```mermaid\n{code}\n```\n\n"
        'Reply with JSON only — no other text: {"pass": true/false, "reason": "one sentence"}'
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    log(f"  [ai_quality_check] embedded error: {data['error'].get('message','')[:120]}")
                    time.sleep(4)
                    continue
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    log(f"  [ai_quality_check] content=null")
                    time.sleep(4)
                    continue
                text = content.strip()
                m = re.search(r"\{.*?\}", text, re.DOTALL)
                if m:
                    obj = json.loads(m.group())
                    return bool(obj.get("pass")), obj.get("reason", "")
                return ("true" in text.lower()), text[:80]
            log(f"  [ai_quality_check] HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code in (401, 402, 403):
                log("  [ai_quality_check] Fatal auth error — admitting by default")
                return True, "auth error — admitted by default"
            time.sleep(4)
        except Exception as e:
            log(f"  [ai_quality_check error] {e}")
            time.sleep(4)
    return True, "quality check failed — admitted by default"


# ── Relevant file selection ───────────────────────────────────────────────────

def select_relevant_files(
    repo: str,
    branch: str,
    file_path: str,
    mermaid_code: str,
    readme_text: str,
    repo_tree: list[str],
    api_key: str,
    model: str,
) -> list[str]:
    """
    Ask the LLM to pick the ≤MAX_SELECTED_FILES most relevant source/config files
    from the repository tree for explaining this diagram.
    """
    tree_text = trim("\n".join(repo_tree), MAX_TREE_CHARS)
    prompt = (
        f"You are selecting the most informative files from a GitHub repository "
        f"to help explain a Mermaid diagram.\n\n"
        f"Goal: Given the README, the full repository file tree, the document path containing "
        f"the diagram, and the Mermaid source, choose at most {MAX_SELECTED_FILES} files that "
        f"best explain the components, flows, or terms in the diagram.\n\n"
        f"Prioritise: source code and config files that map directly to diagram nodes or edges. "
        f"Exclude: images, lock files, test files, build artefacts, and binary files.\n\n"
        f'Return JSON only: {{"files": ["path1", "path2", ...]}}\n\n'
        f"Repository: {repo}  Branch: {branch}  Diagram source file: {file_path}\n\n"
        f"README:\n{readme_text}\n\n"
        f"Mermaid diagram:\n```mermaid\n{mermaid_code}\n```\n\n"
        f"Full repository file tree:\n{tree_text}"
    )
    answer = openrouter_chat(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        model=model,
        max_tokens=300,
        temperature=0.1,
    )
    if not answer:
        return []
    m = re.search(r"\{[\s\S]*\}", answer)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
        files = obj.get("files", [])
        if not isinstance(files, list):
            return []
        return [f for f in files if isinstance(f, str)][:MAX_SELECTED_FILES]
    except Exception:
        return []


def fetch_selected_file_snippets(
    repo: str, branch: str, paths: list[str]
) -> list[str]:
    out = []
    for path in paths[:MAX_SELECTED_FILES]:
        content = download_raw(repo, branch, path)
        if not content:
            continue
        out.append(f"[File] {path}\n{trim(content, MAX_FILE_CHARS)}")
        time.sleep(0.2)
    return out


# ── Main crawl entry ──────────────────────────────────────────────────────────

def run(target: int | None = None, add_more: int | None = None) -> None:
    """
    Crawl GitHub and collect real Mermaid diagrams.

    If dataset/metadata.json already exists the crawler resumes from where it left off.
    Pass add_more to collect N additional samples on top of what already exists.
    """
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    api_key = env_config.get_openrouter_api_key()
    model = env_config.get_generation_model()
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set — aborting crawl.")
        return

    # Load existing metadata
    all_metadata: list[dict] = load_json(REAL_METADATA, default=[])
    collected = len(all_metadata)

    if add_more is not None:
        goal = collected + add_more
    elif target is not None:
        goal = max(target, collected)
    else:
        goal = max(TARGET_REAL, collected)

    log(f"[crawl] collected={collected}, goal={goal}")

    seen_hashes: set[int] = {m.get("mermaid_hash", 0) for m in all_metadata}
    seen_struct: set[int] = {m.get("struct_hash", 0) for m in all_metadata}
    seen_repos: set[str] = {m["repo"] for m in all_metadata}
    repo_structs: dict[str, set[int]] = {}
    for m in all_metadata:
        repo_structs.setdefault(m["repo"], set()).add(m.get("struct_hash", 0))

    stats = {"rule_rej": 0, "ai_rej": 0, "struct_dup": 0, "png_fail": 0}

    for query in REPO_QUERIES:
        if collected >= goal:
            break
        log(f"\n[search] {query}")
        time.sleep(2)

        for page in range(1, 5):
            if collected >= goal:
                break
            repos = search_repos(query, page=page, per_page=30)
            if not repos:
                log(f"  page {page}: no results")
                break
            log(f"  page {page}: {len(repos)} repos")
            time.sleep(2)

            for repo_info in repos:
                if collected >= goal:
                    break
                repo_full = repo_info["full_name"]
                stars = repo_info.get("stargazers_count", 0)
                branch = repo_info.get("default_branch", "main")
                if repo_full in seen_repos:
                    continue
                seen_repos.add(repo_full)
                log(f"\n  [{repo_full}] stars={stars} branch={branch}")

                docs = fetch_docs(repo_full, branch)
                if not docs:
                    log("    no Mermaid-containing docs found")
                    continue
                log(f"    found {len(docs)} doc(s) with Mermaid")

                found_in_repo = 0
                for md_path, content in docs:
                    if collected >= goal:
                        break
                    raw_url = (
                        f"https://raw.githubusercontent.com/{repo_full}/{branch}/{md_path}"
                    )
                    for block in extract_mermaid_blocks(content):
                        if collected >= goal:
                            break
                        ok, collected = _try_save(
                            block=block,
                            repo_full=repo_full,
                            stars=stars,
                            branch=branch,
                            md_path=md_path,
                            raw_url=raw_url,
                            all_metadata=all_metadata,
                            seen_hashes=seen_hashes,
                            seen_struct=seen_struct,
                            repo_structs=repo_structs,
                            stats=stats,
                            collected=collected,
                            goal=goal,
                            api_key=api_key,
                            model=model,
                        )
                        if ok:
                            found_in_repo += 1
                            time.sleep(1.5)

                if found_in_repo:
                    log(f"    contributed {found_in_repo} sample(s) from this repo")
            time.sleep(3)

    log(
        f"\n{'='*50}\n[crawl done] collected={collected}/{goal} | "
        f"rule_rej={stats['rule_rej']} ai_rej={stats['ai_rej']} "
        f"struct_dup={stats['struct_dup']} png_fail={stats['png_fail']}"
    )


def _try_save(
    block: str,
    repo_full: str,
    stars: int,
    branch: str,
    md_path: str,
    raw_url: str,
    all_metadata: list,
    seen_hashes: set,
    seen_struct: set,
    repo_structs: dict,
    stats: dict,
    collected: int,
    goal: int,
    api_key: str,
    model: str,
) -> tuple[bool, int]:
    """Attempt to add one diagram block to the dataset. Returns (saved, new_collected)."""
    if not is_flowchart(block) or len(block) < 40 or len(block) > 12_000:
        return False, collected
    if is_non_english_readme(md_path):
        return False, collected

    h = hash(block)
    sh = structural_hash(block)

    if h in seen_hashes:
        return False, collected
    if sh in seen_struct:
        stats["struct_dup"] += 1
        seen_hashes.add(h)
        log(f"    [struct-dup] {md_path[:55]}")
        return False, collected

    repo_sh = repo_structs.setdefault(repo_full, set())
    if sh in repo_sh:
        stats["struct_dup"] += 1
        seen_hashes.add(h)
        log(f"    [intra-repo dup] {md_path[:55]}")
        return False, collected
    if len(repo_sh) >= MAX_PER_REPO:
        seen_hashes.add(h)
        log(f"    [repo cap {MAX_PER_REPO}] {md_path[:55]}")
        return False, collected

    ok, reason = rule_filter(block, md_path)
    if not ok:
        stats["rule_rej"] += 1
        seen_hashes.add(h)
        log(f"    [rule-reject] {reason} | {md_path[:50]}")
        return False, collected

    ai_ok, ai_reason = ai_quality_check(block, api_key, model)
    seen_hashes.add(h)
    if not ai_ok:
        stats["ai_rej"] += 1
        log(f"    [ai-reject] {ai_reason[:60]} | {md_path[:50]}")
        return False, collected

    log(f"    [passed] {ai_reason[:60]}")

    entry_dir = DATASET_DIR / f"{collected:03d}"
    entry_dir.mkdir(exist_ok=True)
    (entry_dir / "diagram.mmd").write_text(block, encoding="utf-8")

    png_path = entry_dir / "diagram.png"
    if not render_png(block, png_path):
        log("      PNG render failed — skipping")
        (entry_dir / "diagram.mmd").unlink(missing_ok=True)
        entry_dir.rmdir()
        stats["png_fail"] += 1
        return False, collected

    # Gather and persist repo context so describe.py can reuse without re-fetching
    repo_tree = fetch_repo_tree(repo_full, branch)
    readme_text = fetch_readme(repo_full, branch)
    source_doc = fetch_source_doc(raw_url)
    doc_context = extract_local_doc_context(source_doc, block)
    selected_files = select_relevant_files(
        repo_full, branch, md_path, block, readme_text, repo_tree, api_key, model
    )
    log(f"      [context] selected_files={selected_files}")
    snippets = fetch_selected_file_snippets(repo_full, branch, selected_files)

    context = {
        "repo": repo_full,
        "branch": branch,
        "file_path": md_path,
        "raw_url": raw_url,
        "repo_tree": repo_tree,
        "readme_text": readme_text,
        "doc_context": doc_context,
        "selected_files": selected_files,
        "snippets": snippets,
    }
    save_json(entry_dir / "context.json", context)

    repo_sh.add(sh)
    seen_struct.add(sh)

    meta_entry = {
        "id": collected,
        "repo": repo_full,
        "repo_stars": stars,
        "file_path": md_path,
        "branch": branch,
        "raw_url": raw_url,
        "mermaid_hash": h,
        "struct_hash": sh,
        "mermaid_lines": len(block.splitlines()),
        "ai_reason": ai_reason,
        "files": {
            "mermaid": f"dataset/{collected:03d}/diagram.mmd",
            "png": f"dataset/{collected:03d}/diagram.png",
            "context": f"dataset/{collected:03d}/context.json",
            "description": f"dataset/{collected:03d}/description.txt",
            "qa": f"dataset/{collected:03d}/qa.json",
        },
    }
    all_metadata.append(meta_entry)
    save_json(REAL_METADATA, all_metadata)

    collected += 1
    log(
        f"      [saved] {collected}/{goal} → {entry_dir.name}/ "
        f"(rule_rej={stats['rule_rej']} ai_rej={stats['ai_rej']} struct_dup={stats['struct_dup']})"
    )
    return True, collected
