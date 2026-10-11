# 格式设置工作区

本目录保存策划案撰写 Skill 与格式设置 Skill 共用的交接资料、输入样例和验证结果。两个可调用 Skill 的入口统一放在项目 `.agents/skills/` 下。

## 目录

- `策划案格式交接规范.md`：撰写 Skill 交给格式设置 Skill 的 Markdown 结构约定。
- `samples/`：样例输入及其来源、整理和覆盖范围说明。
- `outputs/`：格式设置 Skill 生成的 Word、核验报告和页面预览；其中 `教师节策划案-端到端验证/` 保存教师节样例的端到端验证结果。
- `../.agents/skills/campus-activity-planning/`：生成策划案框架、逐模块整理内容并生成 Markdown 交接稿。
- `../.agents/skills/neu-proposal-format/`：检查交接稿并生成、核验 Word 文档。

## 典型使用顺序

1. 撰写 Skill 与用户完成策划案内容，并等待用户确认全文。
2. 撰写 Skill 按交接规范生成完整 Markdown 稿件。
3. 格式设置 Skill 检查稿件结构；检查通过后生成 Word 和核验材料。
4. 人工逐页检查页面预览，再把检查结果写入核验报告。

`outputs/` 中的文件是验证产物，不是新的输入规范；格式规则以交接规范和格式设置 Skill 的 `references/` 为准。
