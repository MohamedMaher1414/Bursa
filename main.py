from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests, time, datetime, os

def inspect_elmorshed():
    options = Options()
    # ✅ إعدادات متوافقة مع GitHub Actions (بيئة بدون واجهة رسومية)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.elmorshdledwagn.com/prices/l2")
    time.sleep(5)

    tables = driver.find_elements("tag name", "table")
    all_data = []
    for table in tables:
        rows = table.find_elements("tag name", "tr")
        for row in rows:
            cols = [c.text.strip().replace("\n", "") for c in row.find_elements("tag name", "td")]
            if cols:
                all_data.append(cols)
    driver.quit()

    print("\n📋 --- All Table Data ---\n")
    for r in all_data:
        print(r)

    data = {
        "white_meat_market": 0,
        "white_meat_execution": 0,
        "saso_meat_high": 0,
        "saso_meat_low": 0,
        "chick_high": 0,
        "chick_low": 0,
        "saso_pure_high": 0,
        "saso_pure_low": 0,
        "egg_white_high": 0,
        "egg_white_low": 0,
        "egg_red_high": 0,
        "egg_red_low": 0
    }

    for row in all_data:
        name = row[0].replace(" ", "").replace("(", "").replace(")", "").lower()
        try:
            if "اللحم" in name and "الابيض" in name:
                data["white_meat_market"] = float(row[1].replace("00", "0") or 0)
                data["white_meat_execution"] = float(row[2].replace("00", "0") or 0)
            elif "الساسو" in name and "اللحم" in name:
                data["saso_meat_high"] = float(row[1] or 0)
                data["saso_meat_low"] = float(row[2] or 0)
            elif "شركاتالكتاكيت" in name:
                data["chick_high"] = float(row[1] or 0)
                data["chick_low"] = float(row[2] or 0)
            elif "كتكوتساسوبيور" in name:
                data["saso_pure_high"] = float(row[1] or 0)
                data["saso_pure_low"] = float(row[2] or 0)
            elif "بيضابيض" in name:
                data["egg_white_high"] = float(row[1] or 0)
                data["egg_white_low"] = float(row[2] or 0)
            elif "بيضاحمر" in name:
                data["egg_red_high"] = float(row[1] or 0)
                data["egg_red_low"] = float(row[2] or 0)
        except:
            continue

    # 🧠 منطق التعامل مع الأصفار
    if data["white_meat_execution"] == 0:
        data["white_meat_execution"] = data["white_meat_market"] - 1
    if data["saso_meat_low"] == 0:
        data["saso_meat_low"] = data["saso_meat_high"] - 1
    if data["saso_pure_low"] == 0:
        data["saso_pure_low"] = data["saso_pure_high"] - 1
    if data["egg_white_low"] == 0:
        data["egg_white_low"] = data["egg_white_high"] - 1
    if data["egg_red_low"] == 0:
        data["egg_red_low"] = data["egg_red_high"] - 1

    print("\n✅ Extracted prices:", data)
    return data


def send_to_notion(data):
    # ✅ جلب القيم من Secrets (من GitHub Actions)
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")

    if not notion_token or not database_id:
        print("❌ Missing Notion credentials! تأكد إنك ضايف secrets في GitHub.")
        return

    today = datetime.date.today()
    formatted_date = today.strftime("%Y-%m-%d")

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": f"بيانات المرشد {formatted_date}"}}]},
            "التاريخ": {"date": {"start": formatted_date}},
            "سعر اللحم الأبيض - السوق": {"number": data["white_meat_market"]},
            "سعر اللحم الأبيض - التنفيذ": {"number": data["white_meat_execution"]},
            "سعر اللحم الساسو - أعلى": {"number": data["saso_meat_high"]},
            "سعر اللحم الساسو - أقل": {"number": data["saso_meat_low"]},
            "سعر الكتكوت - أعلى": {"number": data["chick_high"]},
            "سعر الكتكوت - أقل": {"number": data["chick_low"]},
            "كتكوت ساسو بيور - أعلى": {"number": data["saso_pure_high"]},
            "كتكوت ساسو بيور - أقل": {"number": data["saso_pure_low"]},
            "بيض أبيض - أعلى": {"number": data["egg_white_high"]},
            "بيض أبيض - أقل": {"number": data["egg_white_low"]},
            "بيض أحمر - أعلى": {"number": data["egg_red_high"]},
            "بيض أحمر - أقل": {"number": data["egg_red_low"]}
        }
    }

    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("✅ تم الإرسال بنجاح إلى Notion.")
    else:
        print("❌ خطأ أثناء الإرسال:", res.text)


if __name__ == "__main__":
    data = inspect_elmorshed()
    send_to_notion(data)
