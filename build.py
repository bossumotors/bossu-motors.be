#!/usr/bin/env python3
"""
Bossu Motors - website-generator.

Leest de voorraad (Google Sheet als CSV, of het lokale bestand voorraad.csv)
en maakt een volledige statische website in de map  dist/  :
  - startpagina met alle wagens (NL + FR)
  - een aparte pagina per wagen (goed voor Google)
  - sitemap.xml, robots.txt, gestructureerde gegevens (schema.org)

Gebruik:
    python build.py                      # leest voorraad.csv
    SHEET_CSV_URL=https://... python build.py
    DOWNLOAD_PHOTOS=1 python build.py    # foto's lokaal opslaan (aanrader online)
"""
import csv, html, io, json, os, re, shutil, sys, unicodedata, urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
DIST = os.path.join(ROOT, "dist")
CACHE = os.path.join(ROOT, ".fotocache")
SITE = CONFIG["site_url"].rstrip("/")
TODAY = date.today().isoformat()

# --------------------------------------------------------------------------- vertalingen
T = {
    "nl": dict(
        lang="nl-BE", home="/", car_dir="wagen", stock="Onze voorraad", all="Alle merken",
        allfuel="Alle brandstoffen", sort="Sorteren", s_new="Nieuwste eerst", s_low="Prijs laag-hoog",
        s_high="Prijs hoog-laag", s_km="Minste km", year="Bouwjaar", km="Kilometerstand", fuel="Brandstof",
        gear="Transmissie", color="Kleur", cc="Motorinhoud", power="Vermogen", reg="1e inschrijving",
        vat="Btw aftrekbaar", yes="Ja", price="Prijs", options="Uitrusting & opties",
        desc="Beschrijving", call="Bel ons", whatsapp="WhatsApp", back="Terug naar de voorraad",
        cars_n="{n} wagens beschikbaar", none="Geen wagens gevonden met deze filters.",
        contact="Contact & bezoek", route="Route plannen", hours="Openingsuren",
        more="Bekijk wagen", interest="Interesse in deze wagen?",
        interest_txt="Bel of stuur een WhatsApp-bericht voor meer info, een proefrit of een inruilvoorstel.",
        why=[("Garantie", "Al onze wagens worden verkocht met garantie."),
             ("Onderhoud & keuring", "Volledig nagekeken, onderhouden en gekeurd voor aflevering."),
             ("Inruil mogelijk", "Uw huidige wagen inruilen? Vraag gerust een voorstel."),
             ("Btw aftrekbaar", "Ruim aanbod bedrijfswagens en wagens met aftrekbare btw.")],
        hero_h="Jonge tweedehandswagens in Zarren",
        hero_p="Ruim aanbod van Audi, BMW, Ford, Mercedes-Benz, Škoda, Volkswagen en meer - nagekeken, onderhouden en met garantie.",
        hero_cta="Bekijk de voorraad",
        meta_home="Bossu Motors in Zarren (Kortemark): ruim aanbod jonge tweedehandswagens en bedrijfswagens met garantie, onderhoud en keuring. Bekijk onze actuele voorraad.",
        title_home="Bossu Motors - Tweedehandswagens Zarren | Garantie & keuring",
        car_title="{car} tweedehands te koop in Zarren | Bossu Motors",
        car_meta="{car} ({year}, {km}) te koop bij Bossu Motors in Zarren voor {price}. Met garantie, onderhoud en keuring. Bel {phone}.",
        photos="Foto's", other="Taal: ", switch="Français", vat_note="btw aftrekbaar",
        price_incl="", wa_msg="Hallo, ik heb interesse in de {car} ({price}) op uw website: {url}",
        sold_note="", footer="Alle prijzen onder voorbehoud van verkoop en tikfouten.",
    ),
    "fr": dict(
        lang="fr-BE", home="/fr/", car_dir="voiture", stock="Notre stock", all="Toutes les marques",
        allfuel="Tous les carburants", sort="Trier", s_new="Les plus récentes", s_low="Prix croissant",
        s_high="Prix décroissant", s_km="Moins de km", year="Année", km="Kilométrage", fuel="Carburant",
        gear="Transmission", color="Couleur", cc="Cylindrée", power="Puissance", reg="1re immatriculation",
        vat="TVA déductible", yes="Oui", price="Prix", options="Équipements & options",
        desc="Description", call="Appelez-nous", whatsapp="WhatsApp", back="Retour au stock",
        cars_n="{n} voitures disponibles", none="Aucune voiture ne correspond à ces filtres.",
        contact="Contact & visite", route="Itinéraire", hours="Heures d'ouverture",
        more="Voir la voiture", interest="Cette voiture vous intéresse ?",
        interest_txt="Appelez-nous ou envoyez un message WhatsApp pour plus d'infos, un essai ou une reprise.",
        why=[("Garantie", "Toutes nos voitures sont vendues avec garantie."),
             ("Entretien & contrôle", "Entièrement vérifiées, entretenues et contrôle technique avant livraison."),
             ("Reprise possible", "Vous voulez faire reprendre votre voiture ? Demandez-nous une offre."),
             ("TVA déductible", "Large choix d'utilitaires et de voitures avec TVA déductible.")],
        hero_h="Voitures d'occasion récentes à Zarren",
        hero_p="Large choix d'Audi, BMW, Ford, Mercedes-Benz, Škoda, Volkswagen et plus - contrôlées, entretenues et avec garantie.",
        hero_cta="Voir le stock",
        meta_home="Bossu Motors à Zarren (Kortemark) : large choix de voitures d'occasion récentes et d'utilitaires avec garantie, entretien et contrôle technique. Découvrez notre stock.",
        title_home="Bossu Motors - Voitures d'occasion Zarren | Garantie & contrôle",
        car_title="{car} d'occasion à vendre à Zarren | Bossu Motors",
        car_meta="{car} ({year}, {km}) à vendre chez Bossu Motors à Zarren pour {price}. Avec garantie, entretien et contrôle technique. Tél. {phone}.",
        photos="Photos", other="Langue : ", switch="Nederlands", vat_note="TVA déductible",
        wa_msg="Bonjour, je suis intéressé(e) par la {car} ({price}) sur votre site : {url}",
        footer="Tous les prix sous réserve de vente et d'erreurs.",
        desc_nl_note="Description complète (en néerlandais) :",
    ),
}
FUEL_FR = {"Benzine": "Essence", "Diesel": "Diesel", "Elektrisch": "Électrique", "Hybride Elektrisch/Benzine": "Hybride essence",
           "Hybride Elektrisch/Diesel": "Hybride diesel", "LPG": "LPG", "CNG": "CNG"}
