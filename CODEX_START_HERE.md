# Codex 项目开发入口

本项目包含两个可调用 Skill：策划案撰写 Skill 负责从活动需求形成框架、逐模块整理内容并生成 Markdown 交接稿；格式设置 Skill 负责检查交接稿并生成、核验 Word 文档。

## 资料位置

- `decisions/DECISIONS.md`：已确认的产品规则和仍开放的设计问题。
- `specs/`：产品边界、业务流程、交接结构、验收和实现计划。
- `knowledge/`：从真实策划案提炼的章节逻辑、内容颗粒度、活动经验和注意事项。
- `references/`：原始策划案、公文格式要求等项目来源材料。
- `.agents/skills/campus-activity-planning/`：策划案撰写 Skill。
- `.agents/skills/neu-proposal-format/`：格式设置 Skill。
- `formatting-skill-workspace/`：两个 Skill 共用的交接规范、样例和验证产物。

## 修改与验证

修改策划案业务行为时，先核对 `decisions/`、相关 `specs/` 和 `knowledge/`，再更新撰写 Skill 并使用 `examples/`、`tests/` 中适用的场景检查。

修改 Word 生成行为时，先核对 `formatting-skill-workspace/策划案格式交接规范.md` 和格式 Skill 的 `references/`，再运行该 Skill 的测试。涉及页面显示时，还要检查 Word 渲染出的每一页预览。

`README.md` 是本项目的快速导览；项目规格与 Skill 实际指令不一致时，先记录具体冲突，再依据已确认的业务规则处理。
