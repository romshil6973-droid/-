$proj = $PSScriptRoot
$pyw  = "C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"

if (-not (Test-Path $pyw)) {
    $pyw = "C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe"
}

# 1. Create VBS launcher
$vbsPath = "$proj\launch_silent.vbs"
$vbs = "Set wsh = CreateObject(""WScript.Shell"")" + "`r`n" + "wsh.Run """"""$pyw"""""" """"""$proj\main.py"""""", 0, False"
Set-Content -Path $vbsPath -Value $vbs -Encoding UTF8
Write-Host "[1/3] launch_silent.vbs created: $vbsPath"

# 2. Fix registry
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $regPath -Name "WorkdayMonitor" -Value "wscript.exe `"$vbsPath`""
Write-Host "[2/3] Registry updated"

# 3. Desktop shortcut
$desktop = [Environment]::GetFolderPath("Desktop")
$wshCom = New-Object -ComObject WScript.Shell
$sc = $wshCom.CreateShortcut("$desktop\WorkdayMonitor.lnk")
$sc.TargetPath = "wscript.exe"
$sc.Arguments = "/b `"$vbsPath`""
$sc.WorkingDirectory = $proj
$sc.Description = "WorkdayMonitor"
$sc.Save()
Write-Host "[3/3] Desktop shortcut created"

Write-Host ""
Write-Host "Done!"
Read-Host "Press Enter to close"
