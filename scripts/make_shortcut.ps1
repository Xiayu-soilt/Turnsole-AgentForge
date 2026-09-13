$desktop = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$desktop\Turnsole AgentForge 启动.lnk")
$lnk.TargetPath = 'd:\project9_ai\botforge\scripts\start_all.bat'
$lnk.WorkingDirectory = 'd:\project9_ai\botforge\scripts'
$lnk.IconLocation = 'd:\project9_ai\botforge\scripts\agentforge.ico, 0'
$lnk.Description = '一键启动 Turnsole AgentForge（MySQL + 后端 + 前端 + 自动打开浏览器）'
$lnk.Save()
Write-Host "shortcut created: $desktop\Turnsole AgentForge 启动.lnk"
Write-Host (Test-Path "$desktop\Turnsole AgentForge 启动.lnk")
