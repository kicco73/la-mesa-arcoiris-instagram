# La Mesa Arcoíris → Instagram

Pubblica su @la.mesa.arcoiris un post per ogni evento Meetup del gruppo, uno al giorno.

## Come funziona
- `data/posts.json`: coda dei post (didascalia, foto, `approved`, `status`). È la fonte di verità: si modifica qui.
- `build.yml`: a ogni modifica di `posts.json` scarica le foto da Meetup e genera `images/<id>/<n>.jpg` (1080×1350).
- `publish.yml`: ogni giorno alle 20:40 (Madrid, ora legale gestita) pubblica il prossimo post con `approved: true` e `status: pending`. Avviato a mano, di default fa solo un controllo (dry-run).

## Highlight
- `data/highlights.json`: un highlight per locale (titolo, foto, `approved`, `status`).
- `stories/<locale>/`: `0.jpg` storia di apertura, `<n>.jpg` foto, `cover.jpg` copertina.
- `stories.yml` (avvio manuale): pubblica come storie gli highlight approvati, fino a 40 storie per esecuzione. Poi in app: Profilo → + → Highlight, scegliendo le storie dall'archivio (l'API non crea highlight).

## Configurazione
1. Account Instagram professionale (Creator), Instagram Tester dell'app Meta "Avance" (Instagram app "Avance-IG").
2. Permesso `instagram_business_content_publish`; redirect URL della business login: l'URL di questo repository.
3. Secret del repository `IG_APP_SECRET` = Instagram app secret.
4. Autorizzazione: aprire il link OAuth, copiare l'URL di ritorno (`?code=...`) e avviare `auth.yml` con quell'URL.
   Il token (60 giorni) viene salvato cifrato in `data/token.enc` con l'app secret come chiave.
5. `refresh-token.yml` lo rinnova il 1° e il 15 di ogni mese.

## Archivio Meetup
L'account Meetup verrà chiuso: tutto è salvato qui.
- `data/events.json`: tutti gli eventi con descrizioni complete, luoghi, partecipanti (conteggio) e link alle foto.
- `data/group_album.json`: elenco dell'album del gruppo.
- `archive/photos/<id>.jpeg`: tutte le foto originali (copertine, album degli eventi, album del gruppo); `index.json` dice da dove viene ciascuna.

## Script
- `scripts/export_meetup.py`: export completo degli eventi in `data/events.json`.
- `scripts/make_posts.py`: generazione iniziale di `posts.json` (da non rieseguire: sovrascrive le modifiche).
- `scripts/archive_meetup.py`: download delle foto originali in `archive/photos`.
- `scripts/build_images.py`: conversione immagini (legge le foto dall'archivio).
- `scripts/publish.py`: pubblicazione.
