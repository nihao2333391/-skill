---
name: neu-proposal-format
description: 将遵守约定结构的东北大学纯文字策划案 Markdown 生成并核验为规范的可编辑 Word 文档。用于内容已经定稿且需要应用公文格式的策划案；不处理任意旧稿、表格、图片或附件正文。
---

# 东北大学策划案格式设置

将已经定稿且符合输入契约的 Markdown 策划案转换为可编辑 DOCX。保持原文、编号、标点、段落和顺序，不参与内容撰写。

## 受理边界

- 只接收策划案撰写 Skill 交出的完整 Markdown 文件，或在代码块中完整保留的同格式文本。
- 只处理主标题、一级标题、二级标题、三级内容段落、普通正文和落款。
- 不处理任意旧稿、表格、图片、附件正文、段内标签和未知结构标记。
- 不修改原稿，不推断缺失层级，不自动修正文稿。

开始处理前，必须读取 [输入契约](references/input-contract.md) 和项目的[策划案格式交接规范](../../../formatting-skill-workspace/策划案格式交接规范.md)。更新、检查或解释格式规则时，再读取 [格式规则](references/format-rules.md)。程序使用 [格式配置](references/format-profile.json)。

## 固定流程

1. 保留原始 Markdown，不覆盖输入文件。
2. 运行 `scripts/format_proposal.py check <input.md>`。
3. 输入、规定字体、Microsoft Word 或运行依赖任一检查失败时停止，向用户报告具体错误；不要生成正式 DOCX。
4. 检查通过后，运行 `scripts/format_proposal.py build <input.md> --output-dir <directory>`。
   - `build` 会启动隐藏的 Microsoft Word COM 进程。若执行环境以 `0x80070005 (E_ACCESSDENIED)` 拒绝 COM，只对同一条 `build` 命令申请沙箱外执行权限；不要改用其他渲染器。
5. 检查生成报告中的内容与格式属性结果。任一机器检查失败时停止，不交付生成物。
6. 打开 `qa/<输入名>/` 中由 Microsoft Word 导出的全部页面 PNG，逐页检查乱码、缺字、异常换行、重叠和错误分页。
7. 视觉检查通过后，运行 `scripts/format_proposal.py finalize-report <report.md> --visual-status pass --pages <实际检查页数>`；失败时将状态写为 `fail` 并说明原因。
8. 只有报告最终状态为“通过”时，才交付 DOCX 和 Markdown 核验报告。`qa/` 是内部证据，用户未要求时不交付。

## 失败处理

- 输入错误报告必须包含行号、错误类型和修正建议。
- 缺少方正小标宋_GBK、方正黑体_GBK、方正楷体_GBK或方正仿宋_GBK时停止；不要安装字体，不要替换字体。
- 无法调用 Microsoft Word 完成渲染时停止，并将结果标记为未完成视觉验收。
- 不要把测试模式生成的文档当作正式成品。

## 输出

成功运行产生：

- `<输入名>.formatted.docx`
- `<输入名>.format-report.md`

报告必须记录输入摘要、环境、对象数量、内容一致性、格式属性、Word 渲染页数和逐页视觉检查结论。
