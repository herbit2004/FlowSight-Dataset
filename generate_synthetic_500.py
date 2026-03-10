#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 500 条合成数据：200 条有意义 (meaningful_000–199)，300 条无意义 (nonsense_000–299)。
- 有意义/无意义分别从 0 编号，加大类前缀。
- 无意义仅两种子类型各 150 条：chaos 完全混乱(0–149)、misleading 误导(150–299)。
- 单线程顺序生成：先 meaningful 0–199，再 nonsense 0–149(chaos)，再 nonsense 150–299(misleading)。
- 复杂度（mermaid 行数）从真实 metadata 的 mermaid_lines 分布抽样。
- 生成/网络/渲染错误均带重试；通过 mmd hash 去重。
"""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import random
import re
import time
from pathlib import Path
from threading import Lock

import requests

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_ROOT / "dataset"
REAL_METADATA = DATASET_DIR / "metadata.json"
SYNTHETIC_METADATA = DATASET_DIR / "synthetic_metadata.json"
LOG_FILE = DATASET_DIR / "generate_synthetic.log"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MERMAID_INK = "https://mermaid.ink/img/{encoded}?type=png"

# 3 组：(prefix, start, end, subtype or None)
GROUPS = [
    ("meaningful", 0, 200, None),
    ("nonsense", 0, 150, "chaos"),
    ("nonsense", 150, 300, "misleading"),
]

MAX_RETRIES = 3
RETRY_SLEEP = 4
MODEL = "google/gemini-2.0-flash-001"

# 有意义图主题/领域列表，按 local_idx 取模使用，避免同一 prompt 重复导致数据雷同
MEANINGFUL_THEMES = [
    "用户注册与登录流程", "订单创建与支付", "商品搜索与推荐", "库存扣减与回滚",
    "消息队列生产与消费", "缓存读写与失效", "API 网关路由与鉴权", "微服务间 RPC 调用",
    "日志采集与聚合", "指标上报与告警", "配置中心下发", "分布式锁与选主",
    "文件上传与存储", "数据同步与 ETL", "审批工作流", "权限与角色校验",
    "会话与单点登录", "支付回调与对账", "风控规则引擎", "推荐排序 pipeline",
    "搜索索引更新", "定时任务调度", "重试与熔断", "灰度发布与流量切换",
    "数据库读写分离", "分库分表路由", "事务与补偿", "事件溯源",
    "设备上报与指令下发", "实时计算与窗口", "批处理任务 DAG", "数据湖分层",
    "客服工单流转", "营销活动规则", "优惠券发放与核销", "积分与等级",
    "推送通知策略", "埋点与行为分析", "AB 实验分流", "特征工程 pipeline",
    "模型训练与部署", "推理服务调用链", "知识图谱构建", "全文检索与高亮",
    "多租户隔离", "配额与限流", "审计日志", "数据脱敏与加密",
    "容器编排与扩缩容", "服务发现与健康检查", "网关限流与熔断", "链路追踪",
    "报表生成与导出", "大屏实时数据", "工单 SLA 与升级", "资源申请与审批",
    "镜像构建与发布", "配置变更与回滚", "密钥轮换", "备份与恢复",
    "跨区域同步", "多活与故障切换", "冷热数据分层", "归档与清理策略",
    "设备心跳与离线检测", "固件升级流程", "规则匹配与动作执行", "工作流状态机",
    "表单校验与提交", "多步向导与草稿", "评论与点赞", "关注与消息流",
    "直播推拉流", "转码与截图", "CDN 回源", "水印与鉴权",
    "发票申请与开具", "合同签署流程", "对账与结算", "账单生成",
    "客服机器人对话", "工单自动分配", "知识库检索", "质检与抽检",
    "仓储入库与出库", "物流轨迹与签收", "退换货流程", "售后补偿",
    "会员等级与权益", "签到与任务", "邀请与裂变", "积分兑换",
    "安全扫描与漏洞修复", "依赖分析与许可", "代码评审与合并", "环境与发布门禁",
]

_lock = Lock()
_seen_hashes: set[int] = set()
_meta_list: list[dict] = []
_target_lines: list[int] = []  # 500 个目标行数，按 global index 分配
_meta_file_lock = Lock()


def _append_synthetic_meta(meta: dict) -> None:
    """追加一条到 synthetic_metadata.json（增量写入，进程中断时可保留已生成记录）。"""
    SYNTHETIC_METADATA.parent.mkdir(parents=True, exist_ok=True)
    existing: list = []
    if SYNTHETIC_METADATA.exists():
        try:
            existing = json.loads(SYNTHETIC_METADATA.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append(meta)
    with _meta_file_lock:
        SYNTHETIC_METADATA.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_api_key() -> str:
    """优先从 build_dataset.py 读取 OPENROUTER_API_KEY，其次用环境变量。"""
    try:
        with open(PROJECT_ROOT / "build_dataset.py", encoding="utf-8") as f:
            m = re.search(r'OPENROUTER_API_KEY\s*=\s*["\']([^"\']+)["\']', f.read())
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


API_KEY = _get_api_key()


def log(msg: str) -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] {msg}\n"
    try:
        print(msg, flush=True)
    except Exception:
        pass
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def load_real_mermaid_lines() -> list[int]:
    """从真实 metadata 读取 mermaid_lines，用于抽样目标复杂度。"""
    if not REAL_METADATA.exists():
        return [15, 20, 25, 30, 22, 18, 35, 10, 40, 50] * 50  # fallback
    with open(REAL_METADATA, encoding="utf-8") as f:
        data = json.load(f)
    lines = [int(item.get("mermaid_lines", 20)) for item in data if isinstance(item.get("mermaid_lines"), (int, float))]
    return lines if lines else [20] * 100


def build_target_lines() -> None:
    """用真实分布抽样 500 个目标行数，顺序与 global index 一致（0-199 meaningful, 200-499 nonsense）。"""
    global _target_lines
    real = load_real_mermaid_lines()
    _target_lines = random.choices(real, k=500)


def hash_mmd(text: str) -> int:
    h = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def _chat(messages: list, max_tokens: int = 2400, temperature: float = 0.7) -> str | None:
    if not API_KEY:
        return None
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                content = r.json().get("choices", [{}])[0].get("message", {}).get("content")
                if isinstance(content, str):
                    return content.strip()
                return None
            log(f"    [OpenRouter {r.status_code}] attempt {attempt + 1}")
            time.sleep(RETRY_SLEEP)
        except Exception as e:
            log(f"    [OpenRouter 异常] {e}")
            time.sleep(RETRY_SLEEP)
    return None


def render_png(mermaid_code: str, out_path: Path) -> bool:
    encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
    url = MERMAID_INK.format(encoded=encoded)
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=45)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("image" in ct or len(r.content) > 500):
                out_path.write_bytes(r.content)
                return True
            log(f"    [mermaid.ink {r.status_code}] attempt {attempt + 1}")
            time.sleep(RETRY_SLEEP)
        except Exception as e:
            log(f"    [mermaid.ink 异常] {e}")
            time.sleep(RETRY_SLEEP)
    return False


def extract_mermaid_block(text: str) -> str | None:
    text = text.strip()
    for pattern in [r"```mermaid\s*\n([\s\S]*?)\n\s*```", r"```\s*\n([\s\S]*?)\n\s*```"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    if text.startswith("graph ") or text.startswith("flowchart "):
        return text
    return None


def extract_introduced_errors(raw_response: str) -> list[str]:
    """从误导类生成的完整回复中解析「引入的反事实错误」列表，用于写入 metadata。"""
    if not raw_response or not raw_response.strip():
        return []
    # 先去掉 mermaid 代码块，避免把代码里的内容当错误
    rest = re.sub(r"```mermaid\s*\n[\s\S]*?\n\s*```", "", raw_response, flags=re.IGNORECASE)
    rest = re.sub(r"```\s*\n[\s\S]*?\n\s*```", "", rest)
    errors: list[str] = []
    # 查找「引入的反事实错误」段落（多种标题形式）
    for marker in [
        r"##\s*引入的反事实错误\s*\n",
        r"引入的反事实错误[：:]\s*\n",
        r"【引入的反事实错误】\s*\n",
        r"引入的反事实错误\s*\n",
    ]:
        m = re.search(marker, rest)
        if m:
            segment = rest[m.end() :].strip()
            # 取到下一个 ## 或结尾
            next_sec = re.search(r"\n\s*##\s+", segment)
            if next_sec:
                segment = segment[: next_sec.start()].strip()
            for line in segment.splitlines():
                line = line.strip()
                # 支持 - / * / 数字. 开头的列表项
                for prefix in (r"^[-*]\s+", r"^\d+[.)]\s+"):
                    if re.match(prefix, line):
                        line = re.sub(prefix, "", line).strip()
                        break
                if line and len(line) > 2:
                    errors.append(line)
            break
    return errors


def generate_mmd_meaningful(target_lines: int, worker_id: str, local_idx: int) -> str | None:
    n = max(6, min(120, target_lines))
    theme = MEANINGFUL_THEMES[local_idx % len(MEANINGFUL_THEMES)]
    prompt = f"""你生成一张 Mermaid 流程图或架构图（graph TD 或 flowchart TD/LR），要求：
