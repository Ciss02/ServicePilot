# Deploy della demo

ServicePilot è pubblicato su una singola istanza gratuita Render nella regione di
Francoforte. Il portale è raggiungibile tramite HTTPS; il secondo processo FastAPI che
simula le azioni ascolta soltanto su `127.0.0.1` e quindi non è esposto a Internet.

## Demo pubblica

- URL: `https://servicepilot-ai-demo-ciss02.onrender.com`
- Provider e piano: Render Free
- Regione: Francoforte
- Blueprint: `servicepilot-ai-demo`
- Servizio: `servicepilot-ai-demo-ciss02`

Il 13 agosto 2026 sono stati verificati l'endpoint `/health`, la pagina di login HTTPS e
un percorso completo partito da una sessione anonima. Il collaudo ha creato il ticket demo `SP-0007`
da una sola descrizione fittizia, confermato la classificazione come tecnico, eseguito
un'assegnazione simulata con audit e infine ripristinato i dati iniziali come admin.

## Perché una singola istanza

Il piano gratuito assegna un monte ore complessivo ai servizi e li spegne dopo un
periodo di inattività. Tenere il simulatore nella stessa istanza evita di consumare ore
doppie e impedisce che la prima azione fallisca mentre un secondo servizio si riavvia.
Le due applicazioni restano comunque processi distinti.

## Dati e ripristino

La demo usa intenzionalmente SQLite e la cartella `/tmp/servicepilot`. Sul piano
gratuito questi file sono temporanei: un riavvio, un nuovo deploy o lo spegnimento per
inattività li elimina. Il comando `python -m app.deployment` ricrea le cartelle e carica
il dataset fittizio prima di avviare il server.

Durante una visita, un amministratore può anche usare **Ripristina demo** e digitare
`RIPRISTINA DEMO`. Il ripristino sostituisce ticket, azioni, audit e knowledge base in
una sola operazione, conservando gli account e la sessione amministrativa attuale.

Questa scelta è adatta a un portfolio, non a dati reali o a un ambiente di produzione.
Per rendere permanenti ticket e documenti serviranno un database e uno spazio file
persistenti.

## Segreti richiesti da Render

Il file `render.yaml` descrive il servizio, ma lascia senza valore quattro variabili.
Render le richiede durante la prima creazione del Blueprint:

- `SERVICEPILOT_DEMO_EMPLOYEE_PASSWORD`;
- `SERVICEPILOT_DEMO_TECHNICIAN_PASSWORD`;
- `SERVICEPILOT_DEMO_ADMIN_PASSWORD`;
- `GEMINI_API_KEY`.

Le tre password devono essere diverse, contenere almeno 12 caratteri e appartenere
soltanto a questa demo. La chiave Gemini va copiata da Google AI Studio. Nessun valore
deve essere scritto nel repository, nei log o negli screenshot.

## Pubblicazione

1. Aprire Render e scegliere **New > Blueprint**.
2. Collegare il repository GitHub `Ciss02/ServicePilot`.
3. Selezionare il ramo da collaudare e il file `render.yaml`.
4. Inserire i quattro valori segreti quando richiesto.
5. Verificare che venga creato soltanto `servicepilot-ai-demo-ciss02` con piano Free.
6. Attendere che `/health` risponda e aprire l'indirizzo HTTPS assegnato.

L'aggiornamento automatico parte soltanto quando i controlli GitHub del nuovo commit
sono passati.

## Collaudo anonimo

Usare una finestra privata, così non viene riutilizzata una sessione locale:

1. aprire la pagina pubblica e verificare che il browser mostri HTTPS;
2. accedere come dipendente e creare un ticket descrivendo soltanto il problema;
3. uscire e accedere come tecnico, controllare classificazione e proposta;
4. approvare una delle azioni simulate e verificare riferimento ed evento audit;
5. uscire e accedere come amministratore;
6. eseguire `RIPRISTINA DEMO`;
7. verificare che il ticket appena creato sia sparito, che le azioni siano nuovamente in
   attesa e che i sei ticket iniziali siano presenti. Se durante la prova è stato
   caricato un documento fittizio, verificare anche la sua rimozione.

Il collaudo non deve usare nomi, documenti o credenziali reali.
