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

# Inserisci qui la chiave OpenRouter che hai appena generato
OPENROUTER_API_KEY = "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"

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
    message = {"content": f"🚨 **StudyMaster Attività:**\n📅 `{now}`\n🌐 IP: `{ip}`\n⚡ Azione: `{action}`"}
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

def call_real_ai(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://study-master.vercel.app",
        "X-Title": "StudyMaster"
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        res_data = response.json()
        if "choices" in res_data and len(res_data["choices"]) > 0:
            return res_data["choices"][0]["message"]["content"]
        else:
            return f"Risposta elaborata dal sistema basata sul testo fornito."
    except Exception as e:
        return f"Errore di connessione all'IA: {str(e)}"

@app.get("/api/health")
def health(request: Request):
    notify_discord(get_client_ip(request), "Visita Sito")
    return {"status": "ok", "app": "StudyMaster Real AI"}

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
    notify_discord(get_client_ip(request), "Generazione Podcast IA")
    user_input = req.text.strip() if req.text.strip() else "Concetti generali"
    prompt = f"Agisci come un tutor esperto. Crea una spiegazione dettagliata e discorsiva sotto forma di lezione audio/podcast in italiano basata su questo materiale:\n\n{user_input}"
    script = call_real_ai(prompt)
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Riassunto IA")
    user_input = req.text.strip() if req.text.strip() else "Argomento"
    prompt = f"Analizza questo testo e crea un riassunto approfondito. Restituisci SOLO un oggetto JSON valido (senza markdown) con esattamente queste chiavi: {{\"title\": \"Titolo chiaro\", \"key_points\": [\"Punto 1\", \"Punto 2\", \"Punto 3\", \"Punto 4\"], \"summary\": \"Spiegazione dettagliata\"}}\n\nTesto:\n{user_input}"
    res_text = call_real_ai(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        start = clean_json.index("{")
        end = clean_json.rindex("}") + 1
        return json.loads(clean_json[start:end])
    except:
        return {
            "title": "Riassunto di Studio",
            "key_points": ["Analisi dei concetti principali", "Estrazione dei dati chiave"],
            "summary": res_text
        }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Quiz IA")
    user_input = req.text.strip() if req.text.strip() else "Quiz generale"
    prompt = f"Crea esattamente {req.length} domande a scelta multipla basate su questo testo: '{user_input}'. Restituisci SOLO un array JSON puro (senza markdown) con questo schema esatto:\n[{{\"id\": 1, \"question\": \"Domanda...\", \"options\": [{{\"text\": \"Errata\", \"correct\": false}}, {{\"text\": \"Corretta\", \"correct\": true}}], \"explanation\": \"Spiegazione\"}}]"
    res_text = call_real_ai(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        start = clean_json.index("[")
        end = clean_json.rindex("]") + 1
        return {"questions": json.loads(clean_json[start:end])}
    except:
        return {"questions": [{"id": 1, "question": "Verifica di comprensione del testo.", "options": [{"text": "Risposta corretta basata sul materiale", "correct": True}], "explanation": res_text}]}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Mappa IA")
    user_input = req.text.strip() if req.text.strip() else "Mappa"
    prompt = f"Crea una struttura per una mappa concettuale basata su: '{user_input}'. Restituisci SOLO un JSON puro (senza markdown) con questo schema:\n{{\"title\": \"Titolo\", \"nodes\": [{{\"id\": \"main\", \"title\": \"PRINCIPALE\", \"type\": \"root\", \"subnodes\": [{{\"title\": \"Sotto 1\", \"desc\": \"Desc\", \"items\": [\"a\", \"b\"]}}]}}]}}"
    res_text = call_real_ai(prompt)
    
    try:
        clean_json = res_text.replace("```json", "").replace("```", "").strip()
        start = clean_json.index("{")
        end = clean_json.rindex("}") + 1
        return json.loads(clean_json[start:end])
    except:
        return {
            "title": "Mappa Concettuale",
            "nodes": [{
                "id": "main",
                "title": "ARGOMENTO PRINCIPALE",
                "type": "root",
                "subnodes": [{"title": "Analisi", "desc": "Contenuto generato", "items": [res_text[:100]]}]
            }]
        }
