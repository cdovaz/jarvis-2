from playwright.sync_api import sync_playwright
import os

def save_session_to_json():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        )

        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()

        print("Navigating to the site...")
        page.goto("https://gemini.google.com")

        print("Please log in manually. The script will wait 60 seconds...")
        print("Tip: increase the timeout below if you need more time for 2FA.")
        page.wait_for_timeout(60000)

        # Better path resolution so it works regardless of where you run it from
        auth_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "auth.json"))
        os.makedirs(os.path.dirname(auth_path), exist_ok=True)

        print(f"Time is up! Exporting session to {auth_path}...")
        context.storage_state(path=auth_path)

        browser.close()
        print(f"Session successfully saved to {auth_path}!")

if __name__ == "__main__":
    save_session_to_json()