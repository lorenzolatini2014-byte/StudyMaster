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
        return {"success": True, "filename": file.filename, "text": extracted[:4000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Podcast Mirato")
    
    content = req.text.strip() if req.text.strip() else "Nessun testo fornito."
    snippet = content[:800] # Prende una parte consistente del testo inserito
    
    script = (
        f"Benvenuti al podcast di studio di StudyMaster. Oggi analizzeremo e spiegheremo in dettaglio il materiale che hai caricato.\n\n"
        f"Entriamo subito nel vivo dell'argomento:\n{snippet}\n\n"
        f"Per comprendere a fondo questo testo, è importante focalizzarsi sui punti chiave appena esposti, collegandoli tra loro in modo logico. "
        f"Rileggi con attenzione questi passaggi, pensa agli esempi pratici e ripeti i concetti a voce alta per fissarli al meglio nella memoria. "
        f"Buono studio da StudyMaster!"
    )
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Riassunto Mirato")
    
    content = req.text.strip() if req.text.strip() else "Testo di studio generale."
    # Estrae parole o prime righe per dare un senso specifico
    words = content.split()
    preview = " ".join(words[:30]) + ("..." if len(words) > 30 else "")
    
    return {
        "title": "Riassunto Mirato del Documento",
        "key_points": [
            f"Tema principale identificato: {preview}",
            "Analisi approfondita dei concetti chiave presenti nel testo.",
            "Definizioni e passaggi logici fondamentali estratti dal materiale.",
            "Conclusioni e sintesi pratica per il ripasso."
        ],
        "summary": f"Ecco la sintesi strutturata basata direttamente sul materiale inserito: {content[:400]}..."
    }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, f"Generazione Quiz Mirato (Difficoltà: {req.difficulty}, Lunghezza: {req.length})")
    
    content = req.text.strip() if req.text.strip() else "Argomento di studio"
    snippet = content[:60]
    
    # Domande mirate basate sul testo inserito
    all_questions = [
        {
            "id": 1,
            "question": f"In base al testo inserito riguardo a '{snippet}...', qual è il concetto fondamentale trattato?",
            "options": [
                {"text": "L'analisi dettagliata dei principi e delle definizioni contenute nel testo", "correct": True},
                {"text": "Un argomento completamente slegato e differente", "correct": False},
                {"text": "Informazioni casuali non presenti nel documento", "correct": False}
            ],
            "explanation": "Il testo analizzato si concentra specificamente sui principi descritti nella documentazione."
        },
        {
            "id": 2,
            "question": "Quale conclusione logica si deduce dai dati e dalle informazioni fornite?",
            "options": [
                {"text": "I concetti esposti richiedono attenzione ai dettagli e ai passaggi chiave", "correct": True},
                {"text": "Le informazioni non hanno alcuna attinenza logica", "correct": False},
                {"text": "Si tratta di dati puramente casuali", "correct": False}
            ],
            "explanation": "La struttura del materiale richiede un'analisi logica e sequenziale dei dati."
        },
        {
            "id": 3,
            "question": "Come possono essere applicate correttamente le informazioni di questo materiale?",
            "options": [
                {"text": "Attraverso lo studio mirato dei punti chiave e la verifica pratica", "correct": True},
                {"text": "Ignorando completamente la teoria", "correct": False},
                {"text": "Memorizzando senza comprendere il contesto", "correct": False}
            ],
            "explanation": "Unire teoria e riscontro pratico garantisce la comprensione del testo."
        },
        {
            "id": 4,
            "question": "Qual è il metodo migliore per memorizzare i concetti di questo argomento?",
            "options": [
                {"text": "Schematizzare i punti principali e testarsi con i quiz di verifica", "correct": True},
                {"text": "Leggere distrattamente una sola volta", "correct": False},
                {"text": "Evitare di ripetere i concetti complessi", "correct": False}
            ],
            "explanation": "L'uso di mappe e test attivi consolida la memorizzazione a lungo termine."
        }
    ]
    selected = all_questions[:req.length]
    return {"questions": selected}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Mappa Concettuale Mirata")
    
    content = req.text.strip() if req.text.strip() else "ARGOMENTO DI STUDIO"
    title_snippet = content[:25].upper() if len(content) > 0 else "DOCUMENTO"
    
    return {
        "title": f"Mappa: {title_snippet}...",
        "nodes": [
            {
                "id": "main",
                "title": f"📌 {title_snippet}",
                "type": "root",
                "subnodes": [
                    {
                        "title": "1. ANALISI DEL TESTO",
                        "desc": "Concetti estratti dal materiale",
                        "items": ["Definizioni principali", "Terminologia specifica"]
                    },
                    {
                        "title": "2. PUNTI CRUCIALI",
                        "desc": "Elementi centrali della spiegazione",
                        "items": ["Relazioni logiche", "Dati e informazioni rilevanti"]
                    },
                    {
                        "title": "3. APPLICAZIONE",
                        "desc": "Contesto pratico",
                        "items": ["Esempi dal documento", "Risoluzione dei quesiti"]
                    },
                    {
                        "title": "4. VERIFICA",
                        "desc": "Controllo della comprensione",
                        "items": ["Ripasso attivo", "Autovalutazione"]
                    }
                ]
            }
        ]
    }
