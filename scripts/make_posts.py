#!/usr/bin/env python3
"""Genera data/posts.json: un post per evento passato, con didascalia e lista foto.

Da eseguire una sola volta: dopo la generazione posts.json è la fonte di verità
e si modifica direttamente (didascalie, foto, approvazione).
"""
import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHOTO_BASE = "https://secure.meetupstatic.com/photos/event/"
EXCLUDED = {"317133581"}  # "Nos mudamos a Instagram": è l'annuncio del passaggio stesso
# date errate su Meetup (il titolo indica il giorno reale)
DATE_FIX = {"313001782": "2026-03-12T21:00:00+01:00"}

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CTA = [
    "¿Te apuntas a la próxima? Síguenos para no perderte ningún encuentro 🌈",
    "¿Quieres venir la próxima vez? Síguenos y entérate de los próximos planes 🌈",
    "La próxima puede ser contigo: síguenos para estar al día de los encuentros 🌈",
    "¿Te unes? Síguenos y te contamos el próximo plan 🌈",
]
BASE_TAGS = "#LaMesaArcoiris #GayBarcelona #AmigosGays #BarcelonaLGBT #QuedadasBarcelona"

# categoria -> (emoji, titolo, luogo, hashtag extra, [varianti di testo])
CAT = {
    "piazzetta": ("🍕", "Pizza a la Napoletana en La Piazzetta",
                  "La Piazzetta · Carrer d'Enric Granados 48, Eixample", "#PizzaNapoletana #PizzaBarcelona", [
        "Una noche más en nuestra pizzería favorita. Masa napolitana de verdad, buena conversación y muchas risas alrededor de la mesa.",
        "Jueves de pizza napoletana en La Piazzetta: caras conocidas, caras nuevas y la misma buena energía de siempre.",
        "Hay planes que no fallan, y la pizza napolitana en La Piazzetta es uno de ellos. Gracias a todos los que vinisteis.",
        "Horno de leña, pizzas para compartir y una mesa llena de amigos. Así son nuestras noches en La Piazzetta.",
        "Volvimos a La Piazzetta y volvimos a salir felices. Pizza, charla y buen rollo para cerrar el día.",
        "Nuestra cita fija con la pizza napoletana. Gente nueva que se sienta a la mesa y sale con nuevos amigos.",
        "Otra noche de pizza en La Piazzetta. Sencillo, cercano y siempre divertido: así nos gusta conocernos.",
        "Margherita, diavola o lo que te pida el cuerpo: lo importante es compartir mesa y risas. ¡Gracias por venir!",
    ]),
    "piazzetta_gv": ("🍕", "Pizza a la Napoletana en La Piazzetta Gran Via",
                     "La Piazzetta · Gran Via de les Corts Catalanes 566", "#PizzaNapoletana #PizzaBarcelona", [
        "Esta vez cambiamos de sede y probamos La Piazzetta de Gran Via. Misma pizza napolitana, mismo buen ambiente y nuevas caras en la mesa.",
    ]),
    "romana": ("🍕", "Pizza a la Romana en Le Romane",
               "Le Romane · Carrer de Muntaner 103, Eixample", "#PizzaRomana #PizzaBarcelona", [
        "Pizza al estilo romano para compartir: cada uno eligió dos sabores y probamos de todo. La mejor manera de romper el hielo.",
        "Volvimos a Le Romane a por pizza al taglio. Muchos sabores, muchas risas y una mesa que no paraba de hablar.",
    ]),
    "lapala": ("🍕", "Pizza a la Romana en La Pala",
               "La Pala Pizza Bar · Av. del Paral·lel 126", "#PizzaRomana #PizzaBarcelona", [
        "Noche de pizza a la romana en el Paral·lel, compartiendo sabores y buena conversación. Pequeño grupo, gran ambiente.",
    ]),
    "bloc34": ("🍸", "Tomamos algo en Bloc 34",
               "Bloc 34 · Carrer de la Perla 34, Gràcia", "#Gracia #BarcelonaBares", [
        "Empezamos la noche con algo de beber en Bloc 34, un clásico de Gràcia. Primeras presentaciones, risas y luego todos a cenar.",
    ]),
    "aperegina": ("🍝", "Cena italiana en Ape Regina",
                  "Restaurante Ape Regina · Carrer de Bruniquer 26", "#CocinaItaliana #RestaurantesBarcelona", [
        "Cena italiana en Ape Regina: pasta, buen vino y una mesa llena de conversación. Una noche de las que dejan ganas de repetir.",
        "Repetimos en Ape Regina, y con la mesa llena. Cocina italiana, buen ambiente y amistades que se van consolidando.",
    ]),
    "abasto": ("🥩", "Empanadas y solomillos en El Abasto",
               "El Abasto · Carrer del Doctor Trueta 229, Poblenou", "#CocinaArgentina #RestaurantesBarcelona", [
        "Noche argentina en el Poblenou: empanadas, solomillo y sobremesa larga. Comer bien y conocerse mejor.",
    ]),
    "fiorito": ("🥩", "Empanadas y solomillos en El Fiorito",
                "El Fiorito · Carrer de Rocafort 29, Sant Antoni", "#CocinaArgentina #RestaurantesBarcelona", [
        "Volvimos a la cocina argentina, esta vez en El Fiorito de Sant Antoni. Empanadas, carne a la brasa y muy buena compañía.",
    ]),
    "federica": ("🍸", "Tomamos algo en La Federica",
                 "La Federica · Carrer de la Salvà 3, Poble-sec", "#PobleSec #BarcelonaBares", [
        "Aperitivo en La Federica, bar gay icónico del Poble-sec. Diez personas, muchas presentaciones y luego a cenar juntos.",
        "Otra vez en La Federica para abrir la noche. Copas, risas y un grupo que cada vez se conoce mejor.",
    ]),
    "delias": ("🫒", "Cena griega en D'Elias",
               "D'Elias · Carrer de Vallhonrat 19, Poble-sec", "#CocinaGriega #RestaurantesBarcelona", [
        "Viajamos a Grecia sin salir del Poble-sec: mezze para compartir, sabores mediterráneos y una mesa muy animada.",
        "Volvimos a D'Elias a por más cocina griega. Platos para compartir y conversación hasta tarde.",
    ]),
    "tootsie": ("🎭", "Tootsie, el musical",
                "Teatro Apolo · Carrer Nou de la Rambla 113", "#Musical #TeatroBarcelona", [
        "Domingo de teatro: fuimos juntos a ver Tootsie en el Apolo. Risas, música y un plan diferente para seguir conociéndonos.",
    ]),
    "maroazul": ("🌮", "Cena mexicana en Maro Azul",
                 "Maro Azul · Carrer de Roger de Flor 218, Eixample", "#CocinaMexicana #RestaurantesBarcelona", [
        "Cena mexicana en Maro Azul para combatir el primer frío. Tacos, picante y una mesa grande llena de buen rollo.",
    ]),
    "pummarola": ("🍹", "AperiPizza: pizza y spritz en Pummarola",
                  "Pummarola · Ronda de Sant Pau 59, Sant Antoni", "#Spritz #PizzaBarcelona", [
        "Apericena a la italiana en Pummarola: margherita, spritz y charla sin prisa. Y la noche siguió en Lo de Carmen.",
        "Volvió la AperiPizza: pizza margherita, un spritz bien frío y mucha gente con ganas de conocerse.",
        "Pizza y spritz en Sant Antoni, el plan perfecto para empezar el fin de semana entre amigos.",
        "Otra AperiPizza en Pummarola. Masa napolitana, aperitivo italiano y risas de principio a fin.",
        "La AperiPizza de vuelta tras el verano, ¡y con la mesa llena! Gracias a todos por venir.",
    ]),
    "lodecarmen": ("🍸", "Tomamos algo en Lo de Carmen",
                   "Lo de Carmen · Av. del Paral·lel 104", "#Paralelo #BarcelonaBares", [
        "La noche siguió en Lo de Carmen, bar icónico del Paral·lel. De pie en la barra, con música y buena compañía.",
        "Copas en Lo de Carmen para conocernos un poco más. Ambiente queer, buena música y muchas risas.",
        "Volvimos a Lo de Carmen para cerrar la noche como se merece: copas, charla y algún baile.",
    ]),
    "boxer": ("🍸", "Tomamos algo en Boxer",
              "Boxer Café · Carrer de la Diputació 167, Eixample", "#Gayxample #BarcelonaBares", [
        "Aperitivo en Boxer, en pleno Gayxample. Primeras copas, presentaciones y luego a cenar todos juntos.",
        "Arrancamos la noche en Boxer. Un bar que ya es casa para el grupo y siempre trae caras nuevas.",
        "Otra tarde en Boxer: una copa, buena conversación y ganas de seguir la noche.",
        "Volvimos a Boxer para tomar algo antes de cenar. Pocos planes son tan sencillos y tan buenos.",
        "Copas en Boxer y nuevas amistades. Gracias a los que os acercasteis por primera vez.",
    ]),
    "navidad": ("🎄", "Cena de Navidad en Foz",
                "Restaurante Foz · Carrer de la Diputació 164, Eixample", "#Navidad #CenaDeNavidad", [
        "Celebramos la Navidad juntos con cena en Foz y un amigo invisible lleno de sorpresas. Gracias por hacer tan especiales estos primeros meses del grupo.",
    ]),
    "foz": ("🍽️", "Cena en Foz",
            "Restaurante Foz · Carrer de la Diputació 164, Eixample", "#CocinaFusion #RestaurantesBarcelona", [
        "Volvimos a Foz, donde celebramos la Navidad. Cocina fusión, mesa íntima y conversación de las buenas.",
    ]),
    "bardaixa": ("🍸", "Tomamos algo en Bardaixa",
                 "Bardaixa · Carrer del Parlament 12, Sant Antoni", "#SantAntoni #BarcelonaBares", [
        "Primer encuentro del año en Bardaixa, en Sant Antoni. Copas, propósitos de año nuevo y luego a cenar.",
        "Tardeo en Bardaixa para empezar mayo. Terraceo, buena compañía y ganas de verano.",
    ]),
    "mangarosa": ("🇧🇷", "Cena brasileña en Manga Rosa",
                  "Manga Rosa · Carrer de Floridablanca 150, Sant Antoni", "#CocinaBrasileña #RestaurantesBarcelona", [
        "Sabores de Brasil para espantar el frío de enero: cena en Manga Rosa con una mesa llena de energía.",
    ]),
    "lacarra": ("🍸", "Tomamos algo en La Carrà",
                "La Carrà · Carrer de Muntaner 34, Eixample", "#Gayxample #BarcelonaBares", [
        "Aperitivo en La Carrà, en el corazón del Gayxample. Brindis, presentaciones y luego a cenar.",
    ]),
    "outofchina": ("🥢", "Cena en Out of China",
                   "Out of China · Carrer d'Aribau 112, Eixample", "#CocinaChina #RestaurantesBarcelona", [
        "Cena en Out of China, un clásico del Eixample, con opciones para todos. Platos al centro y conversación sin fin.",
    ]),
    "elephanta": ("🍸", "Tomamos algo en Elephanta",
                  "Elephanta · Carrer del Torrent d'en Vidalet 37, Gràcia", "#Gracia #BarcelonaBares", [
        "Cócteles en Elephanta, en la Vila de Gràcia, antes de la cena. Un rincón con encanto para conocernos.",
    ]),
    "leggenda": ("🍕", "Tardeo y pizza con Gay Meeting Point",
                 "La Leggenda di Napoli · Carrer del Bruc 55, Eixample", "#PizzaNapoletana #GayMeetingPoint", [
        "Unimos fuerzas con Gay Meeting Point: tardeo en Veridis Quo y luego pizza napolitana en La Leggenda di Napoli. Dos grupos, una gran mesa.",
    ]),
    "phohanoi": ("🍜", "Cena vietnamita en Pho Ha Noi",
                 "Pho Ha Noi · Carrer de la Diputació 218, Eixample", "#CocinaVietnamita #RestaurantesBarcelona", [
        "Despedimos el invierno con un buen pho en Pho Ha Noi. Sabores de Vietnam y una mesa muy bien avenida.",
    ]),
    "bocachancla": ("🥘", "Tapeo en Bocachancla",
                    "Bocachancla · Carrer de la Diputació 77, Eixample", "#Tapas #RestaurantesBarcelona", [
        "Tapeo de calidad en Bocachancla: platos para compartir, buen vino y una noche redonda.",
        "Volvimos a Bocachancla porque nos encantó. Tapas, raciones y risas hasta el cierre.",
        "Último tapeo antes del verano en Bocachancla. Gracias por una temporada llena de buenos momentos.",
    ]),
    "rioja": ("🍷", "La Rioja Pasión en Logroño",
              "Calle del Laurel · Logroño", "#LaRiojaPasion #Logroño #RiojaGayFriendly", [
        "Nos fuimos de viaje a la tercera edición de La Rioja Pasión: ruta de pinchos por la calle Laurel, cata de vermut, visita al Museo de La Rioja y una noche temática inolvidable. Gracias a Rioja GayFriendly y GayLur por la organización.",
    ]),
}


