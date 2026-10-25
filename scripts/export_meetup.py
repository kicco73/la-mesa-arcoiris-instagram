#!/usr/bin/env python3
"""Esporta tutti gli eventi (passati e futuri) del gruppo Meetup in data/events.json.

Usa l'endpoint GraphQL pubblico di Meetup: non serve login.
"""
import json
import pathlib
import requests

URLNAME = "la-mesa-arcoiris"
ENDPOINT = "https://www.meetup.com/gql2"
FIELDS = """
  id title dateTime endTime eventUrl description
  venue { name address city }
  featuredEventPhoto { id highResUrl }
  rsvps { totalCount }
  photoAlbum { id photoCount photoSample { id highResUrl } }
"""
QUERY = """
query($u: String!, $a: String) {
  groupByUrlname(urlname: $u) {
    events(status: %s, first: 50, after: $a) {
      pageInfo { hasNextPage endCursor }
      edges { node { %s } }
    }
  }
}
"""


def fetch(status: str) -> list[dict]:
    events, after = [], None
    while True:
        r = requests.post(
            ENDPOINT,
            json={"query": QUERY % (status, FIELDS), "variables": {"u": URLNAME, "a": after}},
            headers={"user-agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        if body.get("errors"):
            raise RuntimeError(body["errors"])
        page = body["data"]["groupByUrlname"]["events"]
        events += [e["node"] for e in page["edges"]]
        if not page["pageInfo"]["hasNextPage"]:
            return events
        after = page["pageInfo"]["endCursor"]


def main() -> None:
    events = fetch("PAST") + fetch("ACTIVE")
    out = pathlib.Path(__file__).resolve().parent.parent / "data" / "events.json"
    out.write_text(json.dumps(events, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(events)} eventi esportati in {out}")


if __name__ == "__main__":
    main()
