import pandas as pd
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- CONFIGURATION ---
INPUT_CSV = 'websites.csv'     # Make sure this matches your file name
OUTPUT_CSV = 'extracted_emails.csv'

def setup_driver():
    """Sets up Chrome to run specifically in Cloud Shell (Headless)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extract_emails_from_text(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_pattern, text)))

def main():
    print("--- Starting Email Scraper ---")
    
    try:
        df = pd.read_csv(INPUT_CSV)
        print(f"Loaded {len(df)} rows.")
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_CSV}")
        return

    driver = setup_driver()
    results = []

    for index, row in df.iterrows():
        # 1. GET THE NAME AND WEBSITE
        # We use .get() so it doesn't crash if the column name is slightly different
        org_name = row.get('title', 'Unknown Name') 
        raw_url = row.get('website', '')

        # 2. CHECK IF WEBSITE EXISTS
        if pd.isna(raw_url) or str(raw_url).strip() == "":
            print(f"[{index+1}] {org_name}: No website listed, skipping...")
            results.append({
                'Organization': org_name,  # <--- ADDED THIS
                'Website': 'N/A', 
                'Emails': '', 
                'Status': 'Skipped'
            })
            continue
        
        url = str(raw_url).strip()
        if not url.startswith('http'):
            url = 'http://' + url
            
        print(f"[{index+1}] {org_name}: Visiting {url}...")
        
        found_emails = []
        status = "Failed"

        try:
            driver.set_page_load_timeout(20)
            driver.get(url)
            time.sleep(2) 
            
            body_text = driver.find_element(By.TAG_NAME, "body").text
            found_emails = extract_emails_from_text(body_text)
            
            if found_emails:
                print(f"   -> Found: {found_emails}")
                status = "Success"
            else:
                print("   -> No emails found.")
                status = "No Data"

        except Exception as e:
            print(f"   -> Error: {e}")
            status = "Error"

        # 3. SAVE THE DATA WITH THE NAME
        results.append({
            'Organization': org_name,   # <--- ADDED THIS
            'Website': url,
            'Emails': ", ".join(found_emails),
            'Status': status
        })

        # Save progress every 10 rows
        if (index + 1) % 10 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)

    driver.quit()
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"--- Done! Saved to {OUTPUT_CSV} ---")

if __name__ == "__main__":
    main()