GEAR_FR = {"Automaat": "Automatique", "Handgeschakeld": "Manuelle", "Semi-automaat": "Semi-automatique"}
COLOR_FR = {"Zwart": "Noir", "Wit": "Blanc", "Blauw": "Bleu", "Groen": "Vert", "Rood": "Rouge", "Grijs": "Gris",
            "Zilver of Grijs": "Gris / argent", "Zilver": "Argent", "Bruin": "Brun", "Beige": "Beige", "Geel": "Jaune", "Oranje": "Orange"}
OPT_FR = {
    "360° camera": "Caméra 360°", "Achteruitrijcamera": "Caméra de recul", "Adaptieve lichten": "Phares adaptatifs",
    "Airconditioning": "Climatisation", "Automatische klimaatregeling": "Climatisation automatique",
    "Bochtverlichting": "Éclairage en virage", "Boordcomputer": "Ordinateur de bord",
    "Centrale vergrendeling": "Verrouillage centralisé", "Climate control": "Climatronic", "Cruise Control": "Régulateur de vitesse",
    "Dakrails": "Barres de toit", "Digitale radio-ontvangst": "Radio numérique DAB+",
    "Elektrische buitenspiegels": "Rétroviseurs électriques", "Elektrische koffer": "Hayon électrique",
    "Elektrische ramen": "Vitres électriques", "Elektronische parkeerrem": "Frein de parking électrique",
    "Emergency brake assist": "Freinage d'urgence", "Grootlichtassistent": "Assistant feux de route",
    "Head-up Display": "Affichage tête haute", "Inductieladen voor smartphones": "Recharge sans fil smartphone",
    "Koplamp volledig LED": "Phares full LED", "LED dagrijverlichting": "Feux de jour LED", "LED verlichting": "Éclairage LED",
    "Lane Departure Warning": "Alerte de franchissement de ligne", "Lane Keeping Assist": "Assistant de maintien de voie",
    "Lederen bekleding": "Sellerie cuir", "Lichtmetalen velgen": "Jantes en alliage", "Lichtsensor": "Capteur de lumière",
    "Metaalkleur": "Peinture métallisée", "Mistlampen": "Antibrouillards", "Multifunctioneel stuurwiel": "Volant multifonction",
    "Navigatiesysteem": "GPS / navigation", "Panoramadak": "Toit panoramique", "Parkeerassistent": "Assistant de stationnement",
    "Parkeercamera": "Caméra de stationnement", "Parkeersensor": "Capteurs de stationnement", "Regensensor": "Capteur de pluie",
    "Skiluik": "Trappe à skis", "Sound system": "Système audio", "Sportpakket": "Pack sport", "Spraakbediening": "Commande vocale",
    "Start-stop-systeem": "Système start-stop", "Startonderbreker": "Antidémarrage", "Stuurwielverwarming": "Volant chauffant",
    "Verkeersbordherkenning": "Reconnaissance des panneaux", "Vermoeidheidsdetectie": "Détecteur de fatigue",
    "Vooruitrijcamera": "Caméra avant", "Zetelverwarming": "Sièges chauffants", "Bi-Xenon koplampen": "Phares bi-xénon",
    "Geheel digitaal combi-instrument": "Cockpit entièrement numérique", "Sportstoelen": "Sièges sport", "Trekhaak": "Crochet d'attelage",
    "Verwarmde buitenspiegels": "Rétroviseurs chauffants", "Xenon verlichting": "Éclairage xénon",
    "Adaptive Cruise Control": "Régulateur adaptatif", "Elektrische stoelverstelling": "Sièges à réglage électrique",
    "Schuifdeur": "Porte coulissante", "Dodehoekdetectie": "Détection d'angle mort", "Alarm": "Alarme",
    "Traction-control": "Antipatinage", "Keyless entry": "Accès sans clé",
}
FUEL_SCHEMA = {"Benzine": "Gasoline", "Diesel": "Diesel", "Elektrisch": "Electric",
               "Hybride Elektrisch/Benzine": "Hybrid", "Hybride Elektrisch/Diesel": "Hybrid", "LPG": "LPG"}


