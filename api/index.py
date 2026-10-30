import io
import json
import os
import requests
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pypdf
import google.generativeai as genai

app = FastAPI(title="StudyMaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1565779785685278747/3bvQzWHwVV-XCDlZqiukl0TTziWND2_woOj17fkfgnvVZ6uJIojHsrq_4xIKZDaPBLfh")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
        return f"[File {filename} caricato]"

@app.get("/api/health")
def health(request: Request):
    notify_discord(get_client_ip(request), "Visita Sito")
    return {"status": "ok", "app": "StudyMaster"}

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
    notify_discord(get_client_ip(request), "Generazione Podcast con Gemini")
    if not GEMINI_API_KEY:
        return {"script": "⚠️ Errore: Configura la GEMINI_API_KEY su Vercel."}
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""Agisci come un tutor esperto, chiaro ed entusiasta. Crea una lezione vocale dettagliata, approfondita e strutturata (podcast) basata ESATTAMENTE su questo materiale di studio:\n\n{req.text}\n\nSpiega passo dopo passo come funziona l'argomento, fai esempi concreti tratti dal testo, spiega i concetti chiave in modo discorsivo ed esaustivo. Deve essere una spiegazione completa e di alto livello per aiutare lo studente."""
    response = model.generate_content(prompt)
    return {"script": response.text}

@app.post("/api/summary")
def generate_summary(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Riassunto con Gemini")
    if not GEMINI_API_KEY:
        return {"title": "Errore", "key_points": [], "summary": "GEMINI_API_KEY mancante."}
    
    try:
        json_model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type": "application/json"})
        prompt = f"""Analizza questo materiale di studio e crea un riassunto approfondito. Restituisci la risposta in formato JSON con queste chiavi esatte:
        {{
          "title": "Titolo chiaro dell'argomento",
          "key_points": ["Punto chiave 1 dettagliato", "Punto chiave 2 dettagliato", "Punto chiave 3 dettagliato", "Punto chiave 4 dettagliato"],
          "summary": "Una spiegazione discorsiva e dettagliata del testo"
        }}
        Materiale:\n{req.text}"""
        res = json_model.generate_content(prompt)
        return json.loads(res.text)
    except Exception as e:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return {
            "title": "Riassunto Studio",
            "key_points": ["Analisi dei concetti principali del documento."],
            "summary": model.generate_content(f"Riassumi questo testo:\n{req.text}").text
        }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest, request: Request):
    notify_discord(get_client_ip(request), f"Generazione Quiz Gemini (Difficoltà: {req.difficulty}, N: {req.length})")
    if not GEMINI_API_KEY:
        return {"questions": []}
    
    diff_str = {"1": "facile", "2": "medio", "3": "difficile"}.get(str(req.difficulty), "medio")
    
    try:
        json_model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type": "application/json"})
        prompt = f"""Crea esattamente {req.length} domande di verifica a scelta multipla basate RIGOROSAMENTE sul testo fornito sotto. Livello di difficoltà: {diff_str}.
        Restituisci la risposta in formato JSON (un array JSON puro) con questo schema esatto:
        [
          {{
            "id": 1,
            "question": "Testo della domanda...",
            "options": [
              {{"text": "Opzione errata", "correct": false}},
              {{"text": "Opzione corretta", "correct": true}},
              {{"text": "Altra opzione errata", "correct": false}}
            ],
            "explanation": "Spiegazione dettagliata della risposta corretta."
          }}
        ]
        Testo di riferimento:\n{req.text}"""
        
        res = json_model.generate_content(prompt)
        questions = json.loads(res.text)
        return {"questions": questions}
    except Exception as e:
        return {"questions": [{"id": 1, "question": "Errore nella generazione del quiz dall'IA.", "options": [{"text": "Riprova", "correct": true}], "explanation": str(e)}]}

@app.post("/api/map")
def generate_map(req: TextRequest, request: Request):
    notify_discord(get_client_ip(request), "Generazione Mappa con Gemini")
    if not GEMINI_API_KEY:
        return {"title": "Errore", "nodes": []}
    
    try:
        json_model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type": "application/json"})
        prompt = f"""Crea una struttura per una mappa concettuale basata su questo testo. Restituisci un JSON con questo schema esatto:
        {{
          "title": "Titolo della Mappa",
          "nodes": [
            {{
              "id": "main",
              "title": "TITOLO PRINCIPALE",
              "type": "root",
              "subnodes": [
                {{
                  "title": "Sotto-argomento 1",
                  "desc": "Descrizione del nodo",
                  "items": ["Concetto a", "Concetto b"]
                }}
              ]
            }}
          ]
        }}
        Testo di riferimento:\n{req.text}"""
        
        res = json_model.generate_content(prompt)
        return json.loads(res.text)
    except Exception as e:
        return {
            "title": "Mappa Concettuale",
            "nodes": [{
                "id": "main",
                "title": "ARGOMENTO",
                "type": "root",
                "subnodes": [{"title": "Errore", "desc": "Impossibile generare la mappa", "items": [str(e)]}]
            }]
        }
