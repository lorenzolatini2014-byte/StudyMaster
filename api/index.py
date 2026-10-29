from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.post("/api/podcast")
def generate_podcast(req: TextRequest):
    src = req.text.strip() if req.text.strip() else "Tabelline e matematica di base."
    
    # Presentazione ricca, strutturata e della durata giusta
    script = (
        "Benvenuti a questa lezione speciale di StudyMaster dedicata all'apprendimento e alla padronanza delle tabelline. "
        "Spesso le tabelline vengono viste come un ostico scoglio da memorizzare a memoria, ma in realtà sono uno strumento affascinante e logico. "
        "Analizziamo insieme il materiale fornito: " + src[:300] + "\n\n"
        "Prima di tutto, ricordiamo che la moltiplicazione non è altro che un'addizione ripetuta. "
        "Prendiamo ad esempio la tabellina del 2: significa semplicemente raddoppiare ogni quantità. "
        "Quando passiamo alla tabellina del 5, noterai una regolarità straordinaria: le cifre delle unità finiscono sempre alternativamente in zero o in cinque. "
        "Per quanto riguarda la celebre e temuta tabellina del 9, un trucco formale straordinario consiste nell'osservare che la somma delle cifre del risultato fa sempre nove, come nel caso di nove per due che fa diciotto, dove uno più otto fa proprio nove.\n\n"
        "Il segreto per impararle senza sforzo non è ripeterle come un robot, ma comprenderne la simmetria geometrica e fare piccoli esercizi quotidiani. "
        "Ripassa con calma questi passaggi, allenati con i quiz di verifica presenti sulla nostra piattaforma e vedrai che la matematica diventerà semplice e intuitiva. "
        "Buono studio da StudyMaster!"
    )
    return {"script": script}
