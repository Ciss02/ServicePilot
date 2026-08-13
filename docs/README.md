# Guida alla documentazione

Questa pagina aiuta a scegliere il documento giusto senza dover conoscere i numeri
delle issue GitHub. I documenti tecnici descrivono lo stato attuale dell'MVP; i registri
di progetto conservano invece intenzionalmente codici e frasi scritte durante lo
sviluppo.

## Per capire il progetto

- [`../README.md`](../README.md) — panoramica, demo, installazione e credenziali locali;
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — componenti, flussi dei dati e confini di
  sicurezza;
- [`ServicePilot_AI_MVP_Specification.md`](ServicePilot_AI_MVP_Specification.md) —
  perimetro approvato dell'MVP;
- [`V020_PRODUCT_PLAN.md`](V020_PRODUCT_PLAN.md) — comportamento e decisioni condivise
  della roadmap `v0.2.0`;
- [`SECURITY_AND_DEMO_LIMITS.md`](SECURITY_AND_DEMO_LIMITS.md) — protezioni e limiti da
  conoscere prima di usare la demo;
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — configurazione Render, ripristino e collaudo
  pubblico;
- [`QUALITY_CHECKS.md`](QUALITY_CHECKS.md) — controlli automatici e strategia di test.

## Accesso e interfaccia

- [`DEMO_ACCOUNTS.md`](DEMO_ACCOUNTS.md) — account sintetici e gestione delle password;
- [`AUTHENTICATION.md`](AUTHENTICATION.md) — login, sessione e logout;
- [`AUTHORIZATION.md`](AUTHORIZATION.md) — permessi dei tre ruoli;
- [`WEB_INTERFACE.md`](WEB_INTERFACE.md) — struttura delle pagine web;
- [`EMPLOYEE_AREA.md`](EMPLOYEE_AREA.md) — dashboard e ticket del dipendente;
- [`GUIDED_TICKET_INTAKE.md`](GUIDED_TICKET_INTAKE.md) — raccolta guidata della richiesta;
- [`TECHNICIAN_QUEUE.md`](TECHNICIAN_QUEUE.md) — coda operativa di tecnico e admin;
- [`ADMIN_TOOLS.md`](ADMIN_TOOLS.md) — fonti, audit e ripristino della demo.

## Ticket e dati

- [`DOMAIN_VOCABULARY.md`](DOMAIN_VOCABULARY.md) — stati, priorità e valori controllati;
- [`TICKET_CONTRACTS.md`](TICKET_CONTRACTS.md) — dati accettati e restituiti;
- [`TICKET_API.md`](TICKET_API.md) — endpoint e regole del ciclo di vita;
- [`ATTACHMENTS.md`](ATTACHMENTS.md) — archivio privato, limiti, autorizzazione e pulizia;
- [`DATABASE.md`](DATABASE.md) — tabelle, configurazione e persistenza;
- [`SUPPORT_GROUPS.md`](SUPPORT_GROUPS.md) — catalogo amministrabile e appartenenze;
- [`DEMO_DATA.md`](DEMO_DATA.md) — contenuto sintetico e caricamento ripetibile.

## AI e knowledge base

- [`AI_MODEL_ADAPTER.md`](AI_MODEL_ADAPTER.md) — collegamento facoltativo a Gemini;
- [`AI_TICKET_EXTRACTION.md`](AI_TICKET_EXTRACTION.md) — estrazione dalla descrizione;
- [`AI_TICKET_CLASSIFICATION.md`](AI_TICKET_CLASSIFICATION.md) — classificazione e
  revisione umana;
- [`KNOWLEDGE_UPLOAD.md`](KNOWLEDGE_UPLOAD.md) — controlli dei documenti caricati;
- [`KNOWLEDGE_EXTRACTION.md`](KNOWLEDGE_EXTRACTION.md) — estrazione e segmentazione;
- [`KNOWLEDGE_SEARCH.md`](KNOWLEDGE_SEARCH.md) — embedding e ricerca semantica;
- [`SOURCED_SOLUTIONS.md`](SOURCED_SOLUTIONS.md) — suggerimenti RAG con fonti.

## Azioni e tracciamento

- [`PROPOSED_ACTIONS.md`](PROPOSED_ACTIONS.md) — struttura delle azioni suggerite;
- [`SIMULATED_ACTION_SERVICES.md`](SIMULATED_ACTION_SERVICES.md) — integrazioni REST
  esclusivamente simulate;
- [`ACTION_APPROVAL.md`](ACTION_APPROVAL.md) — decisione umana ed esecuzione controllata;
- [`AUDIT_LOG.md`](AUDIT_LOG.md) — cronologia delle operazioni rilevanti.

## Registri storici

Questi file mantengono volutamente i codici `SP-xxx` perché spiegano come il lavoro è
stato suddiviso e verificato nel tempo. Le frasi al futuro presenti nelle decisioni
descrivono il momento in cui la scelta è stata presa, non lo stato attuale del portale.

- [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — tasklist e prossima attività;
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — stato corrente e prove raccolte a ogni passo;
- [`DECISIONS.md`](DECISIONS.md) — registro cronologico delle decisioni;
- [`ServicePilot_4_Week_Learning_and_Build_Roadmap.md`](ServicePilot_4_Week_Learning_and_Build_Roadmap.md)
  — piano formativo originario.

Per iniziare una nuova sessione Codex bastano `AGENTS.md`, `PROJECT_STATUS.md` e
l'attività indicata in `PROJECT_PLAN.md`. Gli altri documenti si aprono solo quando
servono alla funzione su cui si sta lavorando.
