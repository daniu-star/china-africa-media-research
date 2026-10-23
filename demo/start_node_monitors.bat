@echo off
echo 启动分布式爬虫节点监控系统
echo ================================

REM 获取当前活跃的工作节点
for /f "tokens=*" %%i in ('powershell -Command "Get-Content distributed_worker.log | Select-String 'worker-' | Select-String '已向主节点注册' | Select-Object -Last 10 | ForEach-Object { $_.Line -split ' ' | Select-Object -Last 1 } | Sort-Object -Unique") do (
    set "worker=%%i"
    echo 启动监控窗口: %%i
    start "监控节点 %%i" cmd /k "python node_monitor.py --worker %%i"
    timeout /t 2 /nobreak > nul
)

echo.
echo 启动主节点监控窗口
start "监控主节点" cmd /k "python node_monitor.py --master"

echo.
echo 所有监控窗口已启动
echo 按任意键退出此脚本...
pause > nul