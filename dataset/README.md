# Mermaid 架构/流程图数据集

共 **500** 条数据，来自 GitHub 各类热门仓库的 README / 文档文件。

## 每条数据

| 文件 | 内容 |
|------|------|
| `diagram.mmd` | Mermaid 原始源码（graph / flowchart 类型） |
| `diagram.png` | 由 mermaid.ink 渲染的 PNG 图片 |
| `description.txt` | OpenRouter Gemini Flash 生成的中文文字描述 |

## 质量过滤

每条数据经过三道过滤：
1. 多语言 README 过滤（只保留英文 README.md）
2. 规则预过滤（节点数、标签质量、路径黑名单）
3. AI 质量判断（Gemini Flash 判定是否为真实架构/流程图）

结构去重：提取节点 ID + 拓扑，跨语言版本及同仓库内去重；每仓库上限 3 张。

## 数据来源

GitHub 各技术领域热门仓库（按 stars 降序），覆盖微服务、云原生、CI/CD、系统设计、API 等场景。

详细来源见 `metadata.json`。
