import io
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pypdf

app = FastAPI(title="StudyMaster API")

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.split('.')[-1].lower()
    if ext == "pdf":
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "".join([page.extract_text() or "" for page in reader.pages])
    elif ext in ["txt", "md"]:
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        return f"[File {filename} caricato correttamente per l'elaborazione IA]"

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "StudyMaster"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        extracted = extract_text(contents, file.filename)
        return {"success": True, "filename": file.filename, "text": extracted[:3000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/podcast")
def generate_podcast(req: TextRequest):
    src = req.text.strip() if req.text.strip() else "Argomento di studio generale."
    script = (
        f"Benvenuti a questa sessione di studio audio di StudyMaster!\n\n"
        f"Oggi esaminiamo i concetti fondamentali. Ecco la sintesi parlata:\n\n"
        f"Punto 1: {src[:120]}...\n\n"
        f"Punto 2: Approfondiamo gli elementi chiave ed i termini principali da memorizzare.\n\n"
        f"Punto 3: Ricorda di ripassare la sequenza logica dei passaggi prima dell'interrogazione!"
    )
    return {"script": script}

@app.post("/api/summary")
def generate_summary(req: TextRequest):
    src = req.text.strip() if req.text.strip() else "Argomento non specificato."
    return {
        "title": "Riassunto di Studio",
        "key_points": [
            "Definizione principale ed elemento base dell'argomento.",
            "Procedimento e concetti chiave da tenere a mente.",
            "Esempi pratici e collegamenti importanti."
        ],
        "summary": f"Sintesi rapida del contenuto fornito: {src[:250]}..."
    }

@app.post("/api/quiz")
def generate_quiz(req: TextRequest):
    return {
        "questions": [
            {
                "id": 1,
                "question": "Qual è il concetto fondamentale descritto nel testo?",
                "options": [
                    "A) La definizione e i principi di base",
                    "B) Una teoria secondaria non verificata",
                    "C) Un esempio isolato"
                ],
                "correct": "A",
                "explanation": "La risposta A è corretta perché sintetizza il tema principale dell'argomento."
            },
            {
                "id": 2,
                "question": "Quale elemento è indispensabile per la preparazione della verifica?",
                "options": [
                    "A) Ignorare i termini tecnici",
                    "B) Memorizzare la sequenza logica e le parole chiave",
                    "C) Leggere una sola volta"
                ],
                "correct": "B",
                "explanation": "La risposta B permette di fissare i concetti chiave in modo efficace."
            }
        ]
    }

@app.post("/api/map")
def generate_map(req: TextRequest):
    return {
        "nodes": [
            {"title": "Argomento Principale", "desc": "Idea centrale del capitolo"},
            {"title": "Concetto 1", "desc": "Definizioni e termini chiave"},
            {"title": "Concetto 2", "desc": "Processi e fasi operative"},
            {"title": "Conclusione", "desc": "Sintesi per il ripasso finale"}
        ]
    }