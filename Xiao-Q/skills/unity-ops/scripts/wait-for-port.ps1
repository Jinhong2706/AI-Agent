<#
.SYNOPSIS
    轮询等待 UnityOps TCP 端口就绪
.DESCRIPTION
    在启动 Unity 后轮询检测指定端口是否开始监听，
    用于等待 Unity 编辑器加载完成并自动启动服务。
.PARAMETER Port
    目标端口号（默认 8888）
.PARAMETER MaxWaitSeconds
    最长等待秒数（默认 120）
.PARAMETER IntervalSeconds
    轮询间隔秒数（默认 5）
.OUTPUTS
    [PSCustomObject] 包含 connected（bool）、elapsed（int）、pid（int/null）字段
#>

param(
    [int]$Port = 8888,
    [int]$MaxWaitSeconds = 120,
    [int]$IntervalSeconds = 5
)

$elapsed = 0
$connected = $false
$pidInfo = $null

while ($elapsed -lt $MaxWaitSeconds) {
    Start-Sleep -Seconds $IntervalSeconds
    $elapsed += $IntervalSeconds

    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "✅ 端口 $Port 已监听！PID: $($conn.OwningProcess)，耗时 ${elapsed}s"
        $connected = $true
        $pidInfo = $conn.OwningProcess
        break
    } else {
        Write-Host "等待中... ${elapsed}s / ${MaxWaitSeconds}s"
    }
}

if (-not $connected) {
    Write-Host "⚠️ 超时（${MaxWaitSeconds}s），端口 $Port 仍未监听"
}

return [PSCustomObject]@{
    connected = $connected
    elapsed   = $elapsed
    pid       = $pidInfo
}
