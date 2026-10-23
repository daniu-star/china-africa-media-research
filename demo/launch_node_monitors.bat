@echo off
echo 分布式爬虫系统 - 独立节点监控器
echo ===============================================

echo.
echo 正在启动主节点监控终端...
start "监控主节点" cmd /k "echo === 主节点实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_master.log -Tail 3; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] 主节点状态\"; Start-Sleep 10 }\""
timeout /t 2 /nobreak > nul

echo.
echo 正在启动工作节点监控终端...

REM 工作节点 1: worker-95ccd08a
echo 启动监控终端: worker-95ccd08a
start "监控节点 worker-95ccd08a" cmd /k "echo === 工作节点 worker-95ccd08a 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-95ccd08a' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-95ccd08a 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

REM 工作节点 2: worker-dbb70d77
echo 启动监控终端: worker-dbb70d77
start "监控节点 worker-dbb70d77" cmd /k "echo === 工作节点 worker-dbb70d77 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-dbb70d77' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-dbb70d77 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

REM 工作节点 3: worker-22e43c87
echo 启动监控终端: worker-22e43c87
start "监控节点 worker-22e43c87" cmd /k "echo === 工作节点 worker-22e43c87 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-22e43c87' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-22e43c87 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

REM 工作节点 4: worker-977359c1
echo 启动监控终端: worker-977359c1
start "监控节点 worker-977359c1" cmd /k "echo === 工作节点 worker-977359c1 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-977359c1' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-977359c1 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

REM 工作节点 5: worker-02385af4
echo 启动监控终端: worker-02385af4
start "监控节点 worker-02385af4" cmd /k "echo === 工作节点 worker-02385af4 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-02385af4' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-02385af4 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

REM 工作节点 6: worker-a4a44531
echo 启动监控终端: worker-a4a44531
start "监控节点 worker-a4a44531" cmd /k "echo === 工作节点 worker-a4a44531 实时监控 === && echo 开始时间: %date% %time% && echo ------------------------------ && powershell -Command \"while(\$true) { Get-Content distributed_worker.log | Select-String 'worker-a4a44531' | Select-Object -Last 5; Write-Host \"[\$(Get-Date -Format 'HH:mm:ss')] worker-a4a44531 最新动态\"; Start-Sleep 5 }\""
timeout /t 1 /nobreak > nul

echo.
echo 已启动 7 个独立监控终端:
echo - 1个主节点监控终端
echo - 6个工作节点监控终端
echo.
echo 每个终端将独立显示对应节点的实时爬取动态
echo 监控窗口已打开，请查看桌面上的新窗口
echo.
echo 按任意键退出此脚本...
pause > nul