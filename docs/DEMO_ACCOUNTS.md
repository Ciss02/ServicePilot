# Account demo e password sicure

SP-030 prepara i cinque account sintetici per il futuro login senza conservare password
leggibili nel repository o nel database.

## Account disponibili

- tre dipendenti condividono la credenziale configurata per il ruolo `employee`;
- `tecnico@servicepilot.example` usa la credenziale del ruolo `technician`;
- `admin@servicepilot.example` usa la credenziale del ruolo `admin`.

Gli indirizzi appartengono al dominio riservato `.example` e non rappresentano persone
reali.

## Configurazione locale

Prima di eseguire il seed, impostare tre variabili d'ambiente con valori di almeno 12
caratteri:

```powershell
$env:SERVICEPILOT_DEMO_EMPLOYEE_PASSWORD = Read-Host "Password dipendenti demo"
$env:SERVICEPILOT_DEMO_TECHNICIAN_PASSWORD = Read-Host "Password tecnico demo"
$env:SERVICEPILOT_DEMO_ADMIN_PASSWORD = Read-Host "Password amministratore demo"
```

I nomi sono presenti anche in `.env.example`, lasciati intenzionalmente senza valori.
Le credenziali scelte devono rimanere nell'ambiente locale o nella configurazione sicura
del servizio di hosting; non devono essere scritte nei file versionati.

Caricare quindi i dati:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Se una variabile manca o contiene meno di 12 caratteri, il comando si interrompe prima
di modificare il dataset e indica soltanto il nome della variabile, mai il suo valore.

## Cosa viene salvato

Il backend usa `pwdlib` 0.3.0 e Argon2. La password viene trasformata in un hash con un
valore casuale incorporato: non è possibile ricavare direttamente la password
dall'informazione salvata. Lo stesso testo produce hash diversi, ma può essere verificato
in modo sicuro durante il futuro login.

Il seed riutilizza un hash già valido. Se cambia la password configurata, sostituisce
l'hash dell'account demo. Il testo originale non viene salvato né stampato.

## Limiti attuali

SP-030 prepara account e verifica delle password, ma non espone ancora un modulo di
accesso. SP-031 aggiungerà login, sessione e logout; SP-032 applicherà i permessi dei tre
ruoli alle API.