def tr(lang, table, v):
    return table.get(v, v) if lang == "fr" else v


def e(s):
    return html.escape(str(s), quote=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def eur(n):
    return "€ " + f"{int(n):,}".replace(",", ".")


def kmfmt(n):
    return f"{int(n):,}".replace(",", ".") + " km" if str(n).strip() else ""


def num(v):
    try:
        return int(float(str(v).replace(".", "").replace(" ", "").replace(",", ".")))
    except ValueError:
        return 0


# --------------------------------------------------------------------------- voorraad inlezen
def load_rows():
    url = os.environ.get("SHEET_CSV_URL", "").strip() or CONFIG.get("sheet_csv_url", "").strip()
    if url:
        print("Voorraad ophalen uit Google Sheet ...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bossu-site-builder)"})
        text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig")
    else:
        print("Voorraad lezen uit voorraad.csv ...")
        text = open(os.path.join(ROOT, "voorraad.csv"), encoding="utf-8-sig").read()
    cars = []
    for r in csv.DictReader(io.StringIO(text)):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        if r.get("actief", "ja").lower() in ("nee", "neen", "no", "0", "verkocht", "false"):
            continue
        if not (r.get("merk") or r.get("titel")):
            continue
        r["id"] = r.get("id") or slugify(r.get("titel", ""))[:20]
        r["prijs_n"] = num(r.get("prijs", 0))
        r["km_n"] = num(r.get("km", 0))
        r["fotos_l"] = [drive_fix(u) for u in re.split(r"[\s,;]+", r.get("fotos", "")) if u.startswith("http")]
        r["opties_l"] = [o.strip() for o in r.get("opties", "").split("|") if o.strip()]
        r["name"] = f"{r.get('merk', '')} {r.get('model', '')}".strip() or r.get("titel")
        r["slug"] = slugify(f"{r['name']} {r.get('bouwjaar', '')} {r['id']}")
        cars.append(r)
    print(f"{len(cars)} actieve wagens")
    return cars


