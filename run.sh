#!/bin/bash

# نام محیط مجازی
VENV_DIR="venv"

# بررسی وجود محیط مجازی
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# فعال‌سازی محیط مجازی
source $VENV_DIR/bin/activate

# ارتقاء pip
pip install --upgrade pip

# نصب کتابخانه‌های مورد نیاز
pip install -r requirements.txt

# اجرای اسکریپت‌ها به صورت همزمان
echo "Running proxy.py and grass.py..."
python proxy.py &
python grass.py &

# منتظر ماندن تا پایان اجرای اسکریپت‌ها
wait
