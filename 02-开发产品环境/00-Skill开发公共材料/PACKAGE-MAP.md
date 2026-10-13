# 发布包文件映射

统一发布包：`01-发布产品环境/campus-activity-planning/`。构建脚本位于 `scripts/build_release.ps1`，以开发目录为维护源整理运行资料。

| 发布包文件 | 开发维护源 | 用途 |
|---|---|---|
| `SKILL.md` | `01-Skill1-策划案撰写/SKILL.md` | 统一入口及阶段路由 |
| `references/workflow.md` | Skill 1 的 `references/workflow.md` | 框架、逐模块填写、全文确认和交接流程 |
| `references/knowledge/*.md` | `00-Skill开发公共材料/knowledge/*.md` | 历史案例提炼知识 |
| `references/templates/*.md` | `00-Skill开发公共材料/templates/*.md` | 任务信息与框架展示参考 |
| `references/handoff/*.md` | `00-Skill开发公共材料/交接规范/*.md` | Markdown 交接契约 |
| `references/formatting/*` | Skill 2 的 `references/*` | 输入契约、格式规则和配置 |
| `references/formatting/format-workflow.md` | Skill 2 的 `references/format-workflow.md` | Word 阶段流程及运行限制 |
| `scripts/*` | Skill 2 的 `scripts/*` | 本地 Word 生成和核验程序 |

历史原件、Word 样例和验证输出不复制到发布包。发布前检查：运行 `scripts/build_release.ps1`，再检查文件映射完整、包内 Markdown 链接有效、Skill 可读、脚本依赖说明齐全、发布包不含原始案例文件。
