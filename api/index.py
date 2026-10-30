import io
import json
import os
import requests
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pypdf

app = FastAPI(title="StudyMaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Il tuo Webhook di Discord inserito correttamente
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1565779785685278747/3bvQzWHwVV-XCDlZqiukl0TTziWND2_woOj17fkfgnvVZ6uJIojHsrq_4xIKZDaPBLfh"

class QuizRequest(BaseModel):
    text: str
    difficulty: str = "medio"
    length: int = 3

class TextRequest(BaseModel):
    text: str

def notify_discord(ip: str, action: str):
    """Invia una notifica su Discord con IP, Data e Azione"""
    if not DISCORD_WEBHOOK_URL or "api/webhooks" not in DISCORD_WEBHOOK_URL:
        return
    
    now = datetime.now().strftime("%d/%m/%Y alle %H:%M:%S")
    message = {
        "content": f"🚨 **Nuovo accesso / attività su StudyMaster!**\n📅 **Data:** `{now}`\n🌐 **Indirizzo IP:** `{ip}`\n⚡ **Azione:** `{action}`"
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=3)
    except Exception:
        pass

def get_client_ip(request: Request) -> str:
    """Ricava l'IP reale del visitatore anche dietro i proxy di Vercel"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "IP Sconosciuto"

def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.split('.')[-1].lower()
    if ext == "pdf":
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "".join([page.extract_text() or "" for page in reader.pages])
    elif ext in ["txt", "md"]:
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        return f"[File {filename} caricato per l'elaborazione IA]"

@app.get("/api/health")
def health(request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Visita / Apertura Sito")
    return {"status": "ok", "app": "StudyMaster"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    ip = get_client_ip(request) if request else "IP Sconosciuto"
    notify_discord(ip, f"Caricamento file: {file.filename}")
    try:
        contents = await file.read()
        extracted = extract_text(contents, file.filename)
        return {"success": True, "filename": file.filename, "text": extracted[:3000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Podcast")
    src = req.text.strip() if req.text.strip() else "Tabelline e concetti di aritmetica di base."
    script = (
        "Benvenuti a questa lezione speciale di StudyMaster dedicata alla memorizzazione e alla comprensione profonda delle tabelline! "
        "Spesso le tabelline vengono viste come un esercizio faticoso da imparare a memoria, ma in realtà racchiudono una straordinaria armonia di schemi e regole matematiche. "
        "Vediamo insieme i concetti chiave legati al materiale caricato: " + src[:200] + ".\n\n"
        "Per prima cosa, ricordiamo che la moltiplicazione non è altro che una scorciatoia per un'addizione ripetuta. "
        "Prendiamo la tabellina del due: raddoppiare significa semplicemente sommare un numero a se stesso. "
        "La tabellina del cinque è una delle più semplici da memorizzare, perché i risultati terminano sempre e solo con la cifra zero oppure cinque.\n\n"
        "Un piccolo segreto riguarda la temuta tabellina del nove: se osservi bene la somma delle cifre di ogni risultato, noterai che fa sempre nove! "
        "Ad esempio, nove per due fa diciotto, e uno più otto fa esattamente nove. Nove per tre fa ventisette, e due più sette fa ancora nove.\n\n"
        "Infine, grazie alla proprietà commutativa, ricordati che due per tre ha lo stesso identico valore di tre per due. Questo ti permette di dimezzare le cose da memorizzare! "
        "Ripassa questi concetti con calma, ascolta la spiegazione ogni volta che ne hai bisogno e mettiti alla prova con i nostri quiz di verifica per consolidare la tua preparazione. Buon lavoro e buono studio con StudyMaster!"
    )
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Riassunto")
    src = req.text.strip() if req.text.strip() else "Tabelline e matematica di base."
    return {
        "title": "Riassunto: Guida e Trucchi sulle Tabelline",
        "key_points": [
            "La moltiplicazione è un'addizione ripetuta.",
            "Proprietà commutativa: l'ordine dei fattori non cambia il prodotto (es. 3x4 = 4x3).",
            "Regola del 5: i risultati terminano sempre con
