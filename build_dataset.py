#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowSight 数据集一次性构建脚本：从 GitHub 爬取 Mermaid 图 → 渲染 PNG → 直接生成当前格式的 description。

输出与现有 dataset/ 等价：
- 每样本目录：diagram.mmd、diagram.png、description.txt（7 节结构化中文）
- dataset/metadata.json：顶层 JSON 数组，每项含 id, repo, repo_stars, file_path, branch, raw_url,
  mermaid_hash, struct_hash, mermaid_lines, ai_reason, files: { mermaid, png, description }
- 仅当 mmd+png+description 全部成功时才写入目录并追加 metadata，保证无孤儿目录
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
from pathlib import Path

import requests

# ── 配置 ──────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = "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"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

_SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = _SCRIPT_DIR / "dataset"
LOG_FILE = OUTPUT_DIR / "build.log"

TARGET_COUNT = 100
ADD_MORE = int(os.environ.get("ADD_MORE", "100"))
MAX_PER_REPO = 3

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MERMAID_INK = "https://mermaid.ink/img/{encoded}?type=png"

# expand 阶段字符上限
MAX_TREE_CHARS = 30000
MAX_README_CHARS = 6000
MAX_DOC_CHARS = 7000
MAX_FILE_CHARS = 3000
MAX_SELECTED_FILES = 6

KNOWN_DOC_PATHS = [
    "README.md", "ARCHITECTURE.md", "DESIGN.md", "OVERVIEW.md",
    "docs/README.md", "docs/architecture.md", "docs/design.md", "docs/overview.md",
    "doc/README.md", "doc/architecture.md", "documentation/README.md", "wiki/Home.md",
    ".github/README.md", "docs/getting-started.md", "docs/guide.md", "docs/workflow.md",
    "docs/flow.md", "docs/system-design.md", "docs/infrastructure.md", "docs/deployment.md",
]

PATH_BLACKLIST = (
    "/test", "/spec", "/example", "/sample", "/demo",
    "/fixture", "/mock", "/stub", "/playground",
)

REPO_QUERIES = [
    '"graph TD" mermaid in:readme', '"graph LR" mermaid in:readme',
    '"flowchart TD" in:readme', '"flowchart LR" in:readme', '"graph TB" mermaid in:readme',
    'mermaid architecture in:readme microservices', 'mermaid diagram in:readme kubernetes',
    'mermaid flowchart in:readme CI/CD', 'mermaid graph in:readme "system design"',
    'mermaid architecture in:readme backend', 'mermaid diagram in:readme cloud',
    'mermaid graph in:readme "API gateway"', 'mermaid flow in:readme deployment',
    'mermaid diagram in:readme database', 'mermaid graph in:readme authentication',
    'mermaid diagram in:readme pipeline', 'mermaid architecture in:readme docker',
    'mermaid graph in:readme workflow', 'mermaid diagram in:readme "event driven"',
    'mermaid architecture in:readme infrastructure', 'mermaid flowchart in:readme serverless',
    'mermaid graph in:readme "data flow"', 'mermaid diagram in:readme monitoring',
    'mermaid graph in:readme "load balancer"', 'mermaid diagram in:readme "message queue"',
    'mermaid flowchart in:readme "state machine"', 'mermaid graph in:readme "distributed system"',
    'mermaid diagram in:readme "monitoring"', 'mermaid architecture in:readme "security"',
    'mermaid graph in:readme "caching"', 'mermaid flowchart in:readme "onboarding"',
    'mermaid diagram in:readme "testing"', 'mermaid graph in:readme "logging"',
    'mermaid architecture in:readme "scalability"', 'mermaid diagram in:readme "messaging"',
    'mermaid graph in:readme "sync"', 'mermaid flowchart in:readme "approval"',
    'mermaid diagram in:readme "migration"', 'mermaid graph in:readme "gateway"',
    'mermaid architecture in:readme "multi-tenant"', 'mermaid diagram in:readme "batch"',
    'mermaid graph in:readme "real-time"',
]

GH_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "ResearchDatasetCollector/1.0"}
if GITHUB_TOKEN:
    GH_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

OR_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/dataset-builder",
    "X-Title": "FlowSight Dataset Build",
}


