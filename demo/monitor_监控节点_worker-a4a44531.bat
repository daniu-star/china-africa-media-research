@echo off
title 监控节点 worker-a4a44531
echo 监控节点 worker-a4a44531
echo 开始时间: %date% %time%
echo ------------------------------
powershell -Command "while($true) { Get-Content distributed_worker.log | Select-String 'worker-a4a44531' | Select-Object -Last 5; Write-Host '[$(Get-Date -Format "HH:mm:ss")] worker-a4a44531 最新动态'; Start-Sleep 5 }"
pause
