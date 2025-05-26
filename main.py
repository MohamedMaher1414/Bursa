from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import requests
import re
import os

# إعدادات Notion من GitHub Secrets
NOTION_TOKEN = "Bearer " + os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

HEADERS = {
    "Authorization": NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def fetch_prices():
    url = "https://www.elmorshdledwagn.com/prices/l2"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # استخدام المسار الصحيح لـ chromedriver المثبت عبر Snap
    service = Service(executable_path="/snap/bin/chromium.chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    prices = {
        "white_meat_market": None,
        "white_meat_execution": None,
        "chick_high": None,
        "chick_low": None,
    }

    table = soup.find("table")
    if not table:
        print("❌ لم يتم العثور على جدول الأسعار.")
        return prices

    rows = table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all("td")
        if len(cols) != 4:
            continue

        item = cols[0].get_text(strip=True).replace(" ", "")
        item = re.sub(r"[^؀-ۿ]+", "", item)

        price1 = cols[1].get_text(strip=True).replace(",", "").replace("٫", ".")
        price2 = cols[2].get_text(strip=True).replace(",", "").replace("٫", ".")

        try:
            price1 = float(price1)
            price2 = float(price2)
        except ValueError:
            continue

        if "اللحمالابيض" in item:
            prices["white_meat_market"] = price1
            prices["white_meat_execution"] = price2
        elif "معلنشركاتالكتاكيت" in item:
            prices["chick_high"] = price1
            prices["chick_low"] = price2

    if prices["white_meat_execution"] == 0 and prices["white_meat_market"] is not None:
        prices["white_meat_execution"] = prices["white_meat_market"] - 1

    print("✅ Extracted prices:", prices)
    return prices

def add_to_notion(prices):
    today = datetime.today().strftime("%Y-%m-%d")
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"بيانات يوم {today}"}}]},
            "التاريخ": {"date": {"start": today}},
            "سعر اللحم الأبيض - السوق": {"number": prices["white_meat_market"]},
            "سعر اللحم الأبيض - التنفيذ": {"number": prices["white_meat_execution"]},
            "سعر الكتكوت - أعلى": {"number": prices["chick_high"]},
            "سعر الكتكوت - أقل": {"number": prices["chick_low"]},
        },
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, data=json.dumps(payload))
    if res.status_code == 200 or res.status_code == 201:
        print("✅ تم إضافة البيانات إلى نوتشن.")
    else:
        print("❌ خطأ أثناء الإرسال:", res.text)

if __name__ == "__main__":
    prices = fetch_prices()
    add_to_notion(prices)
