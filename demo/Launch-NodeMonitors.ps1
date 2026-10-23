# 分布式爬虫系统 - 独立节点监控器
Write-Host "分布式爬虫系统 - 独立节点监控器" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# 工作节点列表
$workers = @(
    "worker-95ccd08a",
    "worker-dbb70d77", 
    "worker-22e43c87",
    "worker-977359c1",
    "worker-02385af4",
    "worker-a4a44531"
)

Write-Host "`n正在启动主节点监控终端..." -ForegroundColor Yellow
# 启动主节点监控
$masterCommand = @"
echo === 主节点实时监控 ===
echo 开始时间: $(Get-Date)
echo ------------------------------
powershell -Command "while(`$true) { Get-Content distributed_master.log -Tail 3; Write-Host \"[`$(Get-Date -Format 'HH:mm:ss')] 主节点状态\"; Start-Sleep 10 }"
"@

Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $masterCommand -WindowStyle Normal -Title "监控主节点"

Start-Sleep 2

Write-Host "`n正在启动工作节点监控终端..." -ForegroundColor Yellow

# 为每个工作节点启动独立的监控终端
foreach ($worker in $workers) {
    Write-Host "启动监控终端: $worker" -ForegroundColor Cyan
    
    $title = "监控节点 $worker"
    $workerCommand = @"
echo === 工作节点 $worker 实时监控 ===
echo 开始时间: $(Get-Date)
echo ------------------------------
powershell -Command "while(`$true) { Get-Content distributed_worker.log | Select-String '$worker' | Select-Object -Last 5; Write-Host \"[`$(Get-Date -Format 'HH:mm:ss')] $worker 最新动态\"; Start-Sleep 5 }"
"@
    
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $workerCommand -WindowStyle Normal -Title $title
    
    Start-Sleep 1
}

Write-Host "`n已启动 $($workers.Count + 1) 个独立监控终端:" -ForegroundColor Green
Write-Host "- 1个主节点监控终端" -ForegroundColor Green
Write-Host "- $($workers.Count)个工作节点监控终端" -ForegroundColor Green
Write-Host "`n每个终端将独立显示对应节点的实时爬取动态" -ForegroundColor Green
Write-Host "监控窗口已打开，请查看桌面上的新窗口" -ForegroundColor Green

Write-Host "`n按任意键退出此脚本..." -ForegroundColor Yellow
Read-Host "按Enter键继续"