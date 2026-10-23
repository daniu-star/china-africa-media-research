@echo off
title 监控节点 worker-02385af4
echo 监控节点 worker-02385af4
echo 开始时间: %date% %time%
echo ------------------------------
powershell -Command "while($true) { Get-Content distributed_worker.log | Select-String 'worker-02385af4' | Select-Object -Last 5; Write-Host '[$(Get-Date -Format "HH:mm:ss")] worker-02385af4 最新动态'; Start-Sleep 5 }"
pause
