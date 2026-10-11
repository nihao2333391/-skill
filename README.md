# 高校活动策划与文档格式工作区

**状态**：策划案撰写 Skill 与格式设置 Skill 均已形成初版，项目知识、规格和样例继续作为迭代依据。
**推荐使用方式**：在 Codex 中按需调用对应 Skill；修改业务规则前先核对本项目的决定记录与知识资料。
**业务中心**：先生成有业务针对性的一级、二级标题框架，再逐模块协作完成策划案；用户确认全文后，交给格式设置 Skill 生成可编辑 Word。

## 五分钟上手

1. 需要策划案框架和内容协作时，调用 `$campus-activity-planning`；需要将已定稿的交接稿排成 Word 时，调用 `$neu-proposal-format`。
2. 先阅读 `specs/02-case-to-knowledge.md` 及其链接的 `knowledge/` 知识归档；`references/` 收录策划案、通知、手册和格式样例，来源与用途见 `knowledge/sources.md`。
3. 写作 Skill 根据活动信息和历史案例生成与任务相称的一级、二级标题，并为必要部分提供简短内容方向。
4. 用户确认框架后，按一级标题逐模块询问和确认；一次口述牵涉多个模块时，同一回复先确认当前主模块，再按顺序确认受影响模块，但这些模块之后仍须接受专门询问。
5. 全部模块完成专门询问和确认后，在对话框展示便于阅读的完整稿件；等待用户确认全文后，再按 `formatting-skill-workspace/策划案格式交接规范.md` 生成 Markdown 交接稿。
6. 两阶段之间的结构信息如何在技术上承载，暂列设计议题；不可让用户为此编辑 JSON。

## 文件导览

| 路径 | 用途 |
|---|---|
| `CODEX_START_HERE.md` | 给 Codex 的第一轮任务与明确停止点 |
| `decisions/DECISIONS.md` | 已决定事项、开放事项和非目标 |
| `specs/01-product-and-boundaries.md` | 业务目标、使用场景、需求编号 |
| `specs/02-case-to-knowledge.md` | 参考 PDF 的证据提炼与迁移界限 |
| `specs/03-business-flow.md` | 从输入到提纲、写作、定稿的对话流程 |
| `specs/04-outline-contract.md` | 框架交付的表现形式与验收口径 |
| `specs/05-document-and-layout.md` | 写作到排版的语义契约与明确格式规则 |
| `specs/06-acceptance.md` | 可追踪验收与失败用例 |
| `specs/07-implementation-plan.md` | SDD 里程碑、开发次序及交付门槛 |
| `knowledge/` | 面向未来 Skill 的框架设计研究、内容颗粒度、活动经验、注意事项与来源索引 |
| `templates/` | 信息采集与框架展示格式示例 |
| `examples/` | 不同任务条件下的示例输入和期望方向 |
| `tests/` | 分阶段人工/自动化测试场景 |
| `references/` | 用户提供的原始 PDF 与 DOCX 材料 |
| `.agents/skills/campus-activity-planning/` | 策划案框架设计、逐模块内容协作和 Markdown 交接 |
| `.agents/skills/neu-proposal-format/` | 按交接规范生成并核验 Word 文档 |
| `formatting-skill-workspace/` | 两个 Skill 共用的格式交接规范、样例和生成验证结果 |


## 业务处理顺序

预先学习已有案例，提炼常见章节、业务要素、内容颗粒度及不同活动的特殊要求，再进入本次活动的处理流程。

**输入本次活动信息 → 结合历年范式识别涉及的业务方面 → 提供有针对性的标题框架与填充提示 → 用户确认并逐模块补全 → 对话框展示完整稿并等待用户确认 → 按共同约定生成 Markdown 交接稿 → 格式 Skill 处理文档排版。**

底层可以使用轻量结构或临时数据对象，但界面始终优先展示自然文章。`YAML/Markdown/JSON/内存对象` 尚未定型，详见 `decisions/DECISIONS.md`。

2026-10-08 已将知识学习内容归档到 [来源索引](knowledge/sources.md)、[内容颗粒度](knowledge/content-granularity.md)、[活动经验](knowledge/activity-experience.md)和[注意事项](knowledge/cautions.md)。归档供后续 Skill 开发按需读取，状态为知识准备。

## 来源边界与共享提醒

- 当前有多个策划案和一份公文格式示例。招新策划案提供观察到的写法，不能单独证明全校所有活动必须有同样的九个章节。
- PDF 原件第四页包含真实人员的姓名和联系方式。此 ZIP 适合提供给授权的项目开发者；转发公开资料前应对原始附件进行隐私审查。
- 既定格式的具体项目仍要与实际学生会审核要求对齐。
