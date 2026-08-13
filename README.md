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
API per creare, leggere e gestire tecnicamente i ticket, oltre agli account demo con
password protette tramite Argon2. Gli account possono effettuare login, mantenere una
sessione autenticata e fare logout. Le API applicano inoltre i permessi dei ruoli:
ticket personali per i dipendenti e gestione completa per tecnico e amministratore. È
ora disponibile anche una pagina di accesso responsive collegata alla sessione e una
base protetta per le prossime schermate dell'applicazione. Il dipendente dispone inoltre
di un riepilogo dei propri ticket e del relativo dettaglio, senza poter consultare le
richieste di altri account.

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
La pagina di accesso è disponibile su `http://127.0.0.1:8000/login`.

I servizi REST fittizi delle azioni sono un'applicazione separata e possono essere
avviati, quando servono per una prova locale, su `127.0.0.1:8011`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.simulated_services.main:app `
  --host 127.0.0.1 --port 8011
```

Non assegnano ticket reali e non inviano comunicazioni. Il loro funzionamento è
descritto in [`docs/SIMULATED_ACTION_SERVICES.md`](docs/SIMULATED_ACTION_SERVICES.md).

Le operazioni di accesso sono `POST /auth/login`, `GET /auth/session` e
`POST /auth/logout`. Sono inoltre disponibili `POST /tickets`, `GET /tickets`,
`GET /tickets/{ticket_id}` e `PATCH /tickets/{ticket_id}`. Prima di provarle è possibile
caricare il dataset demo con il comando descritto più sotto. Le operazioni sui ticket
richiedono una sessione autenticata.

Per eseguire i test automatici:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Per eseguire gli stessi controlli di qualità usati da GitHub:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -W error
```

La configurazione e il significato dei risultati sono descritti in
[`docs/QUALITY_CHECKS.md`](docs/QUALITY_CHECKS.md).

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

Prima del comando vanno configurate le tre password demo come variabili d'ambiente,
seguendo [`docs/DEMO_ACCOUNTS.md`](docs/DEMO_ACCOUNTS.md). Nessuna password predefinita
è presente nel repository.

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
- [Account demo e password sicure](docs/DEMO_ACCOUNTS.md)
- [Login, sessione e logout](docs/AUTHENTICATION.md)
- [Interfaccia web iniziale](docs/WEB_INTERFACE.md)
- [Area del dipendente](docs/EMPLOYEE_AREA.md)
- [Raccolta guidata dei dati](docs/GUIDED_TICKET_INTAKE.md)
- [Autorizzazione per ruolo](docs/AUTHORIZATION.md)
- [API essenziali dei ticket](docs/TICKET_API.md)
- [Adapter del modello AI](docs/AI_MODEL_ADAPTER.md)
- [Estrazione AI dei dati del ticket](docs/AI_TICKET_EXTRACTION.md)
- [Classificazione AI suggerita](docs/AI_TICKET_CLASSIFICATION.md)
- [Upload sicuro dei documenti](docs/KNOWLEDGE_UPLOAD.md)
- [Estrazione e segmentazione della knowledge base](docs/KNOWLEDGE_EXTRACTION.md)
- [Indicizzazione e ricerca della knowledge base](docs/KNOWLEDGE_SEARCH.md)
- [Suggerimenti tecnici con fonti](docs/SOURCED_SOLUTIONS.md)
- [Modello delle azioni proposte](docs/PROPOSED_ACTIONS.md)
- [Servizi REST simulati per le azioni](docs/SIMULATED_ACTION_SERVICES.md)
- [Approvazione umana delle azioni](docs/ACTION_APPROVAL.md)
- [Audit log e cronologia dei ticket](docs/AUDIT_LOG.md)
- [Strumenti amministrativi e ripristino demo](docs/ADMIN_TOOLS.md)
- [Controlli automatici di qualità](docs/QUALITY_CHECKS.md)
- [Sicurezza e limiti della demo](docs/SECURITY_AND_DEMO_LIMITS.md)
- [Deploy e ripristino della demo](docs/DEPLOYMENT.md)

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
database, a fully synthetic demo dataset, and APIs to create, read, classify, assign,
and update tickets are available. Demo accounts store Argon2 password hashes whose
plain-text values come only from environment variables, and can now log in, keep an
authenticated session, and log out. Ticket APIs enforce role permissions: employees
see only their own requests, while technicians and administrators manage the full queue.
A responsive sign-in page now connects the browser to the same session mechanism and
provides the protected foundation for the next application screens. Employees can also
review their own ticket summary and details without accessing requests owned by other
accounts.

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
Open `http://127.0.0.1:8000/login` to use the browser sign-in page.

The separate fake action services can be started locally on `127.0.0.1:8011`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.simulated_services.main:app `
  --host 127.0.0.1 --port 8011
```

They do not assign real tickets or send messages. See
[`docs/SIMULATED_ACTION_SERVICES.md`](docs/SIMULATED_ACTION_SERVICES.md).

Authentication operations are `POST /auth/login`, `GET /auth/session`, and
`POST /auth/logout`. Ticket operations are `POST /tickets`, `GET /tickets`,
`GET /tickets/{ticket_id}`, and `PATCH /tickets/{ticket_id}`. Ticket operations require
an authenticated session.

Run the automated tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run the same quality checks used by GitHub with:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -W error
```

See [`docs/QUALITY_CHECKS.md`](docs/QUALITY_CHECKS.md) for the configuration and result
interpretation.

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

Configure the three demo password environment variables first, as explained in
[`docs/DEMO_ACCOUNTS.md`](docs/DEMO_ACCOUNTS.md). The repository contains no default
password.

### Disclaimer

This is a portfolio demo. All users, locations, tickets, documents, and procedures will
be synthetic and unrelated to real employers or production systems.

## License

This project is available under the [MIT License](LICENSE).
