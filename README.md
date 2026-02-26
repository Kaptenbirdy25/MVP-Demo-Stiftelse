# Stiftelseforum MVP – förenklad version

En liten Python-baserad MVP för caseet kring stiftelser. UI:t är medvetet nedskalat till tre flikar:

1. **Inmatning** – ett enkelt formulär för den sökande
2. **Resultat** – topp 3 matchningar och ett ansökningsutkast
3. **Bonus** – ett regelbaserat beslutsstöd för stiftelser

## Varför denna version?
Den här versionen är gjord för att kännas som en tydlig MVP snarare än en halvfärdig fullprodukt. Matchningen är lokal och förklarbar. OpenAI är valfritt och används bara för smartare tolkning, bättre utkast och valfri webbresearch.

## Funktioner
- enkelt formulär i Streamlit
- lokal stiftelsekatalog i JSON
- topp 3 matchningar med motiveringar
- redigerbart ansökningsutkast
- bonusflik som visar AI-snålt beslutsstöd för handläggare
- lokal lagring i SQLite
- valfritt OpenAI-stöd via `.env`

## Kom igång på Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Öppna sedan `http://localhost:8501`

## OpenAI (valfritt)
Skriv in din nyckel i `.env` om du vill aktivera AI:

```env
OPENAI_API_KEY=din_nyckel_har
OPENAI_MODEL=gpt-5-mini
OPENAI_WEB_MODEL=gpt-5.2
ENABLE_OPENAI_BY_DEFAULT=true
ENABLE_WEB_RESEARCH_BY_DEFAULT=false
```

Utan nyckel fungerar appen fortfarande med lokal fallback.

## Repo-struktur
```text
stiftelseforum_mvp/
├── app.py
├── config.py
├── db.py
├── drafting.py
├── matching.py
├── models.py
├── openai_service.py
├── repository.py
├── seed.py
├── requirements.txt
├── .env.example
├── data/
│   └── stiftelser.json
└── tests/
    └── test_matching.py
```

## Test
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```
