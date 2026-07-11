Set UAC = CreateObject("Shell.Application")
' Launches Python with console as Administrator (1 = normal window)
UAC.ShellExecute "C:\Program Files\Python310\python.exe", "main.py", "c:\Users\gowsa\Desktop\Coding\Jarvis", "runas", 1