def drive_fix(u):
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([\w-]+)", u)
    return f"https://drive.google.com/uc?export=download&id={m.group(1)}" if m else u


def fetch_photos(cars):
    """Download de foto's naar de site zelf (sneller + blijft werken als het zoekertje weg is)."""
    if os.environ.get("DOWNLOAD_PHOTOS") != "1":
        for c in cars:
            c["img"] = [(u, u) for u in c["fotos_l"]]
        return
    try:
        from PIL import Image
    except ImportError:
        Image = None
    os.makedirs(CACHE, exist_ok=True)
    for c in cars:
        c["img"] = []
        for i, u in enumerate(c["fotos_l"]):
            key = re.sub(r"[^\w]", "", u)[-60:]
            big, small = os.path.join(CACHE, key + ".jpg"), os.path.join(CACHE, key + "_t.jpg")
            try:
                if not os.path.exists(big):
                    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                    raw = urllib.request.urlopen(req, timeout=40).read()
                    if Image:
                        im = Image.open(io.BytesIO(raw)).convert("RGB")
                        im.thumbnail((1400, 1050)); im.save(big, "JPEG", quality=82, optimize=True, progressive=True)
                        im.thumbnail((640, 480)); im.save(small, "JPEG", quality=78, optimize=True, progressive=True)
                    else:
                        open(big, "wb").write(raw); shutil.copy(big, small)
                d = os.path.join(DIST, "img", c["id"])
                os.makedirs(d, exist_ok=True)
                fn = f"{c['slug'][:60]}-{i + 1}"
                shutil.copy(big, os.path.join(d, fn + ".jpg"))
                shutil.copy(small, os.path.join(d, fn + "-k.jpg"))
                c["img"].append((f"/img/{c['id']}/{fn}.jpg", f"/img/{c['id']}/{fn}-k.jpg"))
            except Exception as ex:  # foto niet bereikbaar: gebruik de originele link
                print("  foto overgeslagen:", u[:80], ex)
                c["img"].append((u, u))


# --------------------------------------------------------------------------- HTML-bouwstenen
def car_url(c, lang):
    return f"{T[lang]['home']}{T[lang]['car_dir']}/{c['slug']}/"


def head(lang, title, desc, path, alt_paths, extra="", image=None):
    image = image or f"{SITE}/assets/hero.jpg"
    if image.startswith("/"):
        image = SITE + image
    alts = "".join(f'<link rel="alternate" hreflang="{T[l]["lang"]}" href="{SITE}{p}">' for l, p in alt_paths.items())
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alt_paths["nl"]}">'
    return f"""<!doctype html>
<html lang="{T[lang]['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
{alts}
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{e(image)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:locale" content="{T[lang]['lang'].replace('-', '_')}">
<meta name="theme-color" content="#0b0b0c">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={TODAY}">
{extra}
</head>
<body>"""


def header(lang, other_path):
    t = T[lang]
    other = "fr" if lang == "nl" else "nl"
    return f"""<header class="top"><div class="wrap top-in">
<a class="brand" href="{t['home']}" aria-label="Bossu Motors"><span class="b1">BOSSU</span><span class="b2">motors</span></a>
<nav><a href="{t['home']}#voorraad">{t['stock']}</a><a href="{t['home']}#contact">{t['contact'].split(' ')[0]}</a>
<a class="lang" href="{other_path}" hreflang="{T[other]['lang']}">{'FR' if lang == 'nl' else 'NL'}</a>
<a class="btn btn-sm" href="tel:{CONFIG['phone_intl']}">{CONFIG['phone']}</a></nav>
</div></header>"""


