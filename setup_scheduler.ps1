# setup_scheduler.ps1
# Registers both the 12 PM daily scan and the background interactive button listener

$PythonPath = (Get-Command py.exe).Source
$MainScript = "$PSScriptRoot\main.py"
$ListenerScript = "$PSScriptRoot\bot_listener.py"

New-Item -ItemType Directory -Path "$PSScriptRoot\logs" -Force | Out-Null

# 1. Daily 12 PM Scan Task
$ScanAction  = New-ScheduledTaskAction -Execute $PythonPath -Argument $MainScript -WorkingDirectory $PSScriptRoot
$ScanTrigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"
$ScanSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Unregister-ScheduledTask -TaskName "SandeepJobAgent" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "SandeepJobAgent" -Action $ScanAction -Trigger $ScanTrigger -Settings $ScanSettings -Description "Sandeep Job Agent - daily job scan at 12 PM IST" | Out-Null

# 2. Continuous Background Telegram Button Listener Task
$ListenerAction = New-ScheduledTaskAction -Execute $PythonPath -Argument $ListenerScript -WorkingDirectory $PSScriptRoot
$ListenerTrigger = New-ScheduledTaskTrigger -AtLogOn
$ListenerSettings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit 0

Unregister-ScheduledTask -TaskName "SandeepJobAgentListener" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "SandeepJobAgentListener" -Action $ListenerAction -Trigger $ListenerTrigger -Settings $ListenerSettings -Description "Sandeep Job Agent - Telegram interactive button callback listener" | Out-Null

Write-Host ""
Write-Host "[SUCCESS] Both tasks registered in Windows Task Scheduler!" -ForegroundColor Green
Write-Host "   1. SandeepJobAgent: Runs every day at 12:00 PM IST (Global Remote scan)" -ForegroundColor Cyan
Write-Host "   2. SandeepJobAgentListener: Runs continuously on logon to handle button clicks" -ForegroundColor Cyan
Write-Host ""
