import re

def clean_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # حذف کاراکترهای نیم‌فاصله (U+200C) و صفرعرض (U+200B)
    cleaned_content = content.replace('\u200c', '').replace('\u200b', '')

    # حذف تمام کاراکترهای غیرانگلیسی (شامل کاراکترهای فارسی و غیره)
    cleaned_content = re.sub(r'[^\x00-\x7F]+', '', cleaned_content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

# اجرای پاک‌سازی فایل اصلی
clean_file('paid4.py', 'cleaned_paid4_final.py')

print("کاراکترهای نامرئی و غیرانگلیسی از فایل حذف شدند. فایل جدید: cleaned_paid3_final.py")
