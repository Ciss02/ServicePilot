# ServicePilot AI

> Progetto portfolio in fase di sviluppo / Portfolio project under development

## Italiano

ServicePilot AI è un'applicazione dimostrativa per la gestione intelligente delle
richieste di assistenza IT in un'azienda fittizia con più sedi.

L'obiettivo è mostrare un flusso completo e verificabile:

1. un dipendente descrive e conferma una richiesta;
2. il sistema crea e classifica il ticket;
3. il backend calcola la priorità con regole deterministiche;
4. un tecnico controlla i suggerimenti dell'AI e le relative fonti;
5. qualsiasi azione proposta richiede approvazione umana;
6. le operazioni importanti vengono registrate nell'audit log.

### Stato attuale

Le fondamenta e le regole iniziali del dominio sono complete. Sono disponibili una
prima applicazione FastAPI, il vocabolario dei ticket, la matrice della priorità, i
contratti dati validati, il database iniziale, un dataset completamente sintetico e le
API essenziali per creare e leggere ticket.

La prossima attività è indicata in
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

### Preparazione dell'ambiente locale

Requisito: Python 3.13.

Da PowerShell, nella cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

L'attivazione fa sì che i comandi `python` e `pip` usino le librerie isolate di
ServicePilot. Per uscire dall'ambiente:

```powershell
deactivate
```

Se PowerShell impedisce l'attivazione, è possibile usare direttamente Python senza
modificare le impostazioni del sistema:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### Avvio dell'applicazione

Da PowerShell, nella cartella del progetto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Il server sarà disponibile all'indirizzo `http://127.0.0.1:8000`. L'endpoint
`http://127.0.0.1:8000/health` verifica che il servizio risponda, mentre la
documentazione interattiva delle API è disponibile su `http://127.0.0.1:8000/docs`.

Le prime operazioni disponibili sono `POST /tickets`, `GET /tickets` e
`GET /tickets/{ticket_id}`. Prima di provarle è possibile caricare il dataset demo con
il comando descritto più sotto.

Per eseguire i test automatici:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Per creare il database SQLite locale e le tabelle iniziali:

```powershell
.\.venv\Scripts\python.exe -m app.db
```

Il comando può essere ripetuto senza cancellare i dati. La struttura delle tabelle e
la configurazione sono spiegate in
[`docs/DATABASE.md`](docs/DATABASE.md).

Per caricare o riallineare sedi, profili e ticket dimostrativi:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

### Tecnologie previste

- Python e FastAPI
- SQLAlchemy con SQLite in sviluppo
- Jinja2 e HTMX
- Gemini tramite un adapter indipendente dal provider
- knowledge base PDF/Markdown con RAG
- pytest e controlli automatici GitHub Actions

### Documentazione

- [Specifica MVP](docs/ServicePilot_AI_MVP_Specification.md)
- [Roadmap di apprendimento e sviluppo](docs/ServicePilot_4_Week_Learning_and_Build_Roadmap.md)
- [Piano e tasklist](docs/PROJECT_PLAN.md)
- [Stato corrente](docs/PROJECT_STATUS.md)
- [Decisioni di progetto](docs/DECISIONS.md)
- [Vocabolario del dominio](docs/DOMAIN_VOCABULARY.md)
- [Contratti dati del ticket](docs/TICKET_CONTRACTS.md)
- [Database iniziale](docs/DATABASE.md)
- [Dataset dimostrativo](docs/DEMO_DATA.md)
- [API essenziali dei ticket](docs/TICKET_API.md)

### Avvertenza

ServicePilot AI è una demo per portfolio. Utenti, sedi, ticket e procedure saranno
completamente fittizi. Il progetto non utilizza dati o sistemi di aziende reali.

## English

ServicePilot AI is a portfolio demonstration application for intelligent IT service
request management in a fictional multi-site company.

The planned MVP covers guided ticket creation, deterministic priority calculation,
role-based access, AI-assisted classification, grounded suggestions from a document
knowledge base, human approval of simulated actions, and a complete audit trail.

### Current status

The project foundation and initial domain rules are complete. A first FastAPI
application, ticket vocabulary, priority matrix, validated data contracts, the initial
database, a fully synthetic demo dataset, and the essential ticket create/read APIs are
available.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the next task.

### Local environment setup

Requirement: Python 3.13.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

### Run the application

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health` to check the service or
`http://127.0.0.1:8000/docs` to view the interactive API documentation.

The first available operations are `POST /tickets`, `GET /tickets`, and
`GET /tickets/{ticket_id}`.

Run the automated tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Create the local SQLite database and its initial tables with:

```powershell
.\.venv\Scripts\python.exe -m app.db
```

The command is repeatable and does not delete existing data. See
[`docs/DATABASE.md`](docs/DATABASE.md) for the schema and configuration details.

Load or realign the synthetic sites, profiles, and tickets with:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

### Disclaimer

This is a portfolio demo. All users, locations, tickets, documents, and procedures will
be synthetic and unrelated to real employers or production systems.

## License

This project is available under the [MIT License](LICENSE).
