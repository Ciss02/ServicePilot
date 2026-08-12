# Controlli automatici

## Scopo

I controlli automatici segnalano subito se una modifica rompe un comportamento già
verificato o rende il codice incoerente. Gli stessi comandi vengono eseguiti sul computer
locale e da GitHub Actions, in un ambiente Linux appena creato con Python 3.13.

## Controlli eseguiti

1. `python -m pip check` verifica che le dipendenze installate siano compatibili;
2. `python -m ruff check .` rileva errori comuni, import inutilizzati o disordinati;
3. `python -m ruff format --check .` verifica la formattazione senza cambiare i file;
4. `python -m pytest -W error` esegue tutti i test e tratta ogni avviso come un errore.

Il workflow non richiede password demo o chiavi Gemini. I test sostituiscono i servizi
esterni con componenti fittizi e non consumano chiamate AI reali.

## Esecuzione locale

Dopo aver installato `requirements-dev.txt`, eseguire dalla radice del progetto:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -W error
```

Per applicare automaticamente la formattazione prima di ripetere i controlli:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
```

## Esecuzione su GitHub

Il file `.github/workflows/quality.yml` avvia i controlli:

- per ogni pull request diretta a `main`;
- dopo ogni aggiornamento di `main`;
- manualmente dalla pagina Actions di GitHub.

GitHub annulla un controllo precedente ancora in corso sullo stesso ramo quando arriva
un aggiornamento più recente. In questo modo il risultato visibile riguarda sempre il
codice attuale.

## Interpretare il risultato

- segno verde: tutti i controlli sono passati;
- segno rosso: almeno un comando è fallito; il dettaglio indica il passaggio e l'errore;
- controllo in corso: GitHub sta ancora preparando l'ambiente o eseguendo i comandi.

Una pull request è pronta per il merge soltanto quando il controllo `Qualita e test` è
verde e la modifica è stata verificata anche per gli aspetti visivi eventualmente coinvolti.
