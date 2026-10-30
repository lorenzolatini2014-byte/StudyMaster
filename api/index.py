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

# Chiave Groq inserita direttamente per azzerare qualsiasi errore di configurazione su Vercel
GROQ_API_KEY = "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"

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
    message = {"content": f"🚨 **StudyMaster Attività (Groq Diretto):**\n📅 `{now}`\n🌐 IP: `{ip}`\n⚡ Azione: `{action}`"}
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
        return f"Argomento di studio: {filename}. Spiega approfonditamente i concetti chiave legati a questo titolo."

def call_groq_api(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        res_data = response.json()
        if "choices" in res_data:
            return res_data["choices"][0]["message"]["content"]
        else:
            return f"Errore Groq: {json.dumps(res_data)}"
    except Exception as e:
        return f"Errore di connessione a Groq: {str(e)}"

@app.get("/api/health")
def health(request: Request):
    notify_discord(get_client_ip(request), "Visita Sito")
    return {"status": "ok", "app": "StudyMaster Groq Diretto"}

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
    notify_discord(get_client_ip(request), "Generazione Podcast con Groq")
    user_input = req.text.strip() if req.text.strip() else "Concetti generali di studio"
    
    prompt = f"Agisci come un tutor esperto, chiaro ed entusiasta. Crea una lezione vocale dettagliata, approfondita e strutturata sotto forma di podcast basata su questo materiale:\n\n{user_input}\n\nSpiega passo dopo passo come funziona l'argomento, fai esempi concreti e spiega i concetti chiave in modo discorsivo ed esaustivo."
    script = call_groq_api(prompt)
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Riassunto con Groq")
    user_input = req.text.strip() if req.text.strip() else "Argomento di studio"
    
    prompt = f"Analizza questo testo/argomento e crea un riassunto approfondito. Restituisci SOLO un oggetto JSON valido (senza blocchi di codice markdown o altri caratteri) con queste chiavi esatte:\n{{\"title\": \"Titolo chiaro\", \"key_points\": [\"Punto 1\", \"Punto 2\", \"Punto 3\", \"Punto 4\"], \"summary\": \"Spiegazione dettagliata\"}}\n\nTesto:\n{user_input}"
    res_text = call_groq_api(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {
            "title": "Riassunto Studio",
            "key_points": ["Analisi dei concetti principali del documento."],
            "summary": res_text
        }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    notify_discord(get_client_ip(request), f"Generazione Quiz Groq")
    user_input = req.text.strip() if req.text.strip() else "Argomento generale"
    
    prompt = f"Crea esattamente {req.length} domande di verifica a scelta multipla basate su questo argomento: '{user_input}'. Restituisci SOLO un array JSON puro (senza markdown) con questo schema:\n[{{\"id\": 1, \"question\": \"Domanda...\", \"options\": [{{\"text\": \"Errata\", \"correct\": false}}, {{\"text\": \"Corretta\", \"correct\": true}}], \"explanation\": \"Spiegazione\"}}]"
    res_text = call_groq_api(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        return {"questions": json.loads(clean_json)}
    except:
        return {"questions": [{"id": 1, "question": "Errore nella generazione del quiz.", "options": [{"text": "Riprova", "correct": True}], "explanation": res_text}]}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Mappa con Groq")
    user_input = req.text.strip() if req.text.strip() else "ARGOMENTO"
    
    prompt = f"Crea una struttura per una mappa concettuale basata su: '{user_input}'. Restituisci SOLO un JSON puro (senza markdown) con questo schema:\n{{\"title\": \"Titolo\", \"nodes\": [{{\"id\": \"main\", \"title\": \"PRINCIPALE\", \"type\": \"root\", \"subnodes\": [{{\"title\": \"Sotto 1\", \"desc\": \"Desc\", \"items\": [\"a\", \"b\"]}}]}}]}}"
    res_text = call_groq_api(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {
            "title": "Mappa Concettuale",
            "nodes": [{
                "id": "main",
                "title": "ARGOMENTO",
                "type": "root",
                "subnodes": [{"title": "Errore", "desc": "Impossibile generare", "items": [res_text]}]
            }]
        }
