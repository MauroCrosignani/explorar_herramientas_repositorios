# PowerShell Script to register the Daily Data Science & AI collector in Windows Task Scheduler

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$CollectorPath = Join-Path $ScriptDir "collector.py"

# Make sure collector.py exists
if (-not (Test-Path $CollectorPath)) {
    Write-Error "Could not locate collector.py at: $CollectorPath"
    exit 1
}

# Find the Python executable
$PythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Host "Python not found in PATH. Checking standard installation directories..."
    $PossiblePaths = @(
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python*\python.exe",
        "$env:SystemDrive\Python*\python.exe",
        "$env:ProgramFiles\Python*\python.exe"
    )
    foreach ($PathPattern in $PossiblePaths) {
        $Matches = Resolve-Path $PathPattern -ErrorAction SilentlyContinue
        if ($Matches) {
            $PythonExe = $Matches[0].Path
            break
        }
    }
}

if (-not $PythonExe) {
    Write-Error "Python executable could not be found. Please ensure Python is installed and added to your system PATH."
    exit 1
}

# Look for pythonw.exe (windowless python) in the same directory as python.exe
$PythonDir = Split-Path $PythonExe
$PythonwExe = Join-Path $PythonDir "pythonw.exe"
if (Test-Path $PythonwExe) {
    $ExeToUse = $PythonwExe
    Write-Host "Using silent windowless executable: $ExeToUse"
} else {
    $ExeToUse = $PythonExe
    Write-Host "Using standard executable: $ExeToUse"
}

# Task Configuration
$TaskName = "DailyDataScienceAIExplorer"
$TriggerTime = "19:00" # 7:00 PM daily
$Description = "Runs the Daily Data Science & AI Explorer RSS + GitHub collector script."

Write-Host "Configuring Scheduled Task..."
Write-Host "Project directory: $ProjectDir"
Write-Host "Collector path: $CollectorPath"
Write-Host "Trigger daily at: $TriggerTime"

# Build Scheduled Task Elements (19:00 daily - requires no admin rights)
$Action = New-ScheduledTaskAction -Execute $ExeToUse -Argument "`"$CollectorPath`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register Task Scheduler Task
try {
    # Check if task already exists and delete it to prevent overlap
    Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description $Description -Force
    Write-Host "Task Scheduler trigger registered for daily 19:00 execution." -ForegroundColor Green
}
catch {
    Write-Warning "Failed to register Task Scheduler: $_"
}

# Register Logon execution via User Startup Folder (bypasses Windows Admin permission limits)
try {
    $StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
    $StartupBat = Join-Path $StartupFolder "DailyDataScienceCollector.bat"
    $BatContent = "@echo off`r`nstart `"`" `"$ExeToUse`" `"$CollectorPath`""
    [System.IO.File]::WriteAllText($StartupBat, $BatContent)
    
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host " SUCCESS: Scheduled Systems Registered Successfully!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "Task Name:      $TaskName"
    Write-Host "Daily Trigger:  Every day at $TriggerTime"
    Write-Host "Logon Trigger:  Registered via User Startup Folder"
    Write-Host "Startup Script: $StartupBat"
    Write-Host "=========================================================="
    Write-Host "The collector will run silently in the background at 7:00 PM,"
    Write-Host "AND automatically at login/boot if the 19:00 run was missed."
}
catch {
    Write-Error "Failed to register Startup Folder script: $_"
}
