# Suggerimenti tecnici con fonti

Il percorso RAG di ServicePilot recupera passaggi pertinenti, chiede a Gemini un
suggerimento tecnico e conserva le fonti realmente citate. Una soglia prudenziale
ferma la generazione quando le fonti non sono abbastanza solide. Il risultato assiste
il tecnico ma non modifica automaticamente il ticket.

## Quale problema risolve

La ricerca semantica mostra testo utile, ma richiederebbe al tecnico di riunire i
passaggi in una proposta operativa. Il generatore produce una prima sintesi
verificabile e mantiene sempre accessibili i testi originali da cui deriva.

## Quali dati riceve

La ricerca riceve titolo, descrizione, servizio e sottocategoria del ticket. Gemini
riceve il contesto del ticket e al massimo tre passaggi recuperati, ciascuno con:

- identificativo assegnato dal backend;
- nome del documento;
- sezione o pagina;
- testo originale.

Ticket e procedure sono trattati come dati non affidabili: eventuali istruzioni al loro
interno non possono sostituire l'istruzione di sistema.

## Dove vengono controllati

La risposta deve rispettare uno schema chiuso con un suggerimento tra 20 e 4.000
caratteri e da uno a tre identificativi di fonte, positivi e non duplicati. Il backend
rifiuta l'intero risultato se Gemini cita un identificativo che non appartiene ai
passaggi recuperati.

Prima di chiamare Gemini, il backend conserva soltanto i passaggi con similarità del
coseno pari o superiore a `0,55`. Se non rimane alcun passaggio, la generazione si ferma.
La soglia è un limite prudenziale iniziale, non una percentuale di certezza: dovrà essere
ricalibrata in futuro con un insieme più ampio di domande e procedure dimostrative.

Le fonti sotto soglia non vengono inviate al modello. Questo riduce sia il rischio di una
risposta basata su contenuti vaghi sia il consumo inutile di una chiamata Gemini.

## Dove vengono salvati

Il ticket conserva testo suggerito, stato, eventuale errore e data di generazione. La
tabella `ticket_solution_sources` collega il ticket ai segmenti citati, conservandone
ordine e punteggio di similarità. Testo e collegamenti vengono salvati insieme: non può
rimanere una soluzione parziale senza le proprie fonti.

Se un documento viene rielaborato e i suoi segmenti cambiano, i suggerimenti che li
citavano tornano automaticamente allo stato `pending` per evitare riferimenti obsoleti.

Quando le fonti mancano o sono tutte sotto soglia, il ticket conserva lo stato
controllato `unavailable` e un messaggio che spiega al tecnico se deve indicizzare una
procedura, verificare i dettagli della richiesta o aggiungere documentazione più
specifica. Un eventuale vecchio suggerimento e le sue citazioni vengono rimossi.

## Cosa può andare storto

- ricerca o embedding non disponibili: il ticket resta utilizzabile e mostra un errore;
- nessun documento indicizzato: non viene salvato alcun suggerimento;
- risultati tutti sotto `0,55`: Gemini non viene chiamato e il tecnico riceve indicazioni;
- risposta AI non valida o fonte inventata: l'intero risultato viene rifiutato;
- errore del database: suggerimento e fonti non vengono salvati parzialmente;
- procedura rielaborata: il suggerimento collegato viene invalidato.

## Chi può usare la funzionalità

Tecnico e amministratore possono generare o rigenerare il suggerimento dalla pagina del
ticket. Il dipendente non può avviare la generazione. Il testo resta separato dalla
soluzione finale e non cambia stato, assegnazione o classificazione.

## Quale test dimostra che funziona

- una domanda VPN recupera il passaggio previsto e salva soltanto la fonte citata;
- una ricerca senza risultati si ferma prima di chiamare il modello;
- una ricerca con sole fonti sotto soglia si ferma e mostra il motivo al tecnico;
- una fonte forte viene inviata al modello senza includere i risultati deboli;
- un identificativo di fonte inventato viene rifiutato;
- timeout e risposte non valide lasciano il ticket utilizzabile;
- la rielaborazione di un documento invalida i suggerimenti collegati;
- il tecnico vede suggerimento, documento, sezione e passaggio originale;
- il dipendente non può avviare la generazione;
- la soluzione finale del tecnico resta vuota finché non viene compilata manualmente;
- tutti i test usano adapter finti e non consumano chiamate Gemini.
