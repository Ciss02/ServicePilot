# ServicePilot AI - Vocabolario del dominio

Questo documento descrive i valori ammessi per i concetti principali del portale.
La fonte usata dal codice è `app/domain/vocabulary.py`.

I valori interni sono scritti in inglese, in minuscolo e senza spazi. Sono pensati per
API e database e quindi devono rimanere stabili. Le etichette italiane sono destinate
all'interfaccia e alla documentazione.

## Ruoli

| Valore interno | Etichetta italiana | Responsabilità nell'MVP |
| --- | --- | --- |
| `employee` | Dipendente | Apre richieste e consulta soltanto i propri ticket. |
| `technician` | Tecnico IT | Gestisce i ticket e approva o rifiuta le azioni proposte. |
| `admin` | Amministratore | Ha i permessi tecnici e gestisce documenti, dati demo e audit. |

## Categorie dei ticket

| Valore interno | Etichetta italiana |
| --- | --- |
| `account_and_access` | Account e accessi |
| `devices_and_hardware` | Dispositivi e hardware |
| `software_and_applications` | Software e applicazioni |
| `network_and_connectivity` | Rete e connettività |
| `printers_and_labeling` | Stampanti ed etichettatura |
| `telephony` | Telefonia |
| `retail_systems` | Sistemi di negozio |
| `production_systems` | Sistemi produttivi |
| `information_security` | Sicurezza informatica |
| `other_requests` | Altre richieste |

## Stati del ticket

Gli stati descrivono un ticket già creato. Una richiesta non confermata non è ancora un
ticket e quindi non ha uno stato in questo elenco.

| Valore interno | Etichetta italiana | Significato |
| --- | --- | --- |
| `new` | Nuovo | Il ticket è stato creato e deve ancora essere preso in carico. |
| `in_progress` | In lavorazione | Un tecnico sta analizzando o gestendo il ticket. |
| `waiting_for_requester` | In attesa del richiedente | Servono informazioni o una conferma dal dipendente. |
| `waiting_for_vendor` | In attesa del fornitore | Il lavoro dipende da un fornitore esterno simulato. |
| `resolved` | Risolto | È stata applicata una soluzione, in attesa della chiusura. |
| `closed` | Chiuso | Il lavoro sul ticket è terminato. |

Le regole che stabiliscono quali passaggi tra stati sono consentiti verranno definite
insieme alla gestione tecnica dei ticket; SP-010 definisce soltanto i valori ammessi.

## Impatto

L'impatto misura quanto è ampia la conseguenza operativa del problema.

| Valore interno | Etichetta italiana | Esempio indicativo |
| --- | --- | --- |
| `low` | Basso | Una sola persona, attività non essenziale o alternativa disponibile. |
| `medium` | Medio | Più persone o un servizio importante degradato. |
| `high` | Alto | Un'intera sede o un processo critico è bloccato. |

## Urgenza

L'urgenza misura quanto rapidamente è necessario intervenire.

| Valore interno | Etichetta italiana | Esempio indicativo |
| --- | --- | --- |
| `low` | Bassa | Attività informativa o pianificabile. |
| `medium` | Media | Il lavoro è limitato, ma esiste una soluzione temporanea. |
| `high` | Alta | Il lavoro non può proseguire e non esiste un'alternativa. |

## Priorità

| Valore interno | Etichetta italiana | Significato generale |
| --- | --- | --- |
| `p1` | P1 - Critica | Intervento immediato su un blocco esteso o critico. |
| `p2` | P2 - Alta | Servizio essenziale bloccato con impatto rilevante. |
| `p3` | P3 - Media | Problema con impatto lavorativo ma gestibile temporaneamente. |
| `p4` | P4 - Bassa | Richiesta informativa o attività pianificabile. |

La priorità non viene scelta liberamente dall'AI. Il backend usa la seguente matrice
deterministica, implementata in `app/domain/priority.py`:

| Impatto / Urgenza | Bassa | Media | Alta |
| --- | --- | --- | --- |
| Basso | P4 | P4 | P3 |
| Medio | P4 | P3 | P2 |
| Alto | P3 | P2 | P1 |

Esempi collegati alla specifica:

- impatto alto e urgenza alta producono P1 per un blocco esteso e immediato;
- impatto medio e urgenza alta producono P2 per un servizio essenziale bloccato;
- impatto medio e urgenza media producono P3 per un problema lavorativo gestibile
  temporaneamente;
- impatto basso e urgenza bassa producono P4 per una richiesta pianificabile.

Prima del calcolo, impatto e urgenza devono essere convertiti nei valori controllati del
vocabolario. La funzione rifiuta testi liberi e non consulta né AI né database.