def log(msg: str) -> None:
    safe = msg.encode("gbk", errors="replace").decode("gbk")
    try:
        print(safe, flush=True)
    except Exception:
        pass
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ── GitHub 搜索与 raw 下载 ────────────────────────────────────────────────────
def search_repos(query: str, page: int = 1, per_page: int = 30) -> list:
    for attempt in range(4):
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=GH_HEADERS,
                params={"q": query, "per_page": per_page, "page": page, "sort": "stars", "order": "desc"},
                timeout=25,
            )
            if r.status_code == 200:
                return r.json().get("items", [])
            if r.status_code in (403, 429):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 65))
                wait = max(reset - int(time.time()), 5) + 3
                log(f"  [限速] 等待 {min(wait,90)}s ...")
                time.sleep(min(wait, 90))
            else:
                log(f"  [HTTP {r.status_code}] 搜索失败")
                time.sleep(5)
        except Exception as e:
            log(f"  [网络异常] {e}")
            time.sleep(5)
    return []


def download_raw(repo_full: str, branch: str, path: str) -> str | None:
    url = f"https://raw.githubusercontent.com/{repo_full}/{branch}/{path}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        log(f"  [raw 异常] {e}")
    return None


def fetch_docs(repo_full: str, branch: str) -> list[tuple[str, str]]:
    results = []
    for path in KNOWN_DOC_PATHS:
        content = download_raw(repo_full, branch, path)
        if content and "```mermaid" in content.lower():
            results.append((path, content))
        time.sleep(0.2)
    return results


# ── Mermaid 解析与过滤 ────────────────────────────────────────────────────────
def extract_mermaid_blocks(content: str) -> list[str]:
    blocks = re.findall(r"```mermaid\s*\n([\s\S]*?)\n\s*```", content, re.IGNORECASE)
    return [b.strip() for b in blocks if b.strip()]


def is_flowchart(code: str) -> bool:
    first = code.strip().split("\n")[0].strip().lower()
    return bool(re.match(r"^(graph|flowchart)(\s+(td|lr|tb|rl|bt|ltr|rtl))?[\s;(\n]", first + "\n"))


def structural_hash(code: str) -> int:
    normalized = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}|"[^"]*"', '', code, flags=re.DOTALL)
    normalized = re.sub(r'%%.*', '', normalized)
    edges = re.findall(
        r'(\b[A-Za-z_][\w]*)\s*(?:-->|==>|---|-\.->|--)\s*(?:\|[^|]*\|)?\s*(\b[A-Za-z_][\w]*)',
        normalized,
    )
    if not edges:
        return hash(code)
    return hash(tuple(sorted(f"{s}>{t}" for s, t in edges)))


def is_non_english_readme(path: str) -> bool:
    return bool(re.search(r'(?i)readme\.[a-z]{2,5}(-[a-z]{2,4})?\.md$', path))


def rule_filter(code: str, file_path: str) -> tuple[bool, str]:
    path_lower = file_path.lower()
    for kw in PATH_BLACKLIST:
        if kw in path_lower:
            return False, f"黑名单路径: {kw}"
    lines = code.strip().splitlines()
    if len(lines) < 6:
        return False, f"行数太少({len(lines)}行)"
    labels = re.findall(r'[\[\(\{"\|]([^\[\]\(\)\{\}"\|]{2,60})[\]\)\}"\|]', code)
    bare = re.findall(r'(?:^|\s|-->|==>|---)([A-Za-z][A-Za-z0-9_]{1,})', code)
    all_names = labels + bare
    if len(all_names) < 4:
        return False, f"标签太少({len(all_names)}个)"
    trivial = [n for n in all_names if re.match(r'^[A-Z0-9]{1,2}$', n.strip())]
    if len(trivial) > len(all_names) * 0.6:
        return False, f"单字母标签占比高({len(trivial)}/{len(all_names)})"
    test_words = ("lorem", "ipsum", "foo", "bar", "baz", "test", "demo", "example", "sample", "placeholder", "dummy", "fake", "mock")
    if sum(1 for w in test_words if w in code.lower()) >= 3:
        return False, "含大量测试词"
    arrows = len(re.findall(r'-->|==>|---|-\.->|==>', code))
    if arrows < 3:
        return False, f"连线数太少({arrows}条)"
    return True, ""


