$ErrorActionPreference = 'Stop'

$commonRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$developmentRoot = [IO.Path]::GetFullPath((Join-Path $commonRoot '..'))
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $developmentRoot '..'))
$skill1 = Join-Path $developmentRoot '01-Skill1-策划案撰写'
$skill2 = Join-Path $developmentRoot '02-Skill2-格式排版'
$release = Join-Path $repositoryRoot '01-发布产品环境\campus-activity-planning'
$references = Join-Path $release 'references'

foreach ($path in @(
    $repositoryRoot,
    $commonRoot,
    $skill1,
    $skill2,
    $release
)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "缺少构建所需路径：$path"
    }
}

foreach ($relative in @('knowledge', 'templates', 'formatting', 'handoff', 'agents', 'scripts')) {
    New-Item -ItemType Directory -Path (Join-Path $references $relative) -Force | Out-Null
}

Copy-Item -LiteralPath (Join-Path $skill1 'SKILL.md') -Destination (Join-Path $release 'SKILL.md') -Force
Copy-Item -LiteralPath (Join-Path $skill1 'agents\openai.yaml') -Destination (Join-Path $release 'agents\openai.yaml') -Force
Copy-Item -LiteralPath (Join-Path $skill1 'references\workflow.md') -Destination (Join-Path $references 'workflow.md') -Force
$workflowTarget = Join-Path $references 'workflow.md'
$workflowContent = Get-Content -LiteralPath $workflowTarget -Raw -Encoding UTF8
$workflowContent = $workflowContent.Replace('../../00-Skill开发公共材料/交接规范/策划案格式交接规范.md', 'handoff/策划案格式交接规范.md')
Set-Content -LiteralPath $workflowTarget -Value $workflowContent -Encoding UTF8

$knowledgeSource = Join-Path $commonRoot 'knowledge'
$knowledgeDestination = Join-Path $references 'knowledge'
foreach ($file in Get-ChildItem -LiteralPath $knowledgeSource -File) {
    $target = Join-Path $knowledgeDestination $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    $content = Get-Content -LiteralPath $target -Raw -Encoding UTF8
    if ($file.Name -eq 'sources.md') {
        $content = [regex]::Replace($content, '\[([^\]]+)\]\(\.\./原始案例材料/[^)]+\)', '$1')
    } else {
        $content = [regex]::Replace($content, '\[([^\]]+)\]\(\.\./原始案例材料/[^)]+\)', '[$1](sources.md)')
        $content = [regex]::Replace($content, '\[([^\]]+)\]\(\.\./(?:specs|examples|decisions)/[^)]+\)', '$1')
        $content = $content.Replace('交接规范/策划案格式交接规范.md', '../handoff/策划案格式交接规范.md')
    }
    Set-Content -LiteralPath $target -Value $content -Encoding UTF8
}

foreach ($file in Get-ChildItem -LiteralPath (Join-Path $commonRoot 'templates') -File) {
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $references 'templates') -Force
}
Copy-Item -LiteralPath (Join-Path $commonRoot '交接规范\策划案格式交接规范.md') -Destination (Join-Path $references 'handoff\策划案格式交接规范.md') -Force

foreach ($file in Get-ChildItem -LiteralPath (Join-Path $skill2 'references') -File) {
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $references 'formatting') -Force
}
$formatWorkflow = Join-Path $references 'formatting\format-workflow.md'
Copy-Item -LiteralPath (Join-Path $skill2 'references\format-workflow.md') -Destination $formatWorkflow -Force
$formatContent = Get-Content -LiteralPath $formatWorkflow -Raw -Encoding UTF8
$formatContent = $formatContent.Replace('python scripts/format_proposal.py', 'python ../../scripts/format_proposal.py')
Set-Content -LiteralPath $formatWorkflow -Value $formatContent -Encoding UTF8

foreach ($item in Get-ChildItem -LiteralPath (Join-Path $skill2 'scripts') -Force) {
    Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $release 'scripts') -Recurse -Force
}

@'
# 发布包参考资料索引

本目录中的参考文件随 Skill 一同分发，所有运行时引用均相对本 Skill 包：

- `workflow.md`：框架设计、模块填写、跨模块确认、全文确认和 Markdown 交接流程。
- `knowledge/framework-design-research.md`：活动需求与历史案例章节之间的关系，以及新活动框架的判断方法。
- `knowledge/content-granularity.md`：一级标题、二级标题、正文条目和表格的颗粒度选择。
- `knowledge/activity-experience.md`：不同活动类型的经验及适用条件。
- `knowledge/cautions.md`：事实边界、案例差异、疑点与知识维护提醒。
- `knowledge/sources.md`：案例类型、编号和知识提炼使用的章节位置；原始文件不随包分发。
- `templates/outline-format.md`：框架的对话展示样式参考。
- `templates/task-intake.md`：任务信息识别维度，不是强制表单。
- `handoff/策划案格式交接规范.md`：全文确认后生成 Markdown 的接口约定。
- `formatting/format-workflow.md`、`formatting/input-contract.md`、`formatting/format-rules.md`、`formatting/format-profile.json`：Word 阶段流程、输入结构、格式规则和机器配置。

按当前任务读取相关文件，不要一次加载全部案例知识。历史经验用于校准本次框架，不是固定模板。
'@ | Set-Content -LiteralPath (Join-Path $references 'project-knowledge-map.md') -Encoding UTF8

$unexpectedSourceFiles = Get-ChildItem -LiteralPath $release -Recurse -File | Where-Object {
    $_.Extension -in @('.pdf', '.docx')
}
if ($unexpectedSourceFiles) {
    throw "发布包包含原始 PDF/DOCX，请移除：$($unexpectedSourceFiles.FullName -join ', ')"
}

$brokenLinks = [Collections.Generic.List[string]]::new()
foreach ($markdown in Get-ChildItem -LiteralPath $release -Recurse -File -Filter '*.md') {
    $text = Get-Content -LiteralPath $markdown.FullName -Raw -Encoding UTF8
    foreach ($match in [regex]::Matches($text, '\]\(([^)]+)\)')) {
        $destination = $match.Groups[1].Value
        if ($destination -match '^(https?://|mailto:|#)') { continue }
        $localPath = ($destination -split '#', 2)[0]
        if (-not $localPath) { continue }
        $resolved = [IO.Path]::GetFullPath((Join-Path $markdown.DirectoryName $localPath))
        if (-not (Test-Path -LiteralPath $resolved)) {
            $brokenLinks.Add("$($markdown.FullName): $destination")
        }
    }
}
if ($brokenLinks.Count -gt 0) {
    throw "发布包存在失效链接：`n$($brokenLinks -join "`n")"
}

$manifest = Join-Path $release 'MANIFEST.sha256'
$lines = Get-ChildItem -LiteralPath $release -Recurse -File | Where-Object {
    $_.FullName -ne $manifest
} | Sort-Object FullName | ForEach-Object {
    $relative = [IO.Path]::GetRelativePath($release, $_.FullName).Replace('\', '/')
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $relative"
}
$lines | Set-Content -LiteralPath $manifest -Encoding UTF8
Write-Output "发布包已更新：$release"
Write-Output "包含 $((Get-ChildItem -LiteralPath $release -Recurse -File).Count) 个文件；Markdown 链接和原始附件检查通过。"
