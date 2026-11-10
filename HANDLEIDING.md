# Website Bossu Motors: handleiding

Na de installatie werkt de website zo:

**Google Sheet (uw voorraadlijst)** → elke 2 uur automatisch → **www.bossu-motors.be**

U past alleen de Google Sheet aan. De website volgt vanzelf. Hosting en updates zijn gratis.
U betaalt alleen uw domeinnaam (die hebt u al).

---

## Eenmalige installatie (± 30 minuten)

### Stap 1: Voorraadlijst in Google Sheets zetten
1. Ga naar **sheets.new** (u moet ingelogd zijn met een Google-account).
2. Kies **Bestand → Importeren → Uploaden** en kies `voorraad.csv`. Laat "Spreadsheet vervangen" staan en klik op **Gegevens importeren**.
3. Geef het bestand de naam **Voorraad Bossu Motors**.
4. Kies **Bestand → Delen → Publiceren op internet**:
   - Linkerlijst: het eerste tabblad. Rechterlijst: **Door komma's gescheiden waarden (.csv)**
   - Klik op **Publiceren** en **kopieer de link**. U hebt die nodig in stap 3.

### Stap 2: Gratis GitHub-account en website-opslag
1. Maak een gratis account op **github.com**.
2. Klik rechtsboven op **+ → New repository**.
   - Naam: `bossu-motors-site`. Kies **Public**, want gratis hosting werkt alleen zo. Uw website is toch openbaar.
   - Klik op **Create repository**.
3. Klik op **uploading an existing file**. Pak de zip uit en sleep **alle bestanden en mappen** erin, ook de map `.github`.
   Klik daarna op **Commit changes**.

### Stap 3: De Google Sheet koppelen
1. Ga in de repository naar **Settings → Secrets and variables → Actions → tabblad Variables → New repository variable**.
2. Vul in:
   - Name: `SHEET_CSV_URL`
   - Value: de link uit stap 1.4
3. Klik op **Add variable**.

### Stap 4: Website aanzetten
1. Ga naar **Settings → Pages**. Kies bij *Source* voor **GitHub Actions**.
2. Ga naar het tabblad **Actions** en klik op **Website bijwerken → Run workflow**.
   Na 2 à 3 minuten staat de site online.
3. Ga terug naar **Settings → Pages**. Vul bij *Custom domain* `www.bossu-motors.be` in, klik op **Save** en vink daarna **Enforce HTTPS** aan.
   Dat kan pas nadat u stap 5 hebt gedaan.

### Stap 5: Domeinnaam koppelen
Log in bij de firma waar u bossu-motors.be gekocht hebt (bv. Combell, One.com, Versio, Telenet…). Open daar de **DNS-instellingen**:

| Type  | Naam / host | Waarde                       |
|-------|-------------|------------------------------|
| CNAME | www         | `UW-GITHUB-NAAM.github.io`   |
| A     | @ (leeg)    | 185.199.108.153              |
| A     | @ (leeg)    | 185.199.109.153              |
| A     | @ (leeg)    | 185.199.110.153              |
| A     | @ (leeg)    | 185.199.111.153              |

Verwijder eerst eventuele oude A-records voor "@" en "www". Het kan tot 24 uur duren voor alles werkt.

---

## Dagelijks gebruik: alleen de Google Sheet aanpassen

| Wat?                 | Wat doet u in de sheet?                                                     |
|----------------------|-----------------------------------------------------------------------------|
| **Wagen verkocht**   | Zet in de kolom `actief` het woord **nee**, of verwijder de rij             |
| **Prijs aanpassen**  | Wijzig de kolom `prijs`. Typ alleen cijfers, bv. `18999`                    |
| **Nieuwe wagen**     | Voeg bovenaan een rij in en vul de kolommen in (zie hieronder)               |
| **Volgorde**         | De bovenste rij in de sheet staat eerst op de website                       |
| **Meteen bijwerken** | GitHub → Actions → Website bijwerken → Run workflow. Anders gebeurt het automatisch binnen 2 uur |

**Kolommen:** `id` (uniek, bv. `bm2026-001`), `merk`, `model`, `titel`, `prijs`, `bouwjaar`,
`eerste_inschrijving`, `km`, `brandstof` (Benzine / Diesel / Elektrisch / Hybride Elektrisch/Benzine…),
`transmissie` (Automaat / Handgeschakeld), `kleur`, `motor_cc`, `vermogen_pk`, `btw_aftrekbaar` (ja/nee),
`opties` (gescheiden door `|`), `beschrijving`, `beschrijving_fr` (mag leeg blijven),
`fotos` (links, gescheiden door een spatie).

**Foto's toevoegen:**
- *Makkelijkst:* zet de wagen eerst op 2dehands en vraag dan aan Claude: *"zet mijn nieuwe 2dehands-wagens in de voorraadlijst"*.
- *Zelf:* zet de foto's in Google Drive. Klik rechts op een foto → **Delen** → **Iedereen met de link** → **Link kopiëren** en plak de link in de kolom `fotos`.

De website kopieert alle foto's naar uw eigen site. Ze blijven dus werken, ook als het zoekertje op 2dehands verdwijnt.

---

## Hoger in Google komen (gratis)

1. **Google Bedrijfsprofiel** (business.google.com). Dit is het **allerbelangrijkste** voor lokale zoekopdrachten zoals "tweedehands auto Kortemark" of "garage Zarren".
   - Vul het adres, de website, het telefoonnummer, de openingsuren en de categorie "Tweedehandsautodealer" in.
   - Plaats regelmatig foto's van nieuwe wagens.
   - **Vraag elke klant om een Google-review.** Dat maakt het grootste verschil.
2. **Google Search Console** (search.google.com/search-console):
   - Voeg het domein `bossu-motors.be` toe en bevestig het via een TXT-record bij uw DNS, net zoals in stap 5.
   - Kies **Sitemaps** en dien `https://www.bossu-motors.be/sitemap.xml` in.
3. **Links naar uw site** zetten op uw 2dehands-verkopersprofiel, Facebook, Instagram en in uw e-mailhandtekening.
4. Schrijf **goede beschrijvingen** in de sheet, met merk, model, uitvoering, opties en "Zarren".
   Gebruik bij voorkeur een eigen tekst en niet exact dezelfde als op 2dehands. Google beloont unieke tekst.

De website regelt zelf al het technische deel:
- een aparte pagina per wagen, in het Nederlands én het Frans
- gestructureerde gegevens voor Google (wagen, prijs, kilometerstand, garage)
- sitemap, snelle laadtijd en geschikt voor gsm

---

## Gegevens van de zaak wijzigen
Open `config.json` op GitHub en klik op het potloodje. Daar staan openingsuren, e-mail, btw-nummer en links naar Facebook of Instagram (`same_as`).
Klik daarna op **Commit changes**. De site wordt dan automatisch bijgewerkt.
