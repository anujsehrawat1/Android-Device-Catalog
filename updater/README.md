# 🤖 Automated Updater

This folder contains the `updater.py` script, which is responsible for automatically updating the Android Device Catalog dataset with the latest devices from the Google Play Console.

## How It Works

Instead of re-scraping the entire Google Play Console (which takes hours for 25,000+ devices), this script smartly utilizes the Play Console's Date Filter feature:
1. It asks you how many months back you want to check for new devices.
2. It uses **Playwright** to open a Brave browser session, logs into your console, and automatically applies a filter (e.g., "Added after Aug 1, 2026").
3. It cross-references the filtered devices with the existing `../data/devices.json`.
4. If a new device is found, it automatically downloads its high-quality image (handling SVGs/WebPs), saves it to the `../images/` directory, and appends the metadata to the JSON database.
5. Finally, it commits the changes and pushes the updates directly to GitHub!

## Prerequisites

1. You must have Python installed.
2. You need Playwright and Requests:
   ```bash
   pip install playwright requests python-dateutil
   playwright install chromium
   ```
3. A Google Play Console Developer account with access to the Device Catalog.

## How to Run

Simply navigate to this folder and run the script:

```bash
cd updater
python updater.py
```

The script will ask you:
`Kitne mahine purane devices chahiye? (Enter number, e.g., 1, 2, 6):`

Enter the desired number of months (e.g., `1` for the last month), and let the automation do the rest!
