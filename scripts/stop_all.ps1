$ProgressPreference = 'SilentlyContinue'

Write-Host ''
Write-Host '  正在停止 Turnsole AgentForge 的后端与前端进程...'
Write-Host ''

# 匹配三类进程：
# 1) 启动器打开的两个控制台窗口（taskkill /T 会连带结束其子进程树：python / vite / esbuild）
# 2) 命令行包含 botforge 路径的进程（手动以绝对路径启动的场合）
# 3) 兜底：仍在监听 8000 / 5175 端口的进程
$pids = New-Object 'System.Collections.Generic.HashSet[uint32]'
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'AgentForge (Backend|Frontend)|botforge' } | ForEach-Object { [void]$pids.Add($_.ProcessId) }
foreach ($port in 8000, 5175) {
    try {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | ForEach-Object { [void]$pids.Add($_.OwningProcess) }
    } catch {}
}

if ($pids.Count -eq 0) {
    Write-Host '  没有发现正在运行的 Turnsole AgentForge 进程'
} else {
    foreach ($procId in $pids) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "  已停止 $($p.ProcessName)  PID $procId"
            taskkill /PID $procId /T /F 2>&1 | Out-Null
        }
    }
}

Write-Host ''
Write-Host '  [完成] Turnsole AgentForge 服务已停止'
