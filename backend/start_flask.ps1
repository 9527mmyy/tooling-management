$env:QCLAW_PYTHON_BINARY = "C:\Users\SHICHETAI-4\AppData\Local\Programs\Python\Python311\python.exe"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Set-Location D:\tooling-management\backend
Start-Process -NoNewWindow -FilePath "$env:QCLAW_PYTHON_BINARY" -ArgumentList "app.py"
