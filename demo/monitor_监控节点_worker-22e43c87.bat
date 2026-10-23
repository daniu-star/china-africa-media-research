@echo off
title 监控节点 worker-22e43c87
echo 监控节点 worker-22e43c87
echo 开始时间: %date% %time%
echo ------------------------------
powershell -Command "while($true) { Get-Content distributed_worker.log | Select-String 'worker-22e43c87' | Select-Object -Last 5; Write-Host '[$(Get-Date -Format "HH:mm:ss")] worker-22e43c87 最新动态'; Start-Sleep 5 }"
pause
