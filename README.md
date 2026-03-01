# Typology v2

Test psicologico junghiano conversazionale con avatar AI Sofia.  
72 domande (60 junghiane + 12 Otroversione Kaminski).

## Struttura

```
typology-v2/
├── backend/
│   ├── main.py          # FastAPI server
│   └── requirements.txt
├── frontend/
│   └── index.html       # App React conversazionale
├── render.yaml          # Configurazione Render
└── README.md
```

## Deploy su Render

### 1. Backend (API)
- New Web Service → collega questo repository
- Root Directory: `backend`
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment Variable: `ANTHROPIC_API_KEY` = la tua chiave Anthropic

### 2. Frontend (Static Site)
- New Static Site → collega questo repository
- Root Directory: `frontend`
- Publish Directory: `.`
- Dopo il deploy, aggiorna la variabile `API` in `index.html`  
  con l'URL del tuo backend Render (es. `https://typology-api.onrender.com`)

## Variabili d'ambiente necessarie

| Variabile | Descrizione |
|-----------|-------------|
| `ANTHROPIC_API_KEY` | Chiave API Anthropic (obbligatoria per il backend) |
