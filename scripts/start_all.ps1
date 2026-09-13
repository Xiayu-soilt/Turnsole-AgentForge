$ProgressPreference = 'SilentlyContinue'

$Root = 'd:\project9_ai\botforge'
$BackendDir = Join-Path $Root 'backend'
$FrontendDir = Join-Path $Root 'frontend'
$BackendPython = Join-Path $BackendDir 'venv\Scripts\python.exe'
$BackendUrl = 'http://localhost:8000'
$FrontendUrl = 'http://localhost:5175'

function Test-Port {
    param($Port)
    $c = New-Object Net.Sockets.TcpClient
    try { $c.Connect('127.0.0.1', $Port); return $true } catch { return $false } finally { $c.Close() }
}

function Test-Url {
    param($Url)
    & curl.exe -s -o NUL --max-time 3 $Url 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Wait-Url {
    param($Url, $MaxSec, $Label)
    Write-Host "  [等待] $Label 启动中 " -NoNewline
    for ($i = 0; $i -lt $MaxSec; $i++) {
        if (Test-Url $Url) { Write-Host ' [OK]' -ForegroundColor Green; return $true }
        Write-Host '.' -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
    Write-Host ''
    return $false
}

Write-Host ''
Write-Host '  =================================================='
Write-Host '        Turnsole AgentForge 智能体工厂 · 一键启动'
Write-Host '  =================================================='
Write-Host ''

# ---------- 0) 检查 MySQL ----------
if (Test-Port 3306) {
    Write-Host '  [OK] MySQL 运行中' -ForegroundColor Green
} else {
    Write-Host '  [提示] MySQL 未运行，尝试启动 MySQL80 服务...' -ForegroundColor Yellow
    Start-Service MySQL80 -ErrorAction SilentlyContinue
    if (Test-Port 3306) {
        Write-Host '  [OK] MySQL 服务已启动' -ForegroundColor Green
    } else {
        Write-Host '  [警告] 无法自动启动 MySQL，请手动启动后重试' -ForegroundColor Red
        exit 1
    }
}

# ---------- 1) 后端 FastAPI :8000 ----------
if (Test-Url "$BackendUrl/docs") {
    Write-Host '  [OK] 后端已在运行，跳过启动' -ForegroundColor Green
} else {
    if (Test-Port 8000) {
        # 端口已被占用但 HTTP 未就绪：极可能是本项目的后端正在启动，避免重复启动导致端口冲突
        Write-Host '  [等待] 端口 8000 已被占用（后端可能正在启动），不再重复启动'
    } else {
        Write-Host '  [启动] 后端 FastAPI 开发服务器（首次加载模型约需 10~60 秒）...'
        Start-Process cmd "/k title Turnsole AgentForge Backend :8000 && $BackendPython run.py" -WorkingDirectory $BackendDir
    }
    if (-not (Wait-Url "$BackendUrl/docs" 90 '后端')) {
        Write-Host '  [警告] 后端 90 秒内未就绪，请查看后端窗口中的报错信息' -ForegroundColor Red
        exit 1
    }
    Write-Host '  [OK] 后端就绪  http://localhost:8000' -ForegroundColor Green
}

# ---------- 2) 前端 Vite :5175 ----------
if (Test-Url $FrontendUrl) {
    Write-Host '  [OK] 前端已在运行，跳过启动' -ForegroundColor Green
} else {
    Write-Host '  [启动] 前端 Vite 开发服务器...'
    Start-Process cmd "/k title Turnsole AgentForge Frontend :5175 && npm run dev" -WorkingDirectory $FrontendDir
    if (-not (Wait-Url $FrontendUrl 60 '前端')) {
        Write-Host '  [警告] 前端 60 秒内未就绪，请查看前端窗口中的报错信息' -ForegroundColor Red
        exit 1
    }
    Write-Host '  [OK] 前端就绪  http://localhost:5175' -ForegroundColor Green
}

# ---------- 3) 打开浏览器 ----------
Start-Process $FrontendUrl

Write-Host ''
Write-Host '  =================================================='
Write-Host '   启动完成！正在打开 http://localhost:5175'
Write-Host '   API 文档：http://localhost:8000/docs'
Write-Host '   停止服务：运行 scripts\stop_all.bat'
Write-Host '            或直接关闭两个服务窗口'
Write-Host '  =================================================='
Start-Sleep -Seconds 3