1. 完全虚构，不抄袭任何真实项目；使用合理的技术/业务术语，像真实文档里的图。
2. **本图主题/领域为：{theme}**。请在该领域内自选具体场景（例如具体模块名、步骤名），避免与常见示例雷同。
3. 图约 {n} 行（含节点、边、可选 classDef），结构清晰，可有分支、汇聚、多步。
4. 只输出一个 Mermaid 代码块，不要其他解释。语法必须正确，能被 mermaid.ink 渲染。
5. 节点用英文或中文均可，风格统一。"""
    out = _chat([{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.8)
    if not out:
        return None
    return extract_mermaid_block(out)


def generate_mmd_nonsense(subtype: str, target_lines: int, worker_id: str, local_idx: int) -> tuple[str | None, list[str]]:
    """无意义仅两种：chaos 完全混乱，misleading 误导。返回 (mermaid 或 None, 引入的反事实错误列表，仅 misleading 时非空)。"""
    n = max(6, min(80, target_lines))
    diversity_hint = f"本图为该批次中第 {local_idx + 1} 张（共 150 张），请换一种方式（不要与常见示例雷同），确保多样性。"
    if subtype == "chaos":
        prompt = f"""你生成一张「完全混乱」的 Mermaid 图，要求：

**定义**：像“意大利面拌四十二号混凝土”——内容完全混乱、无真实对应，读者无法用常识或任何领域知识理解。图中可以出现随机节点 ID、自造词、荒谬组合、毫不相干的概念硬拼在一起，或整图毫无逻辑的连线和分支。不需要自洽，可以故意荒谬、无意义。