def footer(lang):
    t = T[lang]
    c = CONFIG
    return f"""<footer class="foot"><div class="wrap foot-in">
<div><div class="brand"><span class="b1">BOSSU</span><span class="b2">motors</span></div>
<p class="muted">Your car, is our passion!</p></div>
<div><strong>{e(c['name'])}</strong><br>{e(c['street'])}<br>{e(c['postal'])} {e(c['city'])}<br>
<a href="tel:{c['phone_intl']}">{e(c['phone'])}</a>{'<br><a href="mailto:' + e(c['email']) + '">' + e(c['email']) + '</a>' if c.get('email') else ''}
{('<br>' + e(c['vat_number'])) if c.get('vat_number') else ''}</div>
<div><strong>{t['hours']}</strong><br>{'<br>'.join(e(h) for h in c['hours_text'][lang])}</div>
</div><div class="wrap muted small">© {date.today().year} {e(c['name'])} · {t['footer']}</div></footer>
<a class="wa-float" href="https://wa.me/{c['whatsapp']}" aria-label="WhatsApp" rel="noopener">{WA_SVG}</a>
</body></html>"""


WA_SVG = '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7.5-.1 1.5-.6 1.8-1.2s.2-1.1.1-1.2-.2-.2-.4-.3Z"/></svg>'


def business_ld():
    c = CONFIG
    return {
        "@context": "https://schema.org", "@type": "AutoDealer", "@id": SITE + "/#dealer",
        "name": c["name"], "url": SITE + "/", "telephone": c["phone_intl"], "image": SITE + "/assets/hero.jpg",
        "slogan": "Your car, is our passion!", "priceRange": "€€",
        "address": {"@type": "PostalAddress", "streetAddress": c["street"], "postalCode": c["postal"],
                    "addressLocality": c["city"], "addressRegion": "West-Vlaanderen", "addressCountry": "BE"},
        **({"geo": {"@type": "GeoCoordinates", "latitude": c["lat"], "longitude": c["lng"]}} if c.get("lat") else {}),
        "areaServed": ["Zarren", "Kortemark", "Diksmuide", "Roeselare", "Torhout", "Ieper", "West-Vlaanderen"],
        **({"openingHoursSpecification": c["opening_hours_schema"]} if c.get("opening_hours_schema") else {}),
        **({"sameAs": c["same_as"]} if c.get("same_as") else {}),
    }


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def card(c, lang):
    t = T[lang]
    img = c["img"][0][1] if c["img"] else "/assets/geen-foto.svg"
    facts = " · ".join(x for x in [c.get("bouwjaar"), kmfmt(c["km_n"]) if c["km_n"] else "",
                                    tr(lang, FUEL_FR, c.get("brandstof", "")), tr(lang, GEAR_FR, c.get("transmissie", ""))] if x)
    vat = f'<span class="tag">{t["vat_note"]}</span>' if c.get("btw_aftrekbaar", "").lower() == "ja" else ""
    return f"""<article class="card" data-merk="{e(c.get('merk', ''))}" data-fuel="{e(c.get('brandstof', ''))}" data-price="{c['prijs_n']}" data-km="{c['km_n']}" data-year="{e(c.get('bouwjaar') or 0)}">
<a href="{car_url(c, lang)}"><div class="ph"><img src="{e(img)}" alt="{e(c['name'])} {e(c.get('bouwjaar', ''))}" loading="lazy" width="640" height="480">{vat}</div>
<div class="cb"><h3>{e(c['name'])}</h3><p class="facts">{e(facts)}</p>
<div class="row"><span class="price">{eur(c['prijs_n'])}</span><span class="more">{t['more']} →</span></div></div></a></article>"""


