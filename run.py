import uvicorn
import asyncio
import sys

# 1. Primeiro definimos a regra do Windows para suportar o Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 2. Só DEPOIS iniciamos o Uvicorn via código
if __name__ == "__main__":
    print("Iniciando servidor customizado com suporte a subprocessos...")
    uvicorn.run("routes.main:app", host="127.0.0.1", port=8000, reload=False)