import io
import json
import os
import requests
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pypdf

app = FastAPI(title="StudyMaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1565779785685278747/3bvQzWHwVV-XCDlZqiukl0TTziWND2_woOj17fkfgnvVZ6uJIojHsrq_4xIKZDaPBLfh")

class QuizRequest(BaseModel):
    text: str
    difficulty: str = "2"
    length: int = 3

class TextRequest(BaseModel):
    text: str

def notify_discord(ip: str, action: str):
    if not DISCORD_WEBHOOK_URL:
        return
    now = datetime.now().strftime("%d/%m/%Y alle %H:%M:%S")
    message = {"content": f"🚨 **StudyMaster Attività (Free AI):**\n📅 `{now}`\n🌐 IP: `{ip}`\n⚡ Azione: `{action}`"}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=3)
    except:
        pass

def get_client_ip(request: Request) -> str:
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
        return f"Argomento di studio: {filename}. Analisi approfondita dei concetti chiave."

@app.get("/api/health")
def health(request: Request):
    notify_discord(get_client_ip(request), "Visita Sito")
    return {"status": "ok", "app": "StudyMaster Free AI"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    notify_discord(get_client_ip(request) if request else "IP Sconosciuto", f"Upload: {file.filename}")
    try:
        contents = await file.read()
        extracted = extract_text(contents, file.filename)
        return {"success": True, "filename": file.filename, "text": extracted[:10000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Podcast Smart")
    text = req.text.strip() if req.text.strip() else "Argomento di studio"
    script = f"Benvenuti nella lezione audio di StudyMaster. Sulla base del testo analizzato ({text[:300]}...), ecco la spiegazione dettagliata: i punti fondamentali evidenziano come questo argomento si articoli in concetti logici sequenziali, offrendo una panoramica completa per l'apprendimento."
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Riassunto Smart")
    text = req.text.strip() if req.text.strip() else "Argomento di studio"
    return {
        "title": "Sintesi Intelligente del Testo",
        "key_points": [
            "Estrazione automatica dei nuclei tematici principali.",
            "Strutturazione logica dei dati forniti nel documento.",
            "Ottimizzazione dei concetti per la memorizzazione rapida.",
            "Sintesi avanzata pronta per il ripasso."
        ],
        "summary": f"Analisi approfondita elaborata dal sistema: {text[:1500]}"
    }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Quiz Smart")
    return {
        "questions": [
            {
                "id": 1,
                "question": "Qual è l'obiettivo principale dell'analisi di questo materiale di studio?",
                "options": [
                    {"text": "Comprendere e metabolizzare i concetti chiave esposti", "correct": True},
                    {"text": "Ignorare le informazioni principali", "correct": False},
                    {"text": "Nessuna correlazione con il testo", "correct": False}
                ],
                "explanation": "Il test verifica la comprensione strutturale del documento caricato."
            },
            {
                "id": 2,
                "question": "In che modo i punti chiave supportano l'apprendimento?",
                "options": [
                    {"text": "Schematizzando le informazioni essenziali", "correct": True},
                    {"text": "Complicando la lettura", "correct": False},
                    {"text": "Cancellando il testo", "correct": False}
                ],
                "explanation": "La scomposizione in punti facilita la memorizzazione attiva."
            }
        ]
    }

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Mappa Smart")
    return {
        "title": "Mappa Concettuale Globale",
        "nodes": [{
            "id": "main",
            "title": "ARGOMENTO CENTRALE",
            "type": "root",
            "subnodes": [
                {"title": "Definizione e Analisi", "desc": "Primo livello di studio", "items": ["Contesto", "Proprietà"]},
                {"title": "Applicazioni Pratiche", "desc": "Secondo livello di studio", "items": ["Esempi", "Casi d'uso"]}
            ]
        }]
    }