# --------------------------------------------------------------------------- pagina's
def build_home(cars, lang):
    t = T[lang]
    c = CONFIG
    path = t["home"]
    brands = sorted({x.get("merk", "") for x in cars if x.get("merk")})
    fuels = sorted({x.get("brandstof", "") for x in cars if x.get("brandstof")})
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "name": t["stock"],
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + car_url(x, lang), "name": x["name"]}
                                    for i, x in enumerate(cars)]}
    out = head(lang, t["title_home"], t["meta_home"], path, {"nl": "/", "fr": "/fr/"},
               ld(business_ld()) + ld(itemlist))
    out += header(lang, "/fr/" if lang == "nl" else "/")
    out += f"""<main>
<section class="hero"><div class="wrap hero-in"><div class="hero-txt">
<p class="eyebrow">Bossu Motors · Zarren</p>
<h1>{t['hero_h']}</h1><p class="lead">{t['hero_p']}</p>
<div class="cta"><a class="btn" href="#voorraad">{t['hero_cta']}</a>
<a class="btn btn-ghost" href="tel:{c['phone_intl']}">{t['call']}: {c['phone']}</a></div>
</div><img class="hero-img" src="/assets/hero.jpg" alt="Bossu Motors - Your car, is our passion!" width="828" height="842"></div></section>
<section class="why"><div class="wrap why-in">{''.join(f'<div><h2>{e(a)}</h2><p>{e(b)}</p></div>' for a, b in t['why'])}</div></section>
<section id="voorraad" class="stock"><div class="wrap">
<div class="stock-head"><h2>{t['stock']}</h2><p class="muted" id="count">{t['cars_n'].format(n=len(cars))}</p></div>
<div class="filters">
<select id="f-merk" aria-label="{t['all']}"><option value="">{t['all']}</option>{''.join(f'<option>{e(b)}</option>' for b in brands)}</select>
<select id="f-fuel" aria-label="{t['allfuel']}"><option value="">{t['allfuel']}</option>{''.join(f'<option value="{e(f)}">{e(tr(lang, FUEL_FR, f))}</option>' for f in fuels)}</select>
<select id="f-sort" aria-label="{t['sort']}"><option value="new">{t['s_new']}</option><option value="low">{t['s_low']}</option><option value="high">{t['s_high']}</option><option value="km">{t['s_km']}</option></select>
</div>
<div class="grid" id="grid">{''.join(card(x, lang) for x in cars)}</div>
<p class="muted none" id="none" hidden>{t['none']}</p>
</div></section>
<section id="contact" class="contact"><div class="wrap contact-in">
<div><h2>{t['contact']}</h2>
<p class="addr"><strong>{e(c['name'])}</strong><br>{e(c['street'])}<br>{e(c['postal'])} {e(c['city'])}</p>
<p><a class="btn" href="tel:{c['phone_intl']}">{c['phone']}</a> <a class="btn btn-ghost" href="https://wa.me/{c['whatsapp']}" rel="noopener">{t['whatsapp']}</a></p>
<p><a href="https://www.google.com/maps/dir/?api=1&amp;destination={e(c['street'] + ', ' + c['postal'] + ' ' + c['city'])}" rel="noopener">{t['route']} →</a></p>
<h3>{t['hours']}</h3><p>{'<br>'.join(e(h) for h in c['hours_text'][lang])}</p></div>
<div class="map"><iframe title="Kaart" loading="lazy" src="https://www.google.com/maps?q={e(c['street'] + ', ' + c['postal'] + ' ' + c['city'])}&amp;output=embed"></iframe></div>
</div></section>
</main>
<script>
(function(){{var g=document.getElementById('grid'),cards=[].slice.call(g.children),m=document.getElementById('f-merk'),f=document.getElementById('f-fuel'),s=document.getElementById('f-sort'),cnt=document.getElementById('count'),none=document.getElementById('none'),tpl={json.dumps(t['cars_n'])};
function run(){{var n=0;cards.forEach(function(c){{var ok=(!m.value||c.dataset.merk===m.value)&&(!f.value||c.dataset.fuel===f.value);c.hidden=!ok;if(ok)n++;}});
var k=s.value,arr=cards.slice();if(k!=='new')arr.sort(function(a,b){{return k==='low'?a.dataset.price-b.dataset.price:k==='high'?b.dataset.price-a.dataset.price:a.dataset.km-b.dataset.km;}});
arr.forEach(function(c){{g.appendChild(c);}});cnt.textContent=tpl.replace('{{n}}',n);none.hidden=n>0;}}
[m,f,s].forEach(function(x){{x.addEventListener('change',run);}});}})();
</script>"""
    out += footer(lang)
    write(path, out)


