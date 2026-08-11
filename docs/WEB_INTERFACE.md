# Interfaccia web iniziale

SP-040 introduce la base grafica responsive di ServicePilot AI e collega il modulo di
accesso alle sessioni già disponibili nel backend.

## Quale problema risolve

Prima di SP-040 l'autenticazione poteva essere provata soltanto tramite API. Ora una
persona può accedere dal browser con un modulo comprensibile, raggiungere una pagina
protetta e chiudere la sessione.

## Pagine disponibili

- `GET /` indirizza verso l'area dell'applicazione;
- `GET /login` mostra il modulo di accesso;
- `POST /login` controlla email e password e avvia la sessione;
- `GET /app` mostra la base dell'area autenticata;
- `POST /logout` revoca la sessione e torna alla pagina di accesso.

Una persona non autenticata che visita `/app` viene accompagnata a `/login`. Chi ha già
una sessione valida non deve invece ripetere l'accesso.

## Dati e controlli

Il modulo riceve email e password. Pydantic controlla la forma dei dati, poi il servizio
di autenticazione condiviso verifica account attivo e hash Argon2. Per qualsiasi
credenziale non valida viene mostrato lo stesso messaggio: in questo modo la pagina non
rivela se una particolare email esiste.

La password non viene reinserita nel documento HTML dopo un errore. La sessione continua
a usare il cookie `HttpOnly` e il database conserva soltanto l'impronta del codice
casuale, come descritto in [`AUTHENTICATION.md`](AUTHENTICATION.md).

## Struttura grafica e accessibilità

I template Jinja2 condividono intestazione, contenuto principale e piè di pagina. Lo
stile è contenuto in un solo file CSS e non scarica immagini, font o script esterni.
Sono presenti:

- etichette visibili per i campi;
- collegamento per saltare direttamente al contenuto;
- indicatore del punto attivo quando si usa la tastiera;
- messaggio di errore annunciabile dalle tecnologie assistive;
- colori con contrasto leggibile e pulsanti abbastanza grandi;
- adattamento a desktop, tablet e telefono;
- rispetto della preferenza di riduzione delle animazioni.

## Dipendenze

- `Jinja2 3.1.6` trasforma i template HTML nei documenti inviati al browser;
- `python-multipart 0.0.32` permette a FastAPI di leggere i campi inviati dai moduli.

Non è stato aggiunto JavaScript: la pagina di accesso non ne ha bisogno. HTMX rimane una
tecnologia prevista e potrà essere introdotta quando una funzione interattiva ne trarrà
un beneficio reale.

## Limiti attuali

`/app` è volutamente una base protetta, non una dashboard completa. Elenco e dettaglio
dei ticket personali appartengono a SP-041; raccolta guidata e conferma appartengono a
SP-042 e SP-043. Limiti ai tentativi ripetuti e revisione finale della sicurezza sono
previsti in SP-081.
