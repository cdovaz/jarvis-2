from playwright.sync_api import sync_playwright
import os
import time
import json
import re

def run_gemini_chat():
    
    with sync_playwright() as p:
    
        browser = p.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )

        auth_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "auth.json"))
        print(f"Loading session from {auth_path}...")
        
        try:
            # We load the session we just manually saved
            context = browser.new_context(
                storage_state=auth_path,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            )
        except Exception as e:
            print(f"Failed to load auth state from {auth_path}. Run main-manual-login.py first!")
            return

        # Anti-detection script
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        print("Navigating to Gemini...")
        page.goto("https://gemini.google.com/gem/4d4533767c58")

        chat_box = page.locator("rich-textarea:visible, .ql-editor:visible, [contenteditable='true']:visible, [role='textbox']:visible").last
        
        try:
            chat_box.wait_for(state="visible", timeout=15000)
        except Exception as e:
            print("Failed to find the chat input box! Taking a screenshot to 'debug_error.png'...")
            page.screenshot(path="debug_error.png", full_page=True)
            browser.close()
            print("Please check debug_error.png. You might need to accept a Terms of Service screen!")
            return

        print("\nGemini Playwright API is ready!")
        print("Type 'exit' or 'quit' to close the session.\n")
        
        while True:
            try:
                prompt_text = input("You: ")
                if not prompt_text.strip():
                    continue
                if prompt_text.strip().lower() in ['exit', 'quit']:
                    print("Exiting Gemini chat...")
                    break
                
                response_locator = page.locator("message-content")
                initial_count = response_locator.count()
                
                chat_box.focus()
                page.keyboard.insert_text(prompt_text)
                # Press Enter to send
                page.keyboard.press("Enter")
                
                # Wait for the new response bubble to appear
                for _ in range(20):
                    if response_locator.count() > initial_count:
                        break
                    page.wait_for_timeout(500)
                
                # Polling slightly to wait for text to stop updating
                previous_text = ""
                stable_count = 0
                
                for _ in range(60):  # Maximum 30 seconds wait for generation
                    current_text = response_locator.last.inner_text()
                    # If the text is not totally empty and hasn't changed
                    if current_text and current_text == previous_text:
                        stable_count += 1
                        if stable_count >= 3: # Text has been stable for 1.5 seconds
                            break
                    else:
                        stable_count = 0
                    previous_text = current_text
                    page.wait_for_timeout(500)
                    
                final_response = response_locator.last.inner_text()
                try:
                    cleaned = re.sub(r"```json|```", "", final_response).strip()
                    response_parsed = json.loads(cleaned)
                    
                    print(f"N-Error: {response_parsed['answer']}\n")
                except Exception as e:
                    print(f"Parse error: {e}")
                    print(f"Y-Error: {final_response}\n")
                
            except KeyboardInterrupt:
                print("\nInterrupted. Exiting...")
                break
            except Exception as e:
                print(f"Error during interaction: {e}")

        browser.close()


if __name__ == "__main__":
    run_gemini_chat()