**禁止**：不要生成看起来像正常架构/流程图/业务逻辑的图。不要使用“用户请求→数据库→响应”这种合理流程。要的是“看不懂、没法用常识对应”的图。

**要求**：图约 {n} 行，Mermaid 语法正确可被 mermaid.ink 渲染。只输出一个 Mermaid 代码块，无其他文字。使用 graph TD 或 flowchart TD。
{diversity_hint}"""
        out = _chat([{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.8)
        if not out:
            return None, []
        return extract_mermaid_block(out), []

    # misleading：真实框架下尽可能多的反事实错误，并输出错误列表
    prompt = f"""你生成一张「误导」的 Mermaid 流程图/架构图，要求如下。

**定义**：图必须使用**真实、有意义的**概念（如：用户请求、登录、数据库、API、缓存、支付、网关、消息队列等），整体看起来像一张正常的业务/技术流程图，但其中**故意植入尽可能多的反事实错误**，使按常识推断会答错，只有严格按图中内容作答才对。

**必须做到**：
1. **尽可能多的反事实错误**：至少 4–6 处（建议 5 处以上），可包括但不限于：
   - 顺序颠倒（本应先 A 后 B，图中写成先 B 后 A）
   - 因果/依赖颠倒（例如：数据库写入 → 用户请求，而非用户请求 → 数据库）
   - 某条边的方向反了（A --> B 写成 B --> A）
   - 分支条件对调（Yes/No 标反，或条件写反）
   - 某节点标签错一字/多字（如「登录」写成「登出」、「读缓存」写成「写缓存」）
   - 荒谬闭环（如 用户请求 → 数据库 → 用户请求）
   - 本应汇聚的两条分支未汇聚，或本应分开的路径被错误合并
