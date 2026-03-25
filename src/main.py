from playwright.sync_api import sync_playwright
import os

def run_automation_with_json():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="msedge", # Change to True when ready
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )

        # --- THIS IS THE CRITICAL LINE ---
        # Create a new context, but inject our saved cookies and storage first
        auth_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "auth.json"))
        print(f"Loading session from {auth_path}...")
        
        try:
            context = browser.new_context(
                storage_state=auth_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            )
        except Exception as e:
            print(f"Failed to load auth state from {auth_path}. Exception: {e}")
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            )

        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        print("Navigating to the site...")
        page.goto("https://gemini.google.com")

        print("You should be instantly logged in!")
        
        # Put your actual automation logic here
        page.wait_for_timeout(10000) # Just pausing so you can see it worked
        
        browser.close()

if __name__ == "__main__":
    run_automation_with_json()