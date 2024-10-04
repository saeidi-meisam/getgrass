@echo off

:: نام محیط مجازی
set VENV_DIR=venv

:: بررسی وجود محیط مجازی
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: فعال‌سازی محیط مجازی
call %VENV_DIR%\Scripts\activate.bat

:: ارتقاء pip
python -m pip install --upgrade pip

:: نصب کتابخانه‌های مورد نیاز
pip install -r requirements.txt

:: اجرای اسکریپت‌ها به صورت همزمان
echo Running proxy.py and grass.py...
start python proxy.py
start python grass.py

:: نگه داشتن پنجره باز
pause