2. 图约 {n} 行，Mermaid 语法正确，能被 mermaid.ink 渲染。使用 graph TD 或 flowchart TD。
3. **在 Mermaid 代码块之后**，必须输出以下内容（用于记录）：
   先写一行标题：## 引入的反事实错误
   然后逐条列出你故意加入的每一处错误，每行一条，格式为：- 错误描述（一句话说明这处错在哪里，例如「边方向反了：应为 认证 → 鉴权，图中为 鉴权 → 认证」）。

**输出格式**：先输出一个 Mermaid 代码块，再输出「## 引入的反事实错误」及其列表。不要省略错误列表。
{diversity_hint}"""
    out = _chat([{"role": "user", "content": prompt}], max_tokens=2600, temperature=0.8)
    if not out:
        return None, []
    mmd = extract_mermaid_block(out)
    errors = extract_introduced_errors(out)
    return mmd, errors


def generate_description(mmd: str, png_path: Path, is_nonsense: bool, subtype: str | None) -> str | None:
    format_spec = """
输出格式必须严格固定为下面 7 个一级标题（标题名不能改、顺序不能变），风格与现有 FlowSight 数据集 description 一致：

## 图类型与用途
用 2-4 句说明图属于什么类型、描述什么流程或架构。

## 图的整体布局
用 1-3 句说明方向（如从上到下）、总体层次、起点与终点。

## 分组/子图/阶段说明
若有 subgraph/阶段则说明；若无则写“图中没有显式子图，但逻辑上可分为……阶段”。

## 节点逐项说明
逐项列出图中关键节点，每行格式为：- **节点ID或节点标签**：该节点在图中的含义说明。（与现有数据集一致，用短横线列表、节点名加粗）

## 连线、分支与汇聚关系
按“源 -> 目标”分条写，有条件则写 `A -- Yes --> B`：说明。

## 仓库语境与术语解释
本图为合成数据，无真实仓库。列出图中出现的 3-8 个术语并解释，每行格式为：- **术语**：解释。

## 可作为 QA Ground Truth 的高信息密度摘要
一段高信息密度摘要，覆盖起点、关键分支、核心节点、终点，便于作为 QA 的 ground truth。
"""
    extra = ""
    if is_nonsense:
        extra = "\n重要：本题为无意义/反常识图，描述时仅陈述图中可见内容，答案须严格以图为准，勿依赖常识推断。"
    prompt = f"""根据下面 Mermaid 源码和渲染图，生成结构化描述（中文），与现有 FlowSight 数据集的 description.txt 格式与风格一致。{extra}

格式规范：
{format_spec}