def build_car(c, lang):
    t = T[lang]
    cf = CONFIG
    path = car_url(c, lang)
    other = "fr" if lang == "nl" else "nl"
    price = eur(c["prijs_n"])
    km = kmfmt(c["km_n"]) if c["km_n"] else ""
    title = t["car_title"].format(car=f"{c['name']} {c.get('bouwjaar', '')}".strip())
    meta = t["car_meta"].format(car=c["name"], year=c.get("bouwjaar") or "-", km=km or "-", price=price, phone=cf["phone"])
    specs = [(t["year"], c.get("bouwjaar")), (t["reg"], c.get("eerste_inschrijving")), (t["km"], km),
             (t["fuel"], tr(lang, FUEL_FR, c.get("brandstof", ""))), (t["gear"], tr(lang, GEAR_FR, c.get("transmissie", ""))),
             (t["power"], f"{c['vermogen_pk']} pk" if lang == "nl" and c.get("vermogen_pk") else (f"{c['vermogen_pk']} ch" if c.get("vermogen_pk") else "")),
             (t["cc"], f"{c['motor_cc']} cc" if c.get("motor_cc") else ""), (t["color"], tr(lang, COLOR_FR, c.get("kleur", ""))),
             (t["vat"], t["yes"] if c.get("btw_aftrekbaar", "").lower() == "ja" else "")]
    specs_html = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in specs if b)
    opts = [tr(lang, OPT_FR, o) for o in c["opties_l"]]
    imgs = c["img"] or [("/assets/geen-foto.svg", "/assets/geen-foto.svg")]
    gallery = f'<div class="main-img"><img id="mainimg" src="{e(imgs[0][0])}" alt="{e(c["name"])} - 1" width="1400" height="1050"></div>'
    if len(imgs) > 1:
        gallery += '<div class="thumbs">' + "".join(
            f'<button type="button" data-src="{e(b)}" aria-label="{t["photos"]} {i + 1}"><img src="{e(s)}" alt="{e(c["name"])} - {i + 1}" loading="lazy" width="160" height="120"></button>'
            for i, (b, s) in enumerate(imgs)) + "</div>"
    if lang == "fr":
        desc = c.get("beschrijving_fr") or ""
        nl_desc = c.get("beschrijving", "")
        summ = f"{c['name']} de {c.get('bouwjaar') or '-'}, {km or '-'}, {tr(lang, FUEL_FR, c.get('brandstof', '')).lower()}, boîte {tr(lang, GEAR_FR, c.get('transmissie', '')).lower()}. Vendue avec garantie, entretien et contrôle technique avant livraison."
        desc_html = f"<p>{e(desc or summ)}</p>" + (f'<details><summary>{t["desc_nl_note"]}</summary><div class="desc">{e(nl_desc)}</div></details>' if nl_desc and not desc else "")
    else:
        desc_html = f'<div class="desc">{e(c.get("beschrijving", ""))}</div>'
    wa = urllib.request.quote(t["wa_msg"].format(car=c["name"], price=price, url=SITE + path))
    car_ld = {
        "@context": "https://schema.org", "@type": "Car", "name": f"{c['name']} {c.get('bouwjaar', '')}".strip(),
        "url": SITE + path, "brand": {"@type": "Brand", "name": c.get("merk", "")}, "model": c.get("model", ""),
        "description": meta, "image": [i[0] if i[0].startswith("http") else SITE + i[0] for i in imgs[:10]],
        "itemCondition": "https://schema.org/UsedCondition",
        "offers": {"@type": "Offer", "price": c["prijs_n"], "priceCurrency": "EUR", "availability": "https://schema.org/InStock",
                   "url": SITE + path, "seller": {"@id": SITE + "/#dealer"}},
    }
    if c.get("bouwjaar"): car_ld["vehicleModelDate"] = c["bouwjaar"]
    if c["km_n"]: car_ld["mileageFromOdometer"] = {"@type": "QuantitativeValue", "value": c["km_n"], "unitCode": "KMT"}
    if c.get("brandstof"): car_ld["fuelType"] = FUEL_SCHEMA.get(c["brandstof"], c["brandstof"])
    if c.get("transmissie"): car_ld["vehicleTransmission"] = "AutomaticTransmission" if "uto" in c["transmissie"] else "ManualTransmission"
    if c.get("kleur"): car_ld["color"] = c["kleur"]
    if c.get("vermogen_pk"): car_ld["vehicleEngine"] = {"@type": "EngineSpecification", "enginePower": {"@type": "QuantitativeValue", "value": c["vermogen_pk"], "unitCode": "BHP"}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Bossu Motors", "item": SITE + t["home"]},
        {"@type": "ListItem", "position": 2, "name": c["name"], "item": SITE + path}]}
    out = head(lang, title, meta, path, {lang: path, other: car_url(c, other)}, ld(car_ld) + ld(crumbs), image=imgs[0][0])
    out += header(lang, car_url(c, other))
    out += f"""<main class="wrap car">
<p class="crumbs"><a href="{t['home']}#voorraad">← {t['back']}</a></p>
<div class="car-grid">
<div class="gallery">{gallery}</div>
<aside class="side">
<h1>{e(c['name'])}</h1><p class="sub">{e(c.get('titel', ''))}</p>
<p class="bigprice">{price}{(' <span class="tag">' + t['vat_note'] + '</span>') if c.get('btw_aftrekbaar', '').lower() == 'ja' else ''}</p>
<dl class="specs">{specs_html}</dl>
<div class="ask"><h2>{t['interest']}</h2><p>{t['interest_txt']}</p>
<a class="btn" href="tel:{cf['phone_intl']}">{t['call']}: {cf['phone']}</a>
<a class="btn btn-ghost" href="https://wa.me/{cf['whatsapp']}?text={wa}" rel="noopener">{t['whatsapp']}</a></div>
</aside></div>
<section class="block"><h2>{t['desc']}</h2>{desc_html}</section>
{('<section class="block"><h2>' + t['options'] + '</h2><ul class="opts">' + ''.join(f'<li>{e(o)}</li>' for o in opts) + '</ul></section>') if opts else ''}
</main>
<script>document.querySelectorAll('.thumbs button').forEach(function(b){{b.addEventListener('click',function(){{document.getElementById('mainimg').src=b.dataset.src;}});}});</script>"""
    out += footer(lang)
    write(path, out)


