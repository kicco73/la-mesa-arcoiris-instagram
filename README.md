# La Mesa Arcoíris → Instagram

Pubblica su @la.mesa.arcoiris un post per ogni evento Meetup del gruppo, uno al giorno.

## Come funziona
- `data/posts.json`: coda dei post (didascalia, foto, `approved`, `status`). È la fonte di verità: si modifica qui.
- `build.yml`: a ogni modifica di `posts.json` scarica le foto da Meetup e genera `images/<id>/<n>.jpg` (1080×1350).
- `publish.yml`: ogni giorno alle 19:30 (Madrid, ora legale gestita) pubblica il prossimo post con `approved: true` e `status: pending`. Avviato a mano, di default fa solo un controllo (dry-run).

## Configurazione
1. Account Instagram professionale (Creator).
2. App Meta con "Instagram API with Instagram Login", permesso `instagram_business_content_publish`; token di lunga durata.
3. Secret del repository `IG_ACCESS_TOKEN` con il token.

Il token di lunga durata scade dopo 60 giorni.

## Script
- `scripts/export_meetup.py`: export completo degli eventi in `data/events.json`.
- `scripts/make_posts.py`: generazione iniziale di `posts.json` (da non rieseguire: sovrascrive le modifiche).
- `scripts/build_images.py`: conversione immagini.
- `scripts/publish.py`: pubblicazione.
