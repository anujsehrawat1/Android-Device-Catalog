import asyncio
import json
import os
import requests
import urllib3
import time
import subprocess
from datetime import datetime
from dateutil.relativedelta import relativedelta
from playwright.async_api import async_playwright

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic paths based on script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

URL = "https://play.google.com/console/u/0/developers/7715734609584840872/app/4974982827268905496/devices?mode=allDevices"
USER_DATA_DIR = os.path.join(BASE_DIR, "scraper", "playwright_profile")
JSON_FILE = os.path.join(BASE_DIR, "data", "devices.json")
JS_FILE = os.path.join(BASE_DIR, "data", "devices_data.js")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

def get_existing_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Create a set of existing models for fast lookup
            existing_models = {d.get("Model", "") for d in data}
            return data, existing_models
    return [], set()

def download_image(session, original_url, model_name):
    if not original_url or not original_url.startswith("http"):
        return None
    
    # Format filename safely
    safe_model = str(model_name).replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '_')
    filename = f"{safe_model}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    # Download with retries
    for attempt in range(3):
        try:
            r = session.get(original_url, timeout=10, verify=False)
            if r.status_code == 200:
                header = r.content[:10]
                # Check actual format
                if header.startswith(b'<?xml') or header.startswith(b'<svg'):
                    filename = f"{safe_model}.svg"
                elif header[:4] == b'RIFF':
                    filename = f"{safe_model}.webp"
                    
                filepath = os.path.join(IMAGES_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(r.content)
                return f"/images/{filename}"
            else:
                return None
        except Exception as e:
            print(f"Retry {attempt+1}/3 failed for image: {e}")
            time.sleep(2)
    return None

def save_data(all_devices):
    # Save JSON
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_devices, f, indent=4)
        
    # Save JS
    with open(JS_FILE, "w", encoding="utf-8") as f:
        f.write("window.DEVICES_DATA = " + json.dumps(all_devices) + ";")

def git_commit_and_push(new_count):
    print("Pushing to GitHub...")
    subprocess.run(["git", "add", "data/", "images/"], cwd=BASE_DIR)
    subprocess.run(["git", "commit", "-m", f"Automated Update: Added {new_count} new devices"], cwd=BASE_DIR)
    res = subprocess.run(["git", "push"], cwd=BASE_DIR)
    if res.returncode == 0:
        print("GitHub update successful! 🎉")
    else:
        print("Failed to push to GitHub. You may need to push manually.")

async def main():
    months_ago = input("Kitne mahine purane devices chahiye? (Enter number, e.g., 1, 2, 6): ").strip()
    try:
        months_ago = int(months_ago)
    except:
        print("Invalid number. Exiting.")
        return

    target_date = datetime.now() - relativedelta(months=months_ago)
    # Format exactly as required: "Aug 1, 2026"
    date_str = target_date.strftime("%b %-d, %Y") if os.name != 'nt' else target_date.strftime("%b %#d, %Y")
    print(f"Applying filter for date: {date_str}")

    all_devices, existing_models = get_existing_data()
    print(f"Loaded {len(all_devices)} existing devices from database.")
    
    # Initialize Requests session for images
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    new_devices_added = []

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        print("Navigating to Play Console...")
        await page.goto(URL, timeout=60000)

        print("Waiting for page load...")
        try:
            await page.wait_for_selector("div.particle-table-row", timeout=15000)
        except:
            await asyncio.to_thread(input, "Table not found automatically. Press Enter here when devices page is loaded...")

        # APPLY FILTER
        print("Applying Date Filter...")
        try:
            # Click "Add filter" input box
            await page.click('input[aria-label="Add filter"]', timeout=5000)
            await page.wait_for_timeout(500)
            
            # Click "Date added to catalog"
            await page.click('[aria-label="Date added to catalog"]', timeout=5000)
            await page.wait_for_timeout(1000)
            
            # Fill the date in the date picker input
            date_input = page.locator('input.input-area').first
            await date_input.click()
            await date_input.fill(date_str)
            # Press 'Enter' or 'Tab' so Angular registers the change and enables 'Apply'
            await date_input.press("Enter")
            await page.wait_for_timeout(500)
            
            # Click Apply button
            await page.click('material-button[aria-label="Apply"]')
            print("Filter applied successfully! Waiting for results to load...")
            await page.wait_for_timeout(3000) # Wait for table refresh
        except Exception as e:
            print(f"Could not apply filter automatically. Error: {e}")
            await asyncio.to_thread(input, "Please apply the filter manually in the browser and press Enter here...")

        current_page = 1
        while True:
            print(f"Scanning page {current_page}...")
            await page.wait_for_selector("div.particle-table-row", timeout=10000)
            await page.wait_for_timeout(100)

            rows = await page.locator("div.particle-table-row").all()
            for row in rows:
                try:
                    cols = await row.locator("ess-cell").all()
                    if len(cols) >= 5:
                        model = await cols[1].inner_text()
                        model = model.strip()
                        
                        # Check if device is new
                        if model not in existing_models:
                            name = await cols[3].inner_text()
                            version = await cols[4].inner_text()
                            
                            img_loc = row.locator("img").first
                            img_url = await img_loc.get_attribute("src") if await img_loc.count() > 0 else ""
                            
                            print(f"Found NEW device: {name} ({model})")
                            
                            # Download image
                            local_img_path = download_image(session, img_url, model)
                            
                            new_device = {
                                "Name": name.strip(),
                                "Model": model,
                                "Version": version.strip(),
                                "Image_URL": local_img_path
                            }
                            
                            new_devices_added.append(new_device)
                            all_devices.append(new_device)
                            existing_models.add(model)
                except Exception as e:
                    print(f"Error extracting row: {e}")
            
            # Go to next page
            next_btn = page.locator("material-button.next") 
            if await next_btn.count() > 0 and await next_btn.is_visible() and not await next_btn.get_attribute("aria-disabled") == "true":
                await next_btn.click()
                current_page += 1
                await page.wait_for_timeout(200)
            else:
                print("No more pages. Scraping finished.")
                break
        
        await browser.close()
        
    # Save & Push
    if new_devices_added:
        print(f"Successfully added {len(new_devices_added)} new devices.")
        save_data(all_devices)
        git_commit_and_push(len(new_devices_added))
    else:
        print("No new devices found for the specified period.")

if __name__ == "__main__":
    try:
        import dateutil
    except ImportError:
        print("Installing required package 'python-dateutil'...")
        subprocess.run(["pip", "install", "python-dateutil"])
        
    asyncio.run(main())