def ai_quality_check(code: str) -> tuple[bool, str]:
    prompt = (
        "下面是一段 Mermaid 流程图/架构图代码。请判断它是否具有实际价值——\n"
        "即：是否描述了真实系统的架构、业务流程、技术工作流、数据流等，\n"
        "而不是教学示例、语法演示、测试用例或随机占位内容。\n\n"
        "判断标准（全部满足才算有价值）：\n"
        "1. 节点有有意义的名称（描述真实组件/步骤）\n"
        "2. 整体表达了清晰的技术或业务逻辑\n"
        "3. 不是 Mermaid 语法的演示或教程\n\n"
        f"```mermaid\n{code}\n```\n\n"
        '请只回复 JSON，格式：{"pass": true/false, "reason": "一句话"}\n不要输出其他内容。'
    )
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.1,
    }
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=OR_HEADERS, json=payload, timeout=30)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"].strip()
                m = re.search(r'\{.*?\}', text, re.DOTALL)
                if m:
                    obj = json.loads(m.group())
                    return bool(obj.get("pass")), obj.get("reason", "")
                return ("true" in text.lower()), text[:80]
            log(f"  [AI质检 {r.status_code}]")
            time.sleep(4)
        except Exception as e:
            log(f"  [AI质检异常] {e}")
            time.sleep(4)
    return True, "质检失败放行"


# ── PNG 渲染 ──────────────────────────────────────────────────────────────────
def render_png(mermaid_code: str, out_path: Path) -> bool:
    encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
    url = MERMAID_INK.format(encoded=encoded)
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=45)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("image" in ct or len(r.content) > 1000):
                out_path.write_bytes(r.content)
                return True
            log(f"    [mermaid.ink {r.status_code}]")
            time.sleep(3)
        except Exception as e:
            log(f"    [mermaid.ink 异常] {e}")
            time.sleep(4)
    return False


# ── 扩展描述：仓库树 / README / 文档 / 选文件 / 多模态生成 ───────────────────────
def http_get(url: str, headers: dict | None = None, timeout: int = 30) -> requests.Response | None:
    hdrs = headers or GH_HEADERS
    for attempt in range(3):
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 429):
                wait_s = 8 * (attempt + 1)
                log(f"[等待] GET {r.status_code} ... {wait_s}s")
                time.sleep(wait_s)
            else:
                return r
        except Exception as e:
            log(f"[网络异常] GET -> {e}")
            time.sleep(3 * (attempt + 1))
    return None


