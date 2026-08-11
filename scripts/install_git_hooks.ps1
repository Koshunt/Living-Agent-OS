$root = Split-Path -Parent $PSScriptRoot
$hooks = Join-Path $root '.git\hooks'
if (-not (Test-Path -LiteralPath $hooks)) {
    throw 'This folder is not a Git worktree.'
}
$hook = Join-Path $hooks 'pre-push'
@"
#!/bin/sh
"./Bridge/.venv/Scripts/python.exe" "scripts/check_before_push.py"
"@ | Set-Content -LiteralPath $hook -Encoding utf8NoBOM
Write-Output 'Installed Agent OS pre-push check.'
