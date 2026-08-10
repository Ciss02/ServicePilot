# Login, sessione e logout

SP-031 permette agli account demo di autenticarsi tramite API e di mantenere la propria
identità tra richieste successive.

## Perché esiste

Confrontare una password è sufficiente per riconoscere l'utente una sola volta. Una
sessione consente invece al browser di dimostrare nelle richieste successive che il
login è già avvenuto, senza reinviare continuamente la password.

## Flusso

1. `POST /auth/login` riceve email e password.
2. Il backend cerca un account attivo e verifica la password contro l'hash Argon2.
3. Se il controllo riesce, crea un codice casuale valido per otto ore.
4. Il browser riceve il codice nel cookie `servicepilot_session`.
5. Il database salva soltanto l'impronta SHA-256 del codice, collegata all'utente.
6. `GET /auth/session` restituisce l'identità quando cookie, sessione e account sono
   ancora validi.
7. `POST /auth/logout` elimina la sessione dal database e il cookie dal browser.

Il cookie usa `HttpOnly`, quindi il normale codice JavaScript della pagina non può
leggerlo, e `SameSite=Lax`, che limita l'invio da siti esterni. In locale può viaggiare
su HTTP; in un ambiente HTTPS occorre impostare:

```powershell
$env:SERVICEPILOT_SECURE_COOKIES = "true"
```

## Endpoint

### `POST /auth/login`

Ingresso:

```json
{
  "email": "tecnico@servicepilot.example",
  "password": "valore-configurato-fuori-dal-repository"
}
```

La risposta contiene soltanto identificativo, email, nome visibile e ruolo. Password,
hash e codice di sessione non compaiono nel JSON. Email inesistente, password errata e
account inattivo restituiscono tutti `401` con lo stesso messaggio, per non rivelare
quale controllo è fallito.

### `GET /auth/session`

Non richiede un corpo: il browser invia automaticamente il cookie. Restituisce la stessa
identità sicura del login oppure `401` se la sessione manca, è sconosciuta, è scaduta o
l'account è diventato inattivo.

### `POST /auth/logout`

Revoca la sessione corrente e restituisce `204`. È sicuro ripeterlo anche quando non
esiste una sessione.

## Dove sono salvati i dati

- `users.password_hash` conserva soltanto l'hash Argon2 della password;
- il cookie del browser conserva il codice casuale della sessione;
- `auth_sessions.token_hash` conserva soltanto l'impronta del codice;
- `auth_sessions` conserva inoltre utente, creazione e scadenza.

Una copia del database non contiene quindi né password né codici di sessione direttamente
utilizzabili.

## Limiti attuali

SP-031 autentica l'utente, ma non modifica ancora le regole delle API ticket. SP-032
userà questa identità per limitare lettura, creazione e modifica in base al ruolo. La
pagina grafica di accesso appartiene a SP-040; limiti ai tentativi ripetuti e revisione
finale della sicurezza della demo appartengono a SP-081.
