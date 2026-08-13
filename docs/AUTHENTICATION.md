# Login, sessione e logout

Gli account demo possono autenticarsi tramite API o interfaccia web e mantenere la
propria identità tra richieste successive grazie a una sessione protetta.

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

La pagina `GET /login` invia gli stessi dati tramite `POST /login`. In caso di successo
porta la persona a `/app`; `POST /logout` revoca la stessa sessione e torna al modulo.
Le rotte API restano disponibili per client che scambiano JSON.

Il cookie usa `HttpOnly`, quindi il normale codice JavaScript della pagina non può
leggerlo, e `SameSite=Lax`, che limita l'invio da siti esterni. In locale può viaggiare
su HTTP; in un ambiente HTTPS occorre impostare:

```powershell
$env:SERVICEPILOT_SECURE_COOKIES = "true"
```

La protezione del portale limita inoltre il login a 10 tentativi al minuto per client,
elimina le sessioni scadute durante un nuovo accesso e conserva al massimo 20 sessioni
attive per account.
La modalità pubblica richiede cookie HTTPS e applica controllo dell'origine, host ammessi
e intestazioni di sicurezza come descritto in
[`SECURITY_AND_DEMO_LIMITS.md`](SECURITY_AND_DEMO_LIMITS.md).

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

## Autorizzazione e limiti

Questa identità protegge le API ticket secondo la matrice descritta in
[`AUTHORIZATION.md`](AUTHORIZATION.md) e la pagina grafica descritta in
[`WEB_INTERFACE.md`](WEB_INTERFACE.md). I contatori di login vivono nel singolo processo:
un deploy con più istanze richiederà un archivio condiviso.
