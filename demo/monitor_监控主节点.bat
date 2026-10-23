@echo off
title 监控主节点
echo 监控主节点
echo 开始时间: %date% %time%
echo ------------------------------
powershell -Command "while($true) { Get-Content distributed_master.log -Tail 3; Write-Host '[$(Get-Date -Format "HH:mm:ss")] 主节点状态'; Start-Sleep 10 }"
pause
