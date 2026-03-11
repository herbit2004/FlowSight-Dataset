# Pilot 配置：仅使用前 N 条数据，输出到 pilot/，不修改 dataset/
from pathlib import Path

PILOT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PILOT_ROOT.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
PILOT_DIR = PILOT_ROOT / "pilot_data"  # 所有 pilot 输出集中在此，与 dataset 完全隔离
PILOT_SIZE = 10

# 风格：mermaid.ink 的 theme 参数，配色/观感差异明显
STYLES = [
    ("default", {}),   # 默认暖色
    ("dark", {"bgColor": "1b1b1f"}),  # 深色背景
    ("forest", {}),    # 绿色系
    ("neutral", {}),   # 黑白中性，适合印刷
]

# OpenRouter 多模态模型（均支持 image 输入）
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = None  # 由 run_pilot 从项目根目录 .env 环境配置读取

VISION_MODELS = [
    "google/gemini-2.0-flash-001",
    "openai/gpt-4o-mini",
    "anthropic/claude-3-5-haiku-20241022",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
]

# 每样本生成的选择题数量（便于拉开差异：含事实+推理）
QA_PER_SAMPLE = 4