Mermaid 源码：
```mermaid
{mmd[:6000]}
```
请严格按 7 个一级标题输出，不要省略；节点与连线的列表格式需与现有数据集一致。"""
    mime = mimetypes.guess_type(png_path.name)[0] or "image/png"
    data_url = f"data:{mime};base64,{base64.b64encode(png_path.read_bytes()).decode('utf-8')}"
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }]
    return _chat(messages, max_tokens=2200, temperature=0.2)


def try_generate_one(prefix: str, local_idx: int, subtype: str | None, target_line: int, worker_label: str) -> bool:
    sample_id = f"{prefix}_{local_idx:03d}"
    global_index = local_idx if prefix == "meaningful" else 200 + local_idx
    out_dir = DATASET_DIR / sample_id
    out_dir.mkdir(parents=True, exist_ok=True)
    mmd_path = out_dir / "diagram.mmd"
    png_path = out_dir / "diagram.png"
    desc_path = out_dir / "description.txt"

    for gen_attempt in range(5):
        if prefix == "meaningful":
            mmd = generate_mmd_meaningful(target_line, worker_label, local_idx)
            introduced_errors: list[str] = []
        else:
            mmd, introduced_errors = generate_mmd_nonsense(subtype or "chaos", target_line, worker_label, local_idx)
        if not mmd or len(mmd) < 30:
            log(f"  [{worker_label}] {sample_id} mmd 生成空/过短 attempt {gen_attempt + 1}")
            time.sleep(RETRY_SLEEP)
            continue
        h = hash_mmd(mmd)
        with _lock:
            if h in _seen_hashes:
                log(f"  [{worker_label}] {sample_id} 重复 mmd hash，重试")
                time.sleep(1)
                continue
        if not render_png(mmd, png_path):
            log(f"  [{worker_label}] {sample_id} PNG 渲染失败")
            time.sleep(RETRY_SLEEP)
            continue
        desc = generate_description(mmd, png_path, prefix == "nonsense", subtype)
        if not desc or "## 图类型与用途" not in desc:
            log(f"  [{worker_label}] {sample_id} description 生成失败")
            png_path.unlink(missing_ok=True)
            time.sleep(RETRY_SLEEP)
            continue
        with _lock:
            _seen_hashes.add(h)
        mmd_path.write_text(mmd, encoding="utf-8")
        desc_path.write_text(desc, encoding="utf-8")
        mermaid_lines = len(mmd.splitlines())
        meta = {
            "id": sample_id,
            "source": "synthetic_realistic" if prefix == "meaningful" else "synthetic_nonsense",
            "mermaid_lines": mermaid_lines,
            "files": {
                "mermaid": f"dataset/{sample_id}/diagram.mmd",
                "png": f"dataset/{sample_id}/diagram.png",
                "description": f"dataset/{sample_id}/description.txt",
            },
        }
        if subtype:
            meta["nonsense_subtype"] = subtype
        if subtype == "misleading" and introduced_errors:
            meta["introduced_errors"] = introduced_errors
        with _lock:
            _meta_list.append(meta)
        # 增量写入 metadata，避免进程中断时丢失已生成记录
        with _lock:
            _append_synthetic_meta(meta)
        err_info = f", introduced_errors={len(introduced_errors)}" if (subtype == "misleading" and introduced_errors) else ""
        log(f"  [{worker_label}] {sample_id} OK (lines={mermaid_lines}{err_info})")
        return True
    log(f"  [{worker_label}] {sample_id} 失败，已跳过")
    if out_dir.exists():
        for f in [mmd_path, png_path, desc_path]:
            if f.exists():
                f.unlink(missing_ok=True)
        try:
            out_dir.rmdir()
        except Exception:
            pass
    return False


def clean_synthetic_data() -> None:
    """删除已生成的合成数据目录与 metadata/log，便于重跑。"""
    import shutil
    deleted_dirs = 0
    for d in DATASET_DIR.iterdir():
        if not d.is_dir():
            continue
        name = d.name
        if name.startswith("meaningful_") or name.startswith("nonsense_"):
            try:
                shutil.rmtree(d)
                deleted_dirs += 1
                log("删除目录: %s" % d.name)
            except Exception as e:
                log("删除失败 %s: %s" % (d.name, e))
    for f in [SYNTHETIC_METADATA, LOG_FILE]:
        if f.exists():
            try:
                f.unlink()
                log("删除文件: %s" % f.name)
            except Exception as e:
                log("删除失败 %s: %s" % (f.name, e))
    log("清理完成，已删除 %d 个合成数据目录。可重新运行: python generate_synthetic_500.py" % deleted_dirs)


def run_all_sequential() -> tuple[int, int]:
    """按顺序生成 500 条：meaningful 0-199，nonsense 0-149(chaos)，nonsense 150-299(misleading)。"""
    total_ok = total_fail = 0
    # 顺序：(meaningful, 0..199), (nonsense chaos, 0..149), (nonsense misleading, 150..299)
    tasks: list[tuple[str, int, str | None]] = []
    for i in range(200):
        tasks.append(("meaningful", i, None))
    for i in range(150):
        tasks.append(("nonsense", i, "chaos"))
    for i in range(150, 300):
        tasks.append(("nonsense", i, "misleading"))
    for idx, (prefix, local_idx, subtype) in enumerate(tasks):
        global_idx = local_idx if prefix == "meaningful" else 200 + local_idx
        target_line = _target_lines[global_idx] if global_idx < len(_target_lines) else 25
        label = f"({idx+1}/500)"
        if try_generate_one(prefix, local_idx, subtype, target_line, label):
            total_ok += 1
        else:
            total_fail += 1
        time.sleep(0.5)
    return total_ok, total_fail


def _canonical_order_key(item: dict) -> tuple[int, int]:
    """排序 key：meaningful 在前、nonsense 在后，同类型按编号升序。"""
    sid = item.get("id", "")
    if sid.startswith("meaningful_"):
        return (0, int(sid.replace("meaningful_", "")))
    if sid.startswith("nonsense_"):
        return (1, int(sid.replace("nonsense_", "")))
    return (2, 0)


def run_retry_missing() -> None:
    """根据 synthetic_metadata.json 找出缺失的 500 条中的 id，只对缺失项重试生成并补全。"""
    expected_ids: set[str] = set()
    for i in range(200):
        expected_ids.add(f"meaningful_{i:03d}")
    for i in range(300):
        expected_ids.add(f"nonsense_{i:03d}")
    existing_ids: set[str] = set()
    existing_meta: list[dict] = []
    if SYNTHETIC_METADATA.exists():
        try:
            existing_meta = json.loads(SYNTHETIC_METADATA.read_text(encoding="utf-8"))
            existing_ids = {m.get("id", "") for m in existing_meta if m.get("id")}
        except Exception as e:
            log("读取 synthetic_metadata.json 失败: %s" % e)
            return
    missing = sorted(expected_ids - existing_ids)
    if not missing:
        log("无缺失，500 条已完整，无需补全。")
        return
    log("补全 %d 条缺失: %s" % (len(missing), missing))
    if not API_KEY:
        log("错误: 未设置 OPENROUTER_API_KEY，退出。")
        return
    seed = os.environ.get("SEED")
    random.seed(int(seed) if seed is not None else int(time.time()))
    build_target_lines()
    ok = fail = 0
    for sample_id in missing:
        if sample_id.startswith("meaningful_"):
            prefix = "meaningful"
            local_idx = int(sample_id.replace("meaningful_", ""))
            subtype = None
        else:
            prefix = "nonsense"
            local_idx = int(sample_id.replace("nonsense_", ""))
            subtype = "chaos" if local_idx < 150 else "misleading"
        global_idx = local_idx if prefix == "meaningful" else 200 + local_idx
        target_line = _target_lines[global_idx] if global_idx < len(_target_lines) else 25
        if try_generate_one(prefix, local_idx, subtype, target_line, "retry"):
            ok += 1
        else:
            fail += 1
        time.sleep(0.5)
    # 合并现有 metadata 与本次新生成的条目，按规范顺序写回
    with _lock:
        new_meta = list(_meta_list)
    all_meta = [m for m in existing_meta] + new_meta
    all_meta.sort(key=_canonical_order_key)
    SYNTHETIC_METADATA.parent.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_METADATA.write_text(json.dumps(all_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log("补全完成: 成功 %d 条, 失败 %d 条, metadata 已按顺序写回。" % (ok, fail))


def main() -> None:
    import sys
    if "--clean" in (sys.argv[1:] or []):
        clean_synthetic_data()
        return
    if "--retry-missing" in (sys.argv[1:] or []):
        run_retry_missing()
        return
    # 立即打日志，确认脚本进入生成流程（并确认 log 文件写的是当前运行）
    log("======== 开始生成 500 条合成数据 ========")
    seed = os.environ.get("SEED")
    random.seed(int(seed) if seed is not None else int(time.time()))
    build_target_lines()
    log("生成 500 条合成数据（单线程顺序）")
    log("目标行数分布: min=%s max=%s 前20个=%s" % (
        min(_target_lines), max(_target_lines), _target_lines[:20],
    ))
    if not API_KEY:
        log("错误: 未设置 OPENROUTER_API_KEY，退出。请设置环境变量或在 build_dataset.py 中配置。")
        return
    log("API Key 已配置，开始顺序生成...")
    total_ok, total_fail = run_all_sequential()
    with _lock:
        meta_copy = list(_meta_list)
    SYNTHETIC_METADATA.parent.mkdir(parents=True, exist_ok=True)
    # 最终覆盖写入，保证顺序与 _meta_list 一致（增量写入可能乱序）
    SYNTHETIC_METADATA.write_text(json.dumps(meta_copy, ensure_ascii=False, indent=2), encoding="utf-8")
    log("全部完成: ok=%d fail=%d metadata 已写入 %s" % (total_ok, total_fail, SYNTHETIC_METADATA))


if __name__ == "__main__":
    main()
