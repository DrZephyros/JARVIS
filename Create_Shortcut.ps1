$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$HOME\Desktop\JARVIS.lnk")

# Point the shortcut directly to PowerShell to silently elevate python and run main.py
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-WindowStyle Hidden -Command `"Start-Process python -ArgumentList 'main.py' -Verb RunAs -WorkingDirectory '$PWD'`""
$Shortcut.WorkingDirectory = "$PWD"

# Give the shortcut the JARVIS logo!
$Shortcut.IconLocation = "$PWD\jarvis_logo.ico"

$Shortcut.Save()
Write-Host "JARVIS Desktop shortcut created successfully!"
