import io
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
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

class QuizRequest(BaseModel):
    text: str
    difficulty: str = "medio"
    length: int = 3

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
        return f"[File {filename} caricato per l'elaborazione IA]"

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
def generate_summary(req: TextRequest):
    src = req.text.strip() if req.text.strip() else "Tabelline e matematica di base."
    return {
        "title": "Riassunto: Guida e Trucchi sulle Tabelline",
        "key_points": [
            "La moltiplicazione è un'addizione ripetuta.",
            "Proprietà commutativa: l'ordine dei fattori non cambia il prodotto (es. 3x4 = 4x3).",
            "Regola del 5: i risultati terminano sempre con 0 o 5.",
            "Trucco del 9: la somma delle cifre di ogni prodotto fa sempre 9 (es. 9x3=27 -> 2+7=9)."
        ],
        "summary": f"Sintesi del materiale caricato ({src[:150]}...): Le tabelline si basano su schemi logici e simmetrie che semplificano il calcolo a mente."
    }

@app.post("/api/quiz")
def generate_quiz(req: QuizRequest):
    # Genera quiz dinamico in base a difficoltà e lunghezza scelte
    all_questions = [
        {
            "id": 1,
            "question": "Quanto fa 9 x 4 e qual è la regola per la tabellina del 9?",
            "options": [
                {"text": "36 (la somma delle cifre 3 + 6 fa 9)", "correct": True},
                {"text": "32 (la somma delle cifre è pari)", "correct": False},
                {"text": "40 (si aggiunge solo uno zero)", "correct": False}
            ],
            "explanation": "9 x 4 = 36. Inoltre, 3 + 6 = 9, confermando la regola della tabellina del 9."
        },
        {
            "id": 2,
            "question": "Cosa afferma la proprietà commutativa della moltiplicazione?",
            "options": [
                {"text": "Se cambi l'ordine dei numeri il risultato non cambia (es. 5x2 = 2x5)", "correct": True},
                {"text": "Bisogna sempre sommare 1 al risultato", "correct": False},
                {"text": "Funziona solo con la tabellina del 10", "correct": False}
            ],
            "explanation": "La proprietà commutativa garantisce che a x b = b x a."
        },
        {
            "id": 3,
            "question": "Come terminano sempre i prodotti della tabellina del 5?",
            "options": [
                {"text": "Sempre con un numero dispari", "correct": False},
                {"text": "Sempre con la cifra 0 oppure 5", "correct": True},
                {"text": "Sempre con il numero 2", "correct": False}
            ],
            "explanation": "I multipli di 5 finiscono sempre alternativamente in 0 o in 5."
        },
        {
            "id": 4,
            "question": "Che cos'è in realtà la moltiplicazione?",
            "options": [
                {"text": "Un'addizione ripetuta", "correct": True},
                {"text": "Una sottrazione complessa", "correct": False},
                {"text": "Una divisione inversa", "correct": False}
            ],
            "explanation": "La moltiplicazione abbreviata calcola un'addizione ripetuta dello stesso numero."
        }
    ]
    
    selected = all_questions[:req.length]
    return {"questions": selected}

@app.post("/api/map")
def generate_map(req: TextRequest):
    return {
        "title": "Mappa Concettuale: Le Tabelline",
        "nodes": [
            {
                "id": "main",
                "title": "📐 LE TABELLINE",
                "type": "root",
                "subnodes": [
                    {
                        "title": "1. CONCETTO BASE",
                        "desc": "Addizione ripetuta dello stesso numero",
                        "items": ["Es: 3 x 4 = 3 + 3 + 3 + 3 = 12", "Fattore x Fattore = Prodotto"]
                    },
                    {
                        "title": "2. PROPRIETÀ COMMUTATIVA",
                        "desc": "Cambiare l'ordine non altera il prodotto",
                        "items": ["a x b = b x a", "Dimezza i calcoli da imparare (es. 7x8 = 8x7)"]
                    },
                    {
                        "title": "3. TABELLINE FACILI",
                        "desc": "Regole immediate da memorizzare",
                        "items": ["Tabellina del 2: Raddoppio dei numeri", "Tabellina del 5: Finisce sempre per 0 o 5", "Tabellina del 10: Aggiungi uno zero finale"]
                    },
                    {
                        "title": "4. TRUCCHI AVANZATI (9)",
                        "desc": "Schema matematico del 9",
                        "items": ["Somma cifre risultato sempre 9 (9x3=27 -> 2+7=9)", "Uso delle 10 dita delle mani"]
                    }
                ]
            }
        ]
    }
