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

Il repository è nella fase iniziale. Sono disponibili specifiche, roadmap e piano di
progetto; il codice dell'applicazione non è ancora stato implementato.

La prossima attività è indicata in
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

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

The repository is in its foundation phase. Requirements, roadmap, and project plan are
available, but the application code has not been implemented yet.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the next task.

### Disclaimer

This is a portfolio demo. All users, locations, tickets, documents, and procedures will
be synthetic and unrelated to real employers or production systems.

## License

This project is available under the [MIT License](LICENSE).