def write(path, content):
    fp = os.path.join(DIST, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(DIST, path.strip("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, "w", encoding="utf-8").write(content)


def build_meta(cars):
    urls = [("/", "/fr/")] + [(car_url(c, "nl"), car_url(c, "fr")) for c in cars]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for nl, fr in urls:
        for p in (nl, fr):
            sm.append(f"<url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod>"
                      f'<xhtml:link rel="alternate" hreflang="nl-BE" href="{SITE}{nl}"/>'
                      f'<xhtml:link rel="alternate" hreflang="fr-BE" href="{SITE}{fr}"/></url>')
    sm.append("</urlset>")
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    domain = re.sub(r"^https?://", "", SITE)
    open(os.path.join(DIST, "CNAME"), "w").write(domain + "\n")
    open(os.path.join(DIST, ".nojekyll"), "w").write("")
    if CONFIG.get("google_site_verification_file"):
        n = CONFIG["google_site_verification_file"]
        open(os.path.join(DIST, n), "w").write(f"google-site-verification: {n}")
    # 404-pagina
    t = T["nl"]
    write("404.html", head("nl", "Pagina niet gevonden | Bossu Motors", "Deze pagina bestaat niet (meer).", "/404.html", {"nl": "/", "fr": "/fr/"})
          + header("nl", "/fr/") + f'<main class="wrap car"><h1>Deze wagen is niet meer beschikbaar</h1><p>Waarschijnlijk is hij al verkocht. / Cette voiture n\'est plus disponible.</p><p><a class="btn" href="/#voorraad">{t["stock"]}</a> <a class="btn btn-ghost" href="/fr/#voorraad">Notre stock</a></p></main>' + footer("nl"))


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"))
    cars = load_rows()
    # volgorde = volgorde in de sheet (bovenaan = eerst getoond)
    fetch_photos(cars)
    for lang in ("nl", "fr"):
        build_home(cars, lang)
        for c in cars:
            build_car(c, lang)
    build_meta(cars)
    print("Klaar: website staat in", DIST)


if __name__ == "__main__":
    main()