def category(e) -> str:
    title, venue = e[1].lower(), (e[5][0] if e[5] else "").lower()
    rules = [
        ("rioja", "rioja"), ("navidad", "navidad"), ("tootsie", "tootsie"),
        ("leggenda", "leggenda"), ("gran vis", "piazzetta_gv"), ("piazzetta", "piazzetta"),
        ("le romane", "romana"), ("la pala", "lapala"), ("bloc 34", "bloc34"),
        ("ape regina", "aperegina"), ("abasto", "abasto"), ("fiorito", "fiorito"),
        ("federica", "federica"), ("d'elias", "delias"), ("maro azul", "maroazul"),
        ("pummarola", "pummarola"), ("lo de carmen", "lodecarmen"), ("boxer", "boxer"),
        ("foz", "foz"), ("bardaixa", "bardaixa"), ("manga rosa", "mangarosa"),
        ("lacarr", "lacarra"), ("out of china", "outofchina"), ("elephanta", "elephanta"),
        ("pho ha noi", "phohanoi"), ("bocachancla", "bocachancla"),
    ]
    hay = title + " | " + venue
    for key, cat in rules:
        if key in hay:
            return cat
    raise ValueError(f"categoria non trovata: {e[1]} / {venue}")


def fecha(e) -> str:
    start = dt.datetime.fromisoformat(DATE_FIX.get(e[0], e[2]))
    end = dt.datetime.fromisoformat(e[3])
    if end.date() > start.date() and (end - start).days >= 1:
        return f"Del {start.day} al {end.day} de {MESES[end.month - 1]} de {end.year}"
    return f"{DIAS[start.weekday()].capitalize()} {start.day} de {MESES[start.month - 1]} de {start.year}"