def openrouter_chat(messages: list, max_tokens: int = 1800, temperature: float = 0.2) -> str | None:
    payload = {"model": "google/gemini-2.0-flash-001", "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=OR_HEADERS, json=payload, timeout=120)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            log(f"[OpenRouter {r.status_code}] attempt={attempt + 1}")
            time.sleep(6 * (attempt + 1))
        except Exception as e:
            log(f"[OpenRouter异常] attempt={attempt + 1} -> {e}")
            time.sleep(6 * (attempt + 1))
    return None


def trim(text: str, max_chars: int) -> str:
    text = text.strip()
    return text if len(text) <= max_chars else text[:max_chars] + "\n... [截断]"


def markdown_without_codeblocks(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "[代码块已省略]", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text_response(r: requests.Response) -> str:
    try:
        return r.content.decode("utf-8")
    except UnicodeDecodeError:
        return r.text


def fetch_repo_tree(repo: str, branch: str) -> list[str]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    r = http_get(url, timeout=45)
    if r is None or r.status_code != 200:
        return []
    return [item["path"] for item in r.json().get("tree", []) if item.get("type") == "blob"]


def fetch_readme(repo: str, branch: str) -> str:
    for path in ("README.md", "readme.md", "Readme.md", "README.MD"):
        content = download_raw(repo, branch, path)
        if content:
            return trim(markdown_without_codeblocks(content), MAX_README_CHARS)
    return "未获取到 README。"


def fetch_source_doc(raw_url: str) -> str:
    r = http_get(raw_url, headers={"User-Agent": "FlowSightBuild/1.0"}, timeout=30)
    if r is None or r.status_code != 200:
        return "未获取到图所在文档。"
    return trim(markdown_without_codeblocks(read_text_response(r)), MAX_DOC_CHARS)


def normalize_mermaid(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def extract_local_doc_context(doc_text: str, mermaid_code: str) -> str:
    matches = list(re.finditer(r"```mermaid\s*\n([\s\S]*?)\n\s*```", doc_text, re.IGNORECASE))
    norm_target = normalize_mermaid(mermaid_code)
    for m in matches:
        block = m.group(1).strip()
        if normalize_mermaid(block) == norm_target:
            pre = doc_text[:m.start()].splitlines()[-35:]
            post = doc_text[m.end():].splitlines()[:35]
            return trim("\n".join(pre + ["[MERMAID图位置]"] + post), MAX_DOC_CHARS)
    return trim(doc_text, MAX_DOC_CHARS)


def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def select_relevant_files(
    repo: str, branch: str, file_path: str, mermaid_code: str, readme_text: str, repo_tree: list[str],
) -> list[str]:
    tree_text = trim("\n".join(repo_tree), MAX_TREE_CHARS)
    prompt = f"""
你要从一个 GitHub 仓库里挑选“最值得读”的代码/配置文件，用来解释一张 Mermaid 图。
目标：根据 README、完整仓库目录树、图所在文档路径、Mermaid 图本身，挑出最相关的文件；优先选能解释图中组件/流程/术语的文件；不要选图片、锁文件、测试、构建产物；最多返回 {MAX_SELECTED_FILES} 个文件。
只返回 JSON，格式：{{"files":["path1","path2"]}}。

仓库：{repo}  分支：{branch}  图所在文档：{file_path}

README：
{readme_text}

Mermaid：
```mermaid
{mermaid_code}
```

完整仓库目录树：
{tree_text}
""".strip()
    answer = openrouter_chat([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.1)
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


def fetch_selected_file_snippets(repo: str, branch: str, paths: list[str]) -> list[str]:
    out = []
    for path in paths[:MAX_SELECTED_FILES]:
        content = download_raw(repo, branch, path)
        if not content:
            continue
        out.append(f"[文件] {path}\n{trim(content, MAX_FILE_CHARS)}")
        time.sleep(0.2)
    return out


def generate_full_description(
    repo: str,
    branch: str,
    file_path: str,
    repo_tree: list[str],
    readme_text: str,
    doc_context: str,
    mermaid_code: str,
    image_path: Path,
    selected_files: list[str],
    selected_snippets: list[str],
) -> str | None:
    tree_text = trim("\n".join(repo_tree), MAX_TREE_CHARS)
    snippet_text = "\n\n".join(selected_snippets) if selected_snippets else "未选择到额外代码文件。"
    selected_text = ", ".join(selected_files) if selected_files else "无"

    format_spec = """
输出格式必须严格固定为下面 7 个一级标题，标题名不能改，顺序不能变：

## 图类型与用途
用 2-4 句说明图属于什么类型、描述什么对象、在仓库中承担什么作用。

## 图的整体布局
用 1-3 句说明方向（TD/LR/TB 等）、总体层次、是否从上到下/从左到右、起点终点在哪。

## 分组/子图/阶段说明
如果图里有 subgraph / stage / lane / phase，就逐项说明；如果没有，也要明确写“图中没有显式子图/分组，但逻辑上可分为……阶段”。

## 节点逐项说明
必须逐项列出关键节点，推荐统一句式：
- **节点ID或标签**：图上含义。若能从 README/代码确认其职责，则补一句仓库语境；若不能确认，写“图中可见，但仓库上下文未进一步说明”。

## 连线、分支与汇聚关系
必须按“源节点 -> 目标节点”的格式分条写，若有条件文字，用：
- `A -> B`：说明
- `D -- Yes --> E`：说明
若多个节点汇聚到一个节点，要明确写“形成汇聚关系”。

## 仓库语境与术语解释
列 3-8 条，仅解释和该图相关的术语、模块、文件、配置；要尽量引用已选代码文件或 README。

## 可作为 QA Ground Truth 的高信息密度摘要
写成一段高信息密度摘要，必须覆盖：起点、关键分支、核心中间节点、终点、至少 1-2 个仓库语境锚点。
""".strip()

    text_prompt = f"""
你现在要为一个 Mermaid 数据集生成“扩展描述” description。

标注目标：
1. 信息量必须 >= 图片本身，读者仅凭这份文字就应能大致重画出图；
2. 需要尊重仓库真实信息：优先依据 README、图所在文档、仓库目录树、所选代码文件；
3. 对图中的术语、组件和流程做解释，但不能编造超出上下文的信息；
4. 这份文字后续会被当作 QA 生成的 ground truth，所以要覆盖图中的显式信息、隐含结构和仓库语境；
5. 如果某个解释只在图中可见、代码/README 未进一步说明，就要明确写“图中可见，但仓库上下文未进一步说明”。

请严格按下面格式规范输出。每个一级标题下都必须有内容，不能省略。输出中文。

格式规范：
{format_spec}

仓库：{repo}  分支：{branch}  图所在文档：{file_path}

Mermaid 源码：
```mermaid
{mermaid_code}
```

README 上下文：
{readme_text}

图所在文档上下文：
{doc_context}

完整仓库目录树：
{tree_text}

LLM 选择的相关文件：{selected_text}

相关代码/配置文件内容：
{snippet_text}
""".strip()

    image_data_url = image_to_data_url(image_path)
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": text_prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ],
    }]
    return openrouter_chat(messages, max_tokens=2200, temperature=0.2)


# ── 主流程：单块尝试入库（含直接生成 full description）────────────────────────
def try_save(
    block: str,
    repo_full: str,
    stars: int,
    branch: str,
    md_path: str,
    raw_url: str,
    all_metadata: list,
    meta_path: Path,
    seen_hashes: set,
    seen_struct_hash: set,
    repo_struct: dict,
    stats: dict,
    collected: int,
    target: int,
) -> tuple[bool, int]:
    if not is_flowchart(block) or len(block) < 40 or len(block) > 12000:
        return False, collected
    if is_non_english_readme(md_path):
        return False, collected

    h, sh = hash(block), structural_hash(block)
    if h in seen_hashes:
        return False, collected
    if sh in seen_struct_hash:
        stats["struct_dup"] += 1
        seen_hashes.add(h)
        log(f"    [结构重复] {md_path[:55]}")
        return False, collected
    repo_structs = repo_struct.setdefault(repo_full, set())
    if sh in repo_structs:
        stats["struct_dup"] += 1
        seen_hashes.add(h)
        log(f"    [仓库内重复] {md_path[:55]}")
        return False, collected
    if len(repo_structs) >= MAX_PER_REPO:
        seen_hashes.add(h)
        log(f"    [仓库上限{MAX_PER_REPO}] {md_path[:55]}")
        return False, collected

    ok, reason = rule_filter(block, md_path)
    if not ok:
        stats["rule_rej"] += 1
        seen_hashes.add(h)
        log(f"    [规则拒] {reason} | {md_path[:50]}")
        return False, collected

    ai_ok, ai_reason = ai_quality_check(block)
    seen_hashes.add(h)
    if not ai_ok:
        stats["ai_rej"] += 1
        log(f"    [AI拒] {ai_reason[:60]} | {md_path[:50]}")
        return False, collected

    log(f"    [通过] {ai_reason[:60]}")

    entry_dir = OUTPUT_DIR / f"{collected:03d}"
    entry_dir.mkdir(exist_ok=True)
    (entry_dir / "diagram.mmd").write_text(block, encoding="utf-8")

    png_path = entry_dir / "diagram.png"
    if not render_png(block, png_path):
        log("      PNG 渲染失败，跳过")
        (entry_dir / "diagram.mmd").unlink(missing_ok=True)
        entry_dir.rmdir()
        stats["png_fail"] += 1
        return False, collected

    # 直接生成当前格式的 description（7 节扩展描述）
    repo_tree = fetch_repo_tree(repo_full, branch)
    readme_text = fetch_readme(repo_full, branch)
    source_doc = fetch_source_doc(raw_url)
    doc_context = extract_local_doc_context(source_doc, block)

    selected_files = select_relevant_files(
        repo_full, branch, md_path, block, readme_text, repo_tree,
    )
    log(f"      [选码] files={selected_files}")
    selected_snippets = fetch_selected_file_snippets(repo_full, branch, selected_files)

    description = generate_full_description(
        repo=repo_full,
        branch=branch,
        file_path=md_path,
        repo_tree=repo_tree,
        readme_text=readme_text,
        doc_context=doc_context,
        mermaid_code=block,
        image_path=png_path,
        selected_files=selected_files,
        selected_snippets=selected_snippets,
    )
    if not description:
        log("      description 生成失败，跳过")
        stats["desc_fail"] = stats.get("desc_fail", 0) + 1
        (entry_dir / "diagram.mmd").unlink(missing_ok=True)
        (entry_dir / "diagram.png").unlink(missing_ok=True)
        entry_dir.rmdir()
        return False, collected

    (entry_dir / "description.txt").write_text(description.strip() + "\n", encoding="utf-8")

    repo_structs.add(sh)
    seen_struct_hash.add(sh)
    all_metadata.append({
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
            "description": f"dataset/{collected:03d}/description.txt",
        },
    })
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    collected += 1
    log(f"      [OK] {collected}/{target} -> {entry_dir.name}/ "
        f"(规则拒:{stats['rule_rej']} AI拒:{stats['ai_rej']} 结构重:{stats['struct_dup']})")
    return True, collected


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("=== FlowSight 数据集构建日志 ===\n", encoding="utf-8")

    meta_path = OUTPUT_DIR / "metadata.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            all_metadata = json.load(f)
        collected = len(all_metadata)
        target = collected + ADD_MORE
        log(f"[续采] 已有 {collected} 条，再采 {ADD_MORE} 条（目标 {target}）")
    else:
        all_metadata = []
        collected = 0
        target = TARGET_COUNT
        log(f"[新采] 目标 {target} 条")

    seen_hashes = {m.get("mermaid_hash", 0) for m in all_metadata}
    seen_struct_hash = {m.get("struct_hash", 0) for m in all_metadata}
    seen_repos = set(m["repo"] for m in all_metadata)
    repo_struct = {}
    for m in all_metadata:
        repo_struct.setdefault(m["repo"], set()).add(m.get("struct_hash", 0))

    stats = {"rule_rej": 0, "ai_rej": 0, "struct_dup": 0, "png_fail": 0, "desc_fail": 0}

    for query in REPO_QUERIES:
        if collected >= target:
            break
        log(f"\n[搜索] {query}")
        time.sleep(2)

        for page in range(1, 5):
            if collected >= target:
                break
            repos = search_repos(query, page=page, per_page=30)
            if not repos:
                log(f"  第{page}页无结果")
                break
            log(f"  第{page}页：{len(repos)} 个仓库")
            time.sleep(2)

            for repo_info in repos:
                if collected >= target:
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
                    log("    无含 mermaid 的文档")
                    continue
                log(f"    找到 {len(docs)} 个含 mermaid 的文件")

                readme_raw = next((c for p, c in docs if p.lower() == "readme.md"), "")
                found_in_repo = 0

                for md_path, content in docs:
                    if collected >= target:
                        break
                    raw_url = f"https://raw.githubusercontent.com/{repo_full}/{branch}/{md_path}"
                    for block in extract_mermaid_blocks(content):
                        if collected >= target:
                            break
                        ok, collected = try_save(
                            block, repo_full, stars, branch, md_path, raw_url,
                            all_metadata, meta_path, seen_hashes, seen_struct_hash, repo_struct, stats, collected, target,
                        )
                        if ok:
                            found_in_repo += 1
                            time.sleep(1.5)

                if found_in_repo:
                    log(f"    本仓库贡献 {found_in_repo} 条")
            time.sleep(3)

    (OUTPUT_DIR / "README.md").write_text(
        f"# FlowSight 架构/流程图数据集\n\n"
        f"共 **{collected}** 条，来自 GitHub 热门仓库 README/文档。\n\n"
        f"每条：`diagram.mmd`（Mermaid 源码）、`diagram.png`（渲染图）、`description.txt`（7 节结构化中文描述）。\n\n"
        f"过滤：多语言 README 过滤、规则预过滤、AI 质量判断、结构去重；每仓库最多 {MAX_PER_REPO} 张。\n\n"
        f"详见 `metadata.json`。\n",
        encoding="utf-8",
    )

    log(f"\n{'='*50}\n[完成] 共采集 {collected} 条")
    log(f"  规则拒:{stats['rule_rej']} AI拒:{stats['ai_rej']} 结构重:{stats['struct_dup']} PNG失败:{stats['png_fail']} 描述失败:{stats.get('desc_fail',0)}\n  路径：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
