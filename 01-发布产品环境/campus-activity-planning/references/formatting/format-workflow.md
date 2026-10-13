# Word 格式模块流程

格式处理只用于已完成内容确认、并符合输入契约的 Markdown 策划案。用户已有完整稿件并要求排版时，也要确认其内容已经定稿。

1. 先读取 `input-contract.md`、`format-rules.md` 和 `format-profile.json`。
2. 保留输入原件，运行 `python ../../scripts/format_proposal.py check <input.md>`。
3. 输入结构、运行依赖、Microsoft Word 或规定字体检查失败时停止，报告具体错误，不生成正式 Word。
4. 检查通过后运行 `python ../../scripts/format_proposal.py build <input.md> --output-dir <directory>`。
5. 检查报告中的文字一致性和格式属性；在 Word 环境中逐页检查渲染结果。
6. 完成视觉检查后运行 `finalize-report` 更新核验状态。未完成页面检查时，不得标记为通过。

脚本依赖 Windows、Microsoft Word、Python 依赖和指定字体。若当前环境不能运行这些工具，停止 Word 生成，保留已确认 Markdown 交接稿，并说明所需本地环境。

格式模块只处理版式，不改写或补充活动内容。

