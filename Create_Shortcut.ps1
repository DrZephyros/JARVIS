$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$HOME\Desktop\JARVIS.lnk")

# Point the shortcut to the invisible launcher script so no console window stays open
$Shortcut.TargetPath = "$PWD\launch_jarvis.vbs"
$Shortcut.WorkingDirectory = "$PWD"

# Give the shortcut the JARVIS logo!
$Shortcut.IconLocation = "$PWD\jarvis_logo.ico"

$Shortcut.Save()
Write-Host "JARVIS Desktop shortcut created successfully!"