def main() -> None:
    events = [e for e in json.loads((ROOT / "data/events_min.json").read_text()) if e[0] not in EXCLUDED]
    events.sort(key=lambda e: e[2])

    # pool di foto d'album per categoria, per variare i post senza foto proprie
    pools: dict[str, list[str]] = {}
    for e in events:
        for p in e[8]:
            pool = pools.setdefault(category(e), [])
            if p not in pool and p != e[6]:
                pool.append(p)

    seen: dict[str, int] = {}
    last_cover: dict[str, str] = {}
    posts = []
    for n, e in enumerate(events):
        cat = category(e)
        k = seen.get(cat, 0)
        seen[cat] = k + 1
        emoji, title, place, tags, variants = CAT[cat]

        own = [p for p in e[8] if p != e[6]]
        photos: list[dict] = [{"src": PHOTO_BASE + p, "fit": "cover"} for p in own]
        if not own and pools.get(cat):
            # foto prese da un'altra data nello stesso locale, a rotazione
            pool = pools[cat]
            pick = pool[k % len(pool)]
            if pick == last_cover.get(cat) and len(pool) > 1:
                pick = pool[(k + 1) % len(pool)]
            last_cover[cat] = pick
            photos.append({"src": PHOTO_BASE + pick, "fit": "cover", "borrowed": True})
        if e[6]:
            photos.append({"src": PHOTO_BASE + e[6], "fit": "contain"})

        caption = "\n".join([
            f"{emoji} {title}",
            "",
            variants[k % len(variants)],
            "",
            f"📍 {place}",
            f"🗓️ {fecha(e)}",
            "",
            CTA[n % len(CTA)],
            "",
            f"{BASE_TAGS} {tags}",
        ])
        posts.append({
            "id": e[0],
            "order": n + 1,
            "meetup_url": f"https://www.meetup.com/la-mesa-arcoiris/events/{e[0]}/",
            "event_title": e[1].strip(),
            "event_date": e[2],
            "caption": caption,
            "photos": photos,
            "approved": False,
            "status": "pending",
            "ig_media_id": None,
        })

    out = ROOT / "data/posts.json"
    out.write_text(json.dumps(posts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(posts)} post scritti in {out}")


if __name__ == "__main__":
    main()
