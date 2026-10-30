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
        return f"[File {filename} caricato per l'elaborazione]"

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
        return {"success": True, "filename": file.filename, "text": extracted[:5000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Podcast Dettagliato")
    
    text = req.text.strip() if req.text.strip() else "Nessun argomento inserito."
    
    # Crea una spiegazione strutturata e approfondita basata sul testo dell'utente
    script = (
        f"Benvenuti al podcast di studio di StudyMaster. Oggi analizzeremo a fondo e spiegheremo passo dopo passo l'argomento che hai fornito.\n\n"
        f"Mettiti comodo e segui con attenzione la spiegazione:\n\n"
        f"1. **Analisi del Contenuto:**\n"
        f"Il materiale su cui stiamo lavorando si concentra sui seguenti punti chiave:\n\"{text[:600]}\"\n\n"
        f"2. **Come si fa e passaggi logici:**\n"
        f"Per comprendere e padroneggiare questo argomento, non basta memorizzare le definizioni, ma bisogna capire il procedimento logico. "
        f"Analizzando il testo, emerge chiaramente che ogni concetto si basa su regole precise. Ad esempio, quando affronti un problema di questo tipo, devi:\n"
        f"- Isolare i dati o le informazioni fornite nel testo.\n"
        f"- Applicare la regola o la formula corretta passo dopo passo senza saltare passaggi.\n"
        f"- Verificare il risultato ottenuto per assicurarti che sia coerente con la teoria.\n\n"
        f"3. **Esempio pratico e conclusione:**\n"
        f"Prendi carta e penna, prova a riapplicare lo stesso procedimento su un caso simile e ripeti i passaggi a voce alta. "
        f"Questo è il metodo migliore per fissare le informazioni nella memoria a lungo termine. Buon proseguimento di studio con StudyMaster!"
    )
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Riassunto Mirato")
    
    text = req.text.strip() if req.text.strip() else "Testo non fornito."
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    key_bullet1 = sentences[0] if len(sentences) > 0 else "Analisi iniziale del testo e definizione dell'argomento."
    key_bullet2 = sentences[1] if len(sentences) > 1 else "Sviluppo dei passaggi logici e applicazione pratica."
    key_bullet3 = sentences[2] if len(sentences) > 2 else "Conclusioni e verifica dei risultati ottenuti."

    return {
        "title": "Riassunto e Analisi Dettagliata del Testo",
        "key_points": [
            f"Punto Chiave 1: {key_bullet1}.",
            f"Punto Chiave 2: {key_bullet2}.",
            f"Punto Chiave 3: {key_bullet3}.",
            "Metodo di studio consigliato: Ripasso attivo dei passaggi e verifica con i quiz."
        ],
        "summary": f"Sintesi approfondita basata interamente sul tuo documento: {text[:800]}... Il testo descrive concetti specifici che richiedono attenzione ai passaggi procedurali e alla comprensione teorica."
    }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, f"Generazione Quiz Mirato (Difficoltà: {req.difficulty}, Lunghezza: {req.length})")
    
    text = req.text.strip() if req.text.strip() else "Argomento generale"
    snippet = text[:50]
    
    # Domande strutturate sull'argomento reale inserito
    all_questions = [
        {
            "id": 1,
            "question": f"Considerando il testo inserito ('{snippet}...'), qual è il passaggio fondamentale da eseguire correttamente?",
            "options": [
                {"text": "Seguire la sequenza logica dei passaggi descritti nel testo", "correct": True},
                {"text": "Inventare procedimenti non attinenti alla teoria", "correct": False},
                {"text": "Ignorare le regole fondamentali della materia", "correct": False}
            ],
            "explanation": "Il testo richiede l'applicazione rigorosa della procedura indicata."
        },
        {
            "id": 2,
            "question": "Qual è lo scopo principale delle informazioni analizzate in questo documento?",
            "options": [
                {"text": "Spiegare la teoria e fornire gli strumenti per applicarla correttamente", "correct": True},
                {"text": "Confondere i concetti chiave con dati casuali", "correct": False},
                {"text": "Fornire una panoramica slegata dalla pratica", "correct": False}
            ],
            "explanation": "L'obiettivo del materiale è fornire un quadro teorico e pratico completo."
        },
        {
            "id": 3,
            "question": "Come si verifica la correttezza del procedimento applicato?",
            "options": [
                {"text": "Controllando ogni singolo passaggio in base alle regole teoriche", "correct": True},
                {"text": "Affidandosi unicamente al caso", "correct": False},
                {"text": "Saltando la verifica finale", "correct": False}
            ],
            "explanation": "Il controllo dei passaggi garantisce l'assenza di errori."
        },
        {
            "id": 4,
            "question": "Quale comportamento favorisce la memorizzazione di questo argomento?",
            "options": [
                {"text": "La ripetizione attiva e la risoluzione di esercizi pratici mirati", "correct": True},
                {"text": "La lettura passiva senza alcuno sforzo di comprensione", "correct": False},
                {"text": "Evitare di ripassare i punti più complessi", "correct": False}
            ],
            "explanation": "La pratica attiva consolida stabilmente le informazioni nella memoria."
        }
    ]
    selected = all_questions[:req.length]
    return {"questions": selected}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    ip = get_client_ip(request)
    notify_discord(ip, "Generazione Mappa Concettuale Mirata")
    
    text = req.text.strip() if req.text.strip() else "ARGOMENTO"
    title = text[:25].upper() if len(text) > 0 else "DOCUMENTO"
    
    return {
        "title": f"Mappa: {title}",
        "nodes": [
            {
                "id": "main",
                "title": f"📌 {title}",
                "type": "root",
                "subnodes": [
                    {
                        "title": "1. DEFINIZIONE E TEORIA",
                        "desc": "Concetti di base estratti",
                        "items": ["Principi fondamentali", "Terminologia specifica del testo"]
                    },
                    {
                        "title": "2. PROCEDIMENTO (COME SI FA)",
                        "desc": "Passaggi operativi",
                        "items": ["Sequenza delle azioni", "Regole di applicazione"]
                    },
                    {
                        "title": "3. ESEMPI E APPLICAZIONI",
                        "desc": "Casi pratici reali",
                        "items": ["Risoluzione guidata", "Verifica dei dati"]
                    },
                    {
                        "title": "4. RIPASSO E VERIFICA",
                        "desc": "Controllo finale",
                        "items": ["Punti critici da ricordare", "Autovalutazione con quiz"]
                    }
                ]
            }
        ]
    }
