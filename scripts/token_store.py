#!/usr/bin/env python3
"""Gestione del token Instagram, salvato cifrato in data/token.enc.

La chiave di cifratura è l'app secret (secret GitHub IG_APP_SECRET): il token non
compare mai in chiaro né nel repository né nei log.

  python scripts/token_store.py auth <code o URL di ritorno>   codice OAuth -> token 60 giorni
  python scripts/token_store.py refresh                        prolunga il token di 60 giorni
  python scripts/token_store.py print                          stampa il token (solo per i workflow)
"""
import os
import pathlib
import subprocess
import sys
import urllib.parse

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / "data" / "token.enc"
CLIENT_ID = "995699106147176"  # Instagram app ID di Avance-IG (pubblico)
REDIRECT_URI = "https://github.com/kicco73/la-mesa-arcoiris-instagram"


def _openssl(args: list[str], data: bytes) -> bytes:
    secret = os.environ["IG_APP_SECRET"]
    out = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-a", "-A", *args,
         "-pass", "env:IG_APP_SECRET"],
        input=data, capture_output=True, check=True, env={**os.environ, "IG_APP_SECRET": secret},
    )
    return out.stdout


def save(token: str) -> None:
    TOKEN_FILE.write_bytes(_openssl([], token.encode()) + b"\n")


def load() -> str:
    return _openssl(["-d"], TOKEN_FILE.read_bytes().strip()).decode()


def _check(r: requests.Response, what: str) -> dict:
    body = r.json()
    if r.status_code >= 400 or "access_token" not in body:
        # niente token nei log: solo il messaggio d'errore di Meta
        raise SystemExit(f"{what} non riuscito: {body.get('error_message') or body.get('error') or r.status_code}")
    return body


def auth(code_or_url: str) -> None:
    code = code_or_url.strip()
    if code.startswith("http"):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(code).query)["code"][0]
    code = code.removesuffix("#_")
    short = _check(requests.post("https://api.instagram.com/oauth/access_token", data={
        "client_id": CLIENT_ID,
        "client_secret": os.environ["IG_APP_SECRET"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }, timeout=30), "Scambio del codice")
    long = _check(requests.get("https://graph.instagram.com/access_token", params={
        "grant_type": "ig_exchange_token",
        "client_secret": os.environ["IG_APP_SECRET"],
        "access_token": short["access_token"],
    }, timeout=30), "Token di lunga durata")
    save(long["access_token"])
    print(f"Token salvato, scade tra {long.get('expires_in', 0) // 86400} giorni.")


def refresh() -> None:
    body = _check(requests.get("https://graph.instagram.com/refresh_access_token", params={
        "grant_type": "ig_refresh_token",
        "access_token": load(),
    }, timeout=30), "Rinnovo del token")
    save(body["access_token"])
    print(f"Token rinnovato, scade tra {body.get('expires_in', 0) // 86400} giorni.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "auth":
        auth(sys.argv[2])
    elif cmd == "refresh":
        refresh()
    elif cmd == "print":
        sys.stdout.write(load())
    else:
        raise SystemExit(__doc__)
