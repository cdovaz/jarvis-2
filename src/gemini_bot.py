import os
import json
import re
import asyncio
from playwright.async_api import async_playwright

# Variáveis globais privadas para manter o navegador vivo
_playwright_manager = None
_browser = None

async def _init_browser():
    """Inicializa o motor do Playwright e o navegador apenas uma vez."""
    global _playwright_manager, _browser
    
    if not _playwright_manager:
        _playwright_manager = await async_playwright().start()
        
    if not _browser:
        _browser = await _playwright_manager.chromium.launch(
            headless=False, # Mude para True em produção
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )
    return _browser

async def create_instance(url="https://gemini.google.com/gem/4d4533767c58"):
    """Cria uma nova aba (contexto isolado) e prepara o chat."""
    browser = await _init_browser()
    auth_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "auth.json"))
    
    try:
        context = await browser.new_context(
            storage_state=auth_path,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        )
    except Exception as e:
        raise Exception(f"Failed to load auth state from {auth_path}. Run main-manual-login.py first!")

    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = await context.new_page()
    await page.goto(url)

    chat_box = page.locator("rich-textarea:visible, .ql-editor:visible, [contenteditable='true']:visible, [role='textbox']:visible").last
    
    try:
        await chat_box.wait_for(state="visible", timeout=15000)
    except Exception as e:
        await page.screenshot(path="debug_error.png", full_page=True)
        raise Exception("Failed to find the chat input box! Check debug_error.png.")

    return page

async def send_prompt(page, prompt_text: str):
    """Envia a mensagem e aguarda a resposta estável na tela."""
    chat_box = page.locator("rich-textarea:visible, .ql-editor:visible, [contenteditable='true']:visible, [role='textbox']:visible").last
    response_locator = page.locator("message-content")
    
    initial_count = await response_locator.count()
    
    await chat_box.focus()
    await page.keyboard.insert_text(prompt_text)
    await page.keyboard.press("Enter")
    
    for _ in range(20):
        if await response_locator.count() > initial_count:
            break
        await page.wait_for_timeout(500)
    
    previous_text = ""
    stable_count = 0
    
    for _ in range(60): 
        current_text = await response_locator.last.inner_text()
        if current_text and current_text == previous_text:
            stable_count += 1
            if stable_count >= 3: 
                break
        else:
            stable_count = 0
        previous_text = current_text
        await page.wait_for_timeout(500)
        
    final_response = await response_locator.last.inner_text()
    
    try:
        cleaned = re.sub(r"```json|```", "", final_response).strip()
        response_parsed = json.loads(cleaned)
        return response_parsed.get('answer', final_response)
    except Exception:
        return final_response

async def teardown():
    """Fecha tudo adequadamente."""
    global _browser, _playwright_manager
    if _browser:
        await _browser.close()
    if _playwright_manager:
        await _playwright_manager.stop()