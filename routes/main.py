from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.gemini_bot import create_instance, send_prompt, teardown

active_pages = {}
page_locks = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando Instância 1...")
    active_pages["browser_1"] = await create_instance()
    page_locks["browser_1"] = asyncio.Lock()
    
    print("Iniciando Instância 2...")
    active_pages["browser_2"] = await create_instance()
    page_locks["browser_2"] = asyncio.Lock()
    
    print("🚀 Servidor FastAPI pronto e conectado ao Playwright!")
    yield
    
    print("Desligando instâncias do Playwright...")
    await teardown()

app = FastAPI(lifespan=lifespan)

class PromptRequest(BaseModel):
    prompt: str
    instance_id: str

@app.post("/generate")
async def generate_response(req: PromptRequest):
    if req.instance_id not in active_pages:
        raise HTTPException(status_code=400, detail="Use browser_1 ou browser_2")
        
    async with page_locks[req.instance_id]:
        try:
            resposta = await send_prompt(
                page=active_pages[req.instance_id], 
                prompt_text=req.prompt
            )
            return {"instance_id": req.instance_id, "response": resposta}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro na extração: {str(e)}")