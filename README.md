# Council of Achrona: Starter kit

Starter kit voor challenge 113 van Hack The Future 2026, aangeboden door Roboest.

## Deze uitwerking

Het doel: de oorzaak van de Desync reconstrueren met meerdere onafhankelijke perspectieven en een onderbouwd herstelplan opleveren. De Koning leidt het onderzoek; ieder Raadslid leest uitsluitend zijn eigen bronnen.

De starter is hier uitgewerkt tot een Council met zes beschikbare Rollen:

- De Koning gebruikt `MODEL_GROOT` om na elke bijdrage een relevante spreker, concrete vraag en inhoudelijke reden te kiezen. Hij houdt `open_vragen` bij en kan zelf vroegtijdig stoppen.
- Minstens drie verschillende Rollen moeten spreken, binnen maximaal tien Raadslid-beurten. Rollen zonder MCP-pad of lokale bron doen niet mee; er moeten minstens drie Rollen met bronnen beschikbaar zijn.
- Het Verdict bevat de oorzaak in drie delen, een geordend herstelplan en risico's; geschillen staan in de trace. Onbekende oorzaakdelen blijven `null`; zekerheid wordt gevraagd en een voorspelling alleen als de bronnen die onderbouwen.
- JSON-antwoorden worden gecontroleerd en zo nodig maximaal tweemaal opnieuw gevraagd. Record-ID's in het besluit en de geschillen moeten in bijdragen van Raadsleden voorkomen. Dit controleert herkomst uit het debat; de inhoudelijke juistheid van een broninterpretatie blijft onderwerp van het debat.
- Elk record-ID dat een Raadslid noemt, wordt getoetst tegen wat het echt uit de eigen bron las (MCP-toolresultaten of lokale bestanden) en het debat. Een verzonnen ID levert één herkansing op; blijft het staan, dan komt het als `onbevestigd` in de trace en telt het niet als bewijs.
- Elk Raadslid heeft een eigen sessie: het onthoudt zijn bron en eerdere bijdragen en krijgt per beurt alleen wat nieuw is in het debat. Dat bespaart tokens en voorkomt herhaling; een gerichte toolcall per beurt blijft verplicht.
- De Koning houdt bij elke routering een `hypothese` bij (ingreep, mechanisme, verloop, met dragende ID's) en kiest zijn vraag om de zwakste hypothese te toetsen. Vragen, redenen en hypotheses mogen alleen tijden en ID's bevatten die een Raadslid noemde: een verzonnen premisse wordt in code geweigerd.
- Een Raadslid dat zijn MCP-bron niet raadpleegt of niets zegt, krijgt één herkansing met gerichte feedback voordat de run afbreekt. Bij Ctrl+C of een fout staat de trace op `status: "fout"`.
- De validator controleert ook bronisolatie, minimale deelname en routeringen. De viewer toont redenen voor herstelacties, mitigaties, zekerheid en eventuele voorspelling.
- Nieuwe tracebeurten krijgen een `tijdstip`. Elk antwoord en elke broncall verwijzen via `in_antwoord_op` naar de vraag en reden van de Koning. `ontvangers` en `context_beurten` tonen met wie een bijdrage gedeeld wordt en welke eerdere bijdragen beschikbaar waren. De viewer maakt deze beurten aanklikbaar. Tijdelijke Windows-bestandsblokkeringen worden kort opnieuw geprobeerd zonder de bestaande trace half te overschrijven.

Voor een echte run heb je nog een teamkey en MCP-paden of het uitgepakte challenge pack nodig. Er worden geen echte zaakgegevens of eindbesluiten meegeleverd.

```powershell
uv sync --locked
Copy-Item .env.example .env  # alleen als je nog geen .env hebt
# Vul je teamkey en minstens drie MCP-paden in .env in, of pak pack.zip uit.
uv run viewer              # in een aparte terminal
uv run council
uv run validate
```

Offline controles zonder API-key, netwerkproviders of teambudget:

```powershell
uv run python -m unittest discover -s tests -v
```

De integratietest gebruikt het echte agent-framework met een lokaal gesimuleerd LLM-endpoint en tijdelijke testbronnen. Testuitvoer komt niet in de root terecht.

Staat de omgeving al in `.venv` maar `uv` niet op je `PATH` (Windows), gebruik `.\.venv\Scripts\uv.exe run council`, of start rechtstreeks met `.\.venv\Scripts\python.exe council.py`. Voor de viewer en validator vervang je `council.py` door `viewer.py` of `validate.py`.

## Wat de Council vond

Uit het ingeleverde `verdict.json` (zekerheid per deel tussen haakjes):

- **Verloop (0,6):** sterke nachtelijke onrust en schildopeningen rond 04:15–04:50, elke vier dagen: dag 10, 14, 18, … 42. Gedragen door de Beast Master, de Oracle en de Guardian Keeper, elk met een eigen bron.
- **Ingreep (0,35):** de activering van de hulpslag als pols "los van de Kroonklok" op dag 10 om 02:40 (ENG-011, +38% doorvoer ENG-012), twee uur vóór het eerste sterke symptoom (BEA-019).
- **Mechanisme (0,2):** een verschoven tijdreferentie na die activering; nog niet bewezen.
- **Voorspelling:** dag 46 (laatste cyclusdag 42 + 4).
- **Herstelplan:** eerst de hulpslag terug op de Kroonklok zetten of onder toezicht uitschakelen, dan de nachtelijke openingen beperken, daarna de open sporen verifiëren.

## Van eerste run naar ingeleverde run

We lazen elke trace zoals een jurylid en stuurden bij op wat we zagen. Een paar voorbeelden:

| Wat we zagen | Wat we deden |
|---|---|
| De Koning vroeg naar "14:32 op 3 April", een premisse die in geen enkele bron stond, en herhaalde die na tegenspraak. | Vragen, redenen en hypotheses mogen alleen tijden en record-ID's bevatten die een Raadslid noemde; de code weigert de rest. De eerste vraag is open en verkennend. |
| De ID-controle vond maar 16 van de 100 ID's in een MCP-bron (ge-escapete tekst, lijst van objecten), dus echte ID's werden als verzonnen gemarkeerd. | Toolresultaten correct uitlezen en een robuustere ID-regex. Elk genoemd ID wordt getoetst tegen wat het Raadslid echt las; verzonnen ID's tellen niet als bewijs. |
| De Engineer pleitte zichzelf vrij met "niets in mijn logs" en liet een incident twee uur na zijn eigen ingreep liggen. | Raadsleden moeten bewijs tegen hun eigen Belang noemen; ontbrekende registratie is geen bewijs. De Koning laat zo'n ontlasting toetsen door een Rol die die uren wel waarneemt. |
| Het eerste Verdict liet ingreep en mechanisme op `null`, zonder voorspelling, met alleen onderzoeksstappen als herstel. | De Koning houdt per beurt een werkhypothese bij, legt alle Rollen op één tijdlijn en kiest de best onderbouwde verklaring met eerlijke zekerheid. Het herstelplan begint met de waarschijnlijkste oorzaak. |
| Raadsleden lazen elke beurt hun hele bron opnieuw en kregen alle oude routeringen mee: 376k invoertokens voor 10 beurten. | Elk Raadslid heeft een sessie en krijgt alleen het nieuwe debat; context compact; maximaal 4 toolcalls per beurt. |

Effect tussen de eerste en de ingeleverde run: ingreep van `null` naar een onderbouwde bewering, een voorspelling erbij, alle zes Rollen gehoord, geen onbevestigde ID's, en 15–30% minder invoertokens.

**Waarom een Council beter werkt dan één agent:** elk Raadslid ziet alleen zijn eigen bron. Het antwoord stond in geen enkele bron volledig: de ingreep stond bij de Engineer, het ritme bij de Beast Master en de Oracle, de openingen bij de Guardian Keeper. De Koning brengt die samen, en de Raadsleden toetsen elkaars beweringen, ook wanneer een Rol een eigen belang heeft. Eén agent met alle bronnen tegelijk zou die tegenspraak niet zien.

De Desync heeft de herinneringen en systemen van Achrona versnipperd. Jullie bouwen een **Council**: een zwerm van samenwerkende AI-agenten (Raadsleden) die elk één Rol vertolken, debatteren, verspreide kennis analyseren en samen tot een **Council Verdict** komen: wat is de oorzaak, wat is het herstelplan, welke risico's zijn er.

Deze Council kun je live in je browser zien debatteren. De **Koning** beslist welk Raadslid spreekt, met welke vraag en waarom. In AI-termen heet dat deel een orchestrator. De oorspronkelijke opdracht en achtergrond staan hieronder; de belangrijkste bouwtaken zijn in deze uitwerking geïmplementeerd.

## Wat je krijgt op de dag

| Wat | Wanneer | Waar |
|---|---|---|
| Deze repo (GitHub-template) | vooraf | GitHub |
| LLM-toegang: Teamkaartje met je teamkey voor het Roboest-endpoint ($5 budget, tot 18:00) | 10:00 | coaches |
| Optioneel: je eigen FreeLLMAPI (gratis, zie "FreeLLMAPI (optioneel)") | vooraf | je laptop |
| Rolkaarten: perspectief, Belang en Kennisbron per Rol | in deze repo | `rolkaarten.md` |
| Challenge pack: Kennisbronnen (bestanden) | 10:00 | `https://mcp.findingsolutions.be/pack.zip` |
| MCP-server: één pad per Rol, `https://mcp.findingsolutions.be/<rol>/mcp` | antwoordt vanaf 10:00 (daarvoor geeft `uv run council` een MCP-fout) | in je `.env` |
| Coaches | de hele dag | in de zaal |

## Vooraf installeren

- Python 3.12 of hoger
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- git en een GitHub-account
- een code-editor

### LLM-toegang

Op de dag krijgt elk team om 10:00 een **Teamkaartje** met een teamkey voor het Roboest-endpoint (`https://roboest.findingsolutions.be/v1`, OpenAI-compatibel). Je kiest er twee modellen mee: `achrona` (klein, voor de Raadsleden) en `achrona-groot` (voor de Koning). Achter die namen wisselt het endpoint zelf tussen providers. De key heeft een budget van $5 en werkt tot 18:00. Je hoeft vooraf niets te installeren.

### FreeLLMAPI (optioneel)

Wil je een back-up als je budget op is, of zelf modellen kiezen? [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) bundelt de gratis tiers van veel LLM-providers achter één OpenAI-compatibel endpoint op je eigen laptop.

1. Installeer het: op Windows de desktop-app uit de [Microsoft Store](https://apps.microsoft.com/detail/9PBN6G8K2B7F); op macOS de app uit [Releases](https://github.com/tashfeenahmed/freellmapi/releases/latest); met Docker `curl -fsSL https://freellmapi.co/install.sh | bash`.
2. Open http://localhost:3001 en voeg op de **Keys**-pagina minstens 2 gratis provider-keys toe (bv. Google AI Studio en Groq). Aanmelden bij een provider vraagt soms een telefoonverificatie: doe dit thuis, niet op de dag.
3. Zet blok 2 van `.env.example` in je `.env` (in plaats van blok 1) met de **unified key** bovenaan de Keys-pagina.

Maak thuis al je repo aan (stap 1–2 hieronder) en draai daarin `uv sync` (en `uv sync --extra devui` als je de DevUI wil). Dan staat alles al geïnstalleerd en verlies je op de dag geen tijd op de wifi.

## Snel starten

1. Klik op **Use this template** en maak een eigen repo aan. Zet die **openbaar**: zo lever je in (zie onderaan).
2. Clone je repo en ga erin staan.
3. Maak je `.env`: kopieer het voorbeeld (`copy .env.example .env` op Windows, `cp .env.example .env` op macOS/Linux), vul in blok 1 de teamkey van je Teamkaartje in en vul de `MCP_<ROL>`-regels in.
4. Open de debatviewer in een tweede terminal:
   ```
   uv run viewer
   ```
5. Start de Council:
   ```
   uv run council
   ```
   In de viewer zie je live wie de Koning aan het woord laat en waarom, wat elk Raadslid zegt, welke Kennisbron het leest en hoeveel tokens het kost.
6. Controleer de uitvoer:
   ```
   uv run validate
   ```
   Groen = `verdict.json` en `trace.json` volgen het schema, komen uit dezelfde run en doorstaan de aanvullende spelregel- en bewijscontroles. Dat garandeert nog niet dat de diagnose inhoudelijk juist is.

Geen uv? Maak een venv (`python -m venv .venv`, activeer met `.venv\Scripts\activate` op Windows of `source .venv/bin/activate`), dan `pip install -e .` en `python viewer.py`, `python council.py`, `python validate.py`.

Viewer op een andere poort: zet `VIEWER_PORT=8101` als omgevingsvariabele. Een andere map bekijken, bv. het voorbeeld: `uv run viewer voorbeeld`.

## Hoe de kit werkt

```
             ┌────────────── jouw laptop ──────────────┐
             │  council.py ── Koning (leidt, geen bron)│
   (.env) ──►│      │      ── Raadslid (Oracle) ───────┼──► MCP  /oracle/mcp
             │      │      ── Raadslid (Engineer) ─────┼──► MCP  /engineer/mcp
             │      │      ── … (tot zes Rollen) ──────┼──► MCP  /<rol>/mcp
             │      ▼                                   │
             │  trace.json + verdict.json ──► viewer    │──► LLM via Roboest-endpoint
             └──────────────────────────────────────────┘
```

| Bestand | Wat |
|---|---|
| `council.py` | De Koning die gericht het debat leidt (`kies_volgende()`), het debat zelf en de gevalideerde synthese. Schrijft `trace.json` na elke beurt en `verdict.json` aan het einde. |
| `besluitvorming.py` | Gedeelde spelregelconstanten (Rollen, Beurtenbudget, minimum Rollen), JSON-verwerking, routeringscontroles en controle van bewijs-ID's uit het debat. |
| `tests/` | Offline tests, inclusief een volledige run tegen een gesimuleerd LLM-endpoint (`uv run python -m unittest discover -s tests -v`). |
| `raadsleden/<rol>.py` | Eén bestand per Raadslid: Rol, naam en publiek perspectief. |
| `rolkaarten.md` | De zes Rolkaarten: perspectief, publiek Belang en soort Kennisbron per Rol. Begin hier om je Rollen te kiezen. |
| `viewer.py` + `viewer.html` | De debatviewer (`uv run viewer`). Leest alleen `trace.json` en `verdict.json`, dus werkt ook als je een ander platform kiest. |
| `voorbeelden/devui_debat.py` | Dezelfde Raadsleden als MAF-group chat in de DevUI van Microsoft (zie "Volgende stappen"). |
| `kennisbronnen/` | Leeg (op een LEESMIJ na). Pak `pack.zip` uit in de root van de repo; dan staan de bronnen in `kennisbronnen/<rol>/`. Staat in `.gitignore`. |
| `schema/` | De JSON-schema's van het Council Verdict en de Debat-trace. |
| `voorbeeld/` | Een ingevuld voorbeeld over een verzonnen zaak (een dorpsmolen), om de vorm te zien. Het valideert bewust niet tegen het Achrona-schema. |
| `validate.py` | Toetst je uitvoer aan de schema's. |

## Wat stel je zelf in?

- **Welke Rollen** meedoen: alle zes Rolbestanden zijn aanwezig. Geef een Rol in `.env` een `MCP_<ROL>=https://mcp.findingsolutions.be/<rol>/mcp` of lokale bronnen. De Koning kiest uit Rollen met bronnen; minstens drie moeten beschikbaar zijn. De spreekvolgorde wordt inhoudelijk gekozen.
- **Kennisbronnen**: standaard leest elk Raadslid via MCP. Laat je `MCP_<ROL>` leeg, dan gaan de bestanden uit `kennisbronnen/<rol>/` (uit `pack.zip`) in de prompt van alleen dat Raadslid. Rollen zonder bron worden bij de start gemeld en overgeslagen. Een MCP-bijdrage zonder succesvol toolresultaat breekt de run af.
- **Modellen**: `MODEL_KLEIN` voor de Raadsleden, `MODEL_GROOT` voor de Koning, `REASONING` voor het denkwerk. Op het Roboest-endpoint zijn dat `achrona` en `achrona-groot`. Een andere provider kies je alleen via `.env` (blokken voor het Roboest-endpoint, FreeLLMAPI en Ollama). Met FreeLLMAPI kies je `auto:fast`/`auto:smartest` of een vast model uit de catalogus op http://localhost:3001. Support geven we op het Roboest-endpoint en FreeLLMAPI; andere eigen modellen mogen, zonder support.
- **Rondes**: de Koning kiest zelf het stopmoment; `RONDES` wordt niet meer gebruikt. Het Beurtenbudget (10 Raadslid-beurten) geldt altijd.
- **Het debat zelf**: de instructies, wie wie aan het woord laat (`kies_volgende()`), wat elk Raadslid van het debat ziet, en hoe de Koning het Verdict invult. Dat staat allemaal in `council.py`.

**Verbruik**: je teamkey heeft $5 budget en maximaal 60 calls per minuut; dat volstaat voor tientallen volledige runs. Gratis tiers van FreeLLMAPI hebben eigen limieten per provider. De viewer en de terminal tonen per run hoeveel tokens het kleine en het grote model gebruikten; het staat ook in `trace.json` onder `verbruik`. Bij een rate limit (429) wacht de kit en probeert opnieuw. Budget op? Dan geeft het endpoint een fout over het budget: schakel over op FreeLLMAPI (blok 2) of vraag een coach.

## De Koning leidt het debat

`async kies_volgende(beurten, leden, koning, opties, verbruik)` in `council.py` beslist voor elke beurt wie spreekt. De Koning krijgt publieke Rolkaarten en het debat, zonder ruwe Kennisbronnen. De functie geeft een gecontroleerd object met `rol`, `vraag`, `reden` en `open_vragen` terug. `rol: null` stopt het debat. Elke keuze wordt als `routering` vastgelegd (`aan`, `vraag`, `reden`, `open_vragen`); na 10 Raadslid-beurten stopt de code altijd.

Deze uitwerking gebruikt een LLM als Koning, aangevuld met controles in code: wie kan een bewering toetsen, welke kennis ontbreekt en wanneer voegt een extra beurt weinig toe? Ieder Raadslid ziet de bijdragen en routeringen, maar alleen zijn eigen ruwe bronnen.

### Na je eerste run: waar kijk je naar?

Lees het debat in de viewer zoals een jurylid het zou lezen:

- **Routeringen**: staat er overal `vaste volgorde`? Dan kiest jullie Koning nog niets.
- **Toolcalls**: heeft elk Raadslid zijn Kennisbron gelezen vóór het sprak? Een Raadslid zonder toolcall kan feiten en ID's verzinnen, en de anderen nemen dat over.
- **Open sporen**: welke bewering heeft nog niemand getoetst? Waar spreken Raadsleden elkaar tegen? Naar welke andere Rol verwijst iemand?
- **Verspilde beurten**: wie herhaalt of vat alleen samen wat al gezegd is?
- **Oorzaak**: welke delen (ingreep, mechanisme, verloop) zijn nog onbekend?

Wat je daar ziet, verbeter je in `kies_volgende()`.

### Regels of een agent?

Regels in code zijn een goed begin, maar ze zien geen inhoud: ze herkennen hoogstens een naam in een tekst. Twee Raadsleden die over hetzelfde spreken met andere woorden, merkt een regel niet op. Een Koning als **agent** is meestal sneller gebouwd en kiest beter, omdat hij het debat echt leest.

De vorm:

```
Raadsleden + debat tot nu toe  ──►  LLM (MODEL_GROOT)  ──►  {"rol": ..., "vraag": ..., "reden": ...}
```

Dit is geïmplementeerd via dezelfde agent-client als de Raadsleden. `kies_volgende()` is nu async. `vraag_json()` verwerkt ook JSON in codeblokken, valideert het antwoord en vraagt bij fouten gericht om herstel.

## Spelregels

- Eén Raadslid per Rol. Elk Raadslid leest alleen de Kennisbron van zijn eigen Rol. De viewer en de jury kijken dat na in de trace.
- De Koning leidt het debat en stelt het Verdict op, maar leest zelf geen Kennisbron.
- Maximaal 10 Raadslid-beurten per run (het **Beurtenbudget**). Alleen berichten van Raadsleden tellen; toolcalls, Routeringen en berichten van de Koning niet.
- Vóór elke Raadslid-beurt staat een `routering` in de trace: aan wie, welke vraag en waarom. `spreker` is `koning` (in code of als agent), een Rol (handoff) of `mens`.
- Prompts en code bevatten geen inhoud uit de Kennisbronnen (geen record-ID's of feiten). Wat de Council weet, komt uit het debat.
- Menselijke tussenkomst mag, maar staat in de trace als `spreker: "mens"`. Een Routering door een mens telt niet mee voor de Council-score.
- `trace.json` is de ongewijzigde uitvoer van de run die het Verdict maakte. Niet achteraf bewerken.
- Elke Rol heeft een Belang en kan ernaast zitten.

## Wat moet je zelf bouwen?

De onderstaande oorspronkelijke bouwtaken zijn in deze uitwerking verwerkt. De kwaliteit van vragen, broninterpretatie en diagnose moet nog met de echte Kennisbronnen worden beoordeeld.

- Een **Koning** die het debat leidt in plaats van de vaste volgorde, met een reden bij elke keuze.
- Meer Raadsleden (minstens 3 Rollen). Meer Rollen geven meer kennis, maar elke beurt telt. De Kennisbronnen verwijzen soms naar andere Rollen: dat zegt je welke Rol je nog mist.
- Een Koning die het `verdict.json` echt invult: de oorzaak in drie delen (`ingreep`, `mechanisme`, `verloop`), elk met een bewering en record-ID's als bewijs, een geordend herstelplan (`acties`) en minstens één risico. Weet je een deel niet, laat dan `bewering: null`.
- `geschillen` in de trace: waarover waren de Raadsleden het oneens, en hoe werd het beslecht?
- Let op: modellen schrijven ID's soms met een speciaal koppelteken (`ORA‑101`). `uv run validate` meldt dat; vervang het door een gewoon `-`.

## Jurering

Drie criteria, elk 0–10: **Verdict** (40%), **Council** (40%: hoe goed orchestreert jullie Council, zichtbaar in de Routeringen van de trace) en **Presentatie** (20%, met de vraag: waarom werkt jullie Council hier beter dan één agent?). Zonder Extra uitdaging haal je per criterium hoogstens 8 op 10. Voor wie sneller klaar is:

- **Verdict**: voorspel wanneer de Desync opnieuw toeslaat als niemand ingrijpt (optioneel veld `voorspelling {dag, bewering, bewijs[]}`) · geef je zekerheid per deel van de oorzaak (optioneel veld `zekerheid`, 0–1, per slot).
- **Council**: laat je Koning zelf beslissen wanneer het debat klaar is, en waarom (een `routering` met `aan: null` vóór het budget op is) · laat je Koning een lijst open vragen bijhouden en na elke beurt bijwerken (optioneel veld `open_vragen` in de `routering`).
- **Presentatie**: draai de Council live tijdens de pitch · bouw een eigen, rijkere visualisatie van het debat (bovenop of in plaats van de viewer) of geef de Rollen avatars.

## Volgende stappen

- **DevUI**: `uv run --extra devui python voorbeelden/devui_debat.py` opent de DevUI van [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) met dezelfde Raadsleden als group chat. Het gebruikt de bestanden uit `kennisbronnen/<rol>/` (geen MCP: pak eerst `pack.zip` uit) en schrijft geen trace. Handig om orchestratie te verkennen.
- MAF heeft patronen voor orchestratie: een group chat met een manager die de spreker kiest, Handoff (een agent geeft het woord door) en Magentic (een manager met een plan en open vragen). Gebruik ze, of kies een eigen platform: zolang je `verdict.json` en `trace.json` in dit formaat oplevert, met een `routering` vóór elke Raadslid-beurt, mag alles.
- Bouw RAG op de Kennisbronnen: het Roboest-endpoint biedt geen embeddings aan, FreeLLMAPI wel (`/v1/embeddings`).

## Inleveren (om 16:00)

- Je repo is **openbaar** en je deelt de link met ons via het inleverformulier (link bij de briefing).
- Commit en push `verdict.json` en `trace.json` (in de root, uit dezelfde run) vóór 16:00. Alleen de laatste commit vóór 16:00 telt.
- Kleine correcties aan `verdict.json` (bv. koppeltekens) mogen; `trace.json` laat je ongewijzigd.

## Licentie

MIT, zie `LICENSE`.
