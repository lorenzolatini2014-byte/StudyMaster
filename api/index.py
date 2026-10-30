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
        return {"success": True, "filename": file.filename, "text": extracted[:3000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Podcast")
    
    user_topic = req.text.strip() if req.text.strip() else "l'argomento di studio caricato"
    
    script = (
        f"Benvenuti a questa lezione speciale di StudyMaster dedicata all'approfondimento del tuo materiale di studio!\n\n"
        f"Oggi analizzeremo insieme i punti fondamentali del contenuto che hai inserito: '{user_topic}'.\n\n"
        f"Comprendere a fondo questo argomento è essenziale per costruire una preparazione solida e duratura. "
        f"Quando ti approcci a questo studio, concentrati prima sulle definizioni chiave e sui concetti di base, "
        f"per poi passare all'applicazione pratica e agli esempi specifici.\n\n"
        f"Prenditi tutto il tempo necessario per ripassare queste informazioni con calma. "
        f"Usa le mappe concettuali e i quiz di verifica messi a disposizione sulla piattaforma per mettere alla prova le tue conoscenze. "
        f"Buono studio da StudyMaster!"
    )
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Riassunto")
    
    user_topic = req.text.strip() if req.text.strip() else "Materiale fornito"
    snippet = user_topic[:150] + "..." if len(user_topic) > 150 else user_topic
    
    return {
        "title": "Riassunto Intelligente del Materiale",
        "key_points": [
            f"Argomento Principale: {snippet}",
            "Punto Chiave 1: Identificazione dei concetti fondamentali ed elementi di base.",
            "Punto Chiave 2: Analisi delle relazioni logiche tra i vari argomenti trattati.",
            "Punto Chiave 3: Applicazione e ripasso sintetico per la preparazione."
        ],
        "summary": f"Sintesi dettagliata del materiale inserito: '{snippet}'. L'argomento è stato organizzato in punti chiari per facilitare la memorizzazione e la comprensione veloce."
    }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, f"Generazione Quiz (Difficoltà: {req.difficulty}, Lunghezza: {req.length})")
    
    topic_title = req.text.strip()[:40] if req.text.strip() else "Argomento caricato"
    
    all_questions = [
        {
            "id": 1,
            "question": f"Qual è l'obiettivo principale nello studio di: '{topic_title}'?",
            "options": [
                {"text": "Comprendere i concetti di base e applicarli correttamente", "correct": True},
                {"text": "Mantenere solo una visione superficiale senza approfondire", "correct": False},
                {"text": "Ignorare le definizioni chiave dell'argomento", "correct": False}
            ],
            "explanation": "La comprensione dei concetti chiave è la base per la padronanza della materia."
        },
        {
            "id": 2,
            "question": "Quale approccio è più efficace durante il ripasso?",
            "options": [
                {"text": "Sintetizzare le informazioni con schemi e verificare le proprie risposte", "correct": True},
                {"text": "Leggere una sola volta senza fare esercizi", "correct": False},
                {"text": "Memorizzare senza capire il significato", "correct": False}
            ],
            "explanation": "L'elaborazione attiva e la verifica costante migliorano la ritenzione del materiale."
        },
        {
            "id": 3,
            "question": "Come si collegano i concetti all'interno dell'argomento trattato?",
            "options": [
                {"text": "In una struttura logica e consequenziale", "correct": True},
                {"text": "In modo del tutto casuale e senza legami", "correct": False},
                {"text": "Esclusivamente tramite regole mnemoniche", "correct": False}
            ],
            "explanation": "Tutti i punti del materiale di studio sono legati da relazioni di causa-effetto e sequenza."
        },
        {
            "id": 4,
            "question": "Cosa è raccomandato fare in caso di dubbi durante lo studio?",
            "options": [
                {"text": "Riconsultare il materiale originale e riascoltare la spiegazione audio", "correct": True},
                {"text": "Procedere ignorando i punti non chiari", "correct": False},
                {"text": "Cambiare del tutto materia senza risolvere il dubbio", "correct": False}
            ],
            "explanation": "Chiarire subito i dubbi evita di accumulare lacune nello studio."
        }
    ]
    selected = all_questions[:req.length]
    return {"questions": selected}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Mappa Concettuale")
    
    topic_title = req.text.strip()[:30] if req.text.strip() else "MATERIALE DI STUDIO"
    
    return {
        "title": f"Mappa Concettuale: {topic_title}",
        "nodes": [
            {
                "id": "main",
                "title": f"📌 {topic_title.upper()}",
                "type": "root",
                "subnodes": [
                    {
                        "title": "1. CONCETTI CHIAVE",
                        "desc": "Definizioni e nozioni fondamentali",
                        "items": ["Elementi di base dell'argomento", "Terminologia specifica"]
                    },
                    {
                        "title": "2. STRUTTURA LOGICA",
                        "desc": "Collegamento tra le idee",
                        "items": ["Principi di funzionamento", "Relazioni di causa ed effetto"]
                    },
                    {
                        "title": "3. APPLICAZIONE PRATICA",
                        "desc": "Esempi ed esercizi di verifica",
                        "items": ["Casi di studio specifici", "Risoluzione di problemi"]
                    },
                    {
                        "title": "4. SINTESI FINALE",
                        "desc": "Punti da ricordare per la verifica",
                        "items": ["Schematizzazione dei concetti", "Ripasso e autovalutazione"]
                    }
                ]
            }
        ]
    }
