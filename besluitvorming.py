"""JSON-antwoorden van de Koning controleren zonder zelf kennisbronnen te lezen."""
import json
import re

from jsonschema import Draft202012Validator

ROLLEN = ("archmage", "engineer", "guardian_keeper", "historian", "oracle", "beast_master")
BEURTENBUDGET = 10  # maximaal aantal Raadslid-beurten per run
MIN_ROLLEN = 3  # minimaal aantal verschillende Rollen dat moet spreken

# Geen \b: bronnen leveren soms ge-escapete tekst ("...\\nARC-015,..."), waar geen woordgrens staat.
ID = re.compile(r"(?<![A-Z])(?:ARC|ENG|GUA|HIS|ORA|BEA)-[0-9]{3}(?![0-9])")
ID_STREEP = re.compile(r"(?<![A-Z])(ARC|ENG|GUA|HIS|ORA|BEA)[‐‑‒–—―−]([0-9]{3})(?![0-9])")

TIJD = re.compile(r"(?<![0-9])[0-2]?[0-9]:[0-5][0-9](?![0-9])")  # tijdstippen als 14:32


def normaliseer_ids(data):
    if isinstance(data, str):
        return ID_STREEP.sub(r"\1-\2", data)
    if isinstance(data, list):
        return [normaliseer_ids(v) for v in data]
    if isinstance(data, dict):
        return {k: normaliseer_ids(v) for k, v in data.items()}
    return data


def bron_ids(tekst):
    """Alle record-ID's in een tekst, met genormaliseerde koppeltekens."""
    return set(ID.findall(normaliseer_ids(tekst or "")))


def lees_json(tekst):
    """Accepteer ook een codeblok of toelichting rond één JSON-object."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", tekst):
        try:
            data, _ = decoder.raw_decode(tekst[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise ValueError("Het antwoord bevat geen geldig JSON-object.")


def toets_schema(data, schema):
    fouten = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: str(e.absolute_path))
    if fouten:
        raise ValueError("; ".join(
            f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in fouten[:8]
        ))


def routering_schema(rollen):
    return {
        "type": "object",
        "required": ["rol", "vraag", "reden", "open_vragen", "hypothese"],
        "additionalProperties": False,
        "properties": {
            "rol": {"enum": [*rollen, None]},
            "vraag": {"type": ["string", "null"], "minLength": 1},
            "reden": {"type": "string", "minLength": 1},
            "open_vragen": {"type": "array", "maxItems": 5, "items": {"type": "string", "minLength": 1}},
            "hypothese": {
                "type": "object",
                "description": "Huidige werkhypothese per oorzaakdeel, met de dragende ID's; null = nog onbekend.",
                "required": ["ingreep", "mechanisme", "verloop"],
                "additionalProperties": False,
                "properties": {k: {"type": ["string", "null"], "minLength": 1}
                               for k in ("ingreep", "mechanisme", "verloop")},
            },
        },
    }


def toets_routering(data, beurten, rollen):
    toets_schema(data, routering_schema(rollen))
    gesproken = {b["spreker"] for b in beurten if b["soort"] == "bericht" and b["spreker"] in rollen}
    gezegd = normaliseer_ids(" ".join(b["tekst"] for b in beurten
                                      if b["soort"] == "bericht" and b["spreker"] in rollen))
    hypothese = " ".join(v for v in data["hypothese"].values() if v)
    eigen = normaliseer_ids(f"{data['vraag'] or ''} {data['reden']} {hypothese}")
    verzonnen = sorted((bron_ids(eigen) - bron_ids(gezegd))
                       | {t for t in TIJD.findall(eigen) if t not in TIJD.findall(gezegd)})
    if verzonnen:
        raise ValueError(f"Je vraag of reden noemt {', '.join(verzonnen)}, maar geen Raadslid noemde dat. "
                         "Gebruik alleen feiten uit het debat; stel anders een open vraag.")
    if data["rol"] is None:
        if len(gesproken) < MIN_ROLLEN:
            raise ValueError(f"Laat minstens {MIN_ROLLEN} verschillende Rollen spreken voordat je stopt.")
        if data["vraag"] is not None:
            raise ValueError("Bij stoppen moet vraag null zijn.")
    elif not isinstance(data["vraag"], str) or not data["vraag"].strip():
        raise ValueError("Een Raadslid moet een concrete vraag krijgen.")
    else:
        aantal = sum(b["soort"] == "bericht" and b["spreker"] in rollen for b in beurten)
        if aantal >= BEURTENBUDGET:
            raise ValueError("Het Beurtenbudget is op: stop met rol:null.")
        if BEURTENBUDGET - aantal <= MIN_ROLLEN - len(gesproken) and data["rol"] in gesproken:
            raise ValueError(f"Kies een Rol die nog niet sprak om binnen het budget {MIN_ROLLEN} Rollen te horen.")


def debat_ids(beurten, rollen):
    """Alleen uitspraken van Raadsleden tellen, geen suggesties van de Koning.

    ID's die een Raadslid noemde maar niet in de eigen bron of het debat voorkwamen
    (`onbevestigd`), gelden niet als bewijs.
    """
    return {
        record for b in beurten if b["soort"] == "bericht" and b["spreker"] in rollen
        for record in bron_ids(b["tekst"]) if record not in b.get("onbevestigd", ())
    }


def toets_bewijs(data, toegelaten):
    """Controleer bewijsvelden én verwijzingen in vrije tekst op herkomst uit het debat."""
    onbekend = set(ID.findall(json.dumps(data, ensure_ascii=False))) - toegelaten
    if onbekend:
        raise ValueError(f"Record-ID's kwamen niet voor in het debat: {', '.join(sorted(onbekend))}")
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "bewijs" and isinstance(value, list):
                onbekend = set(value) - toegelaten
                if onbekend:
                    raise ValueError(f"Bewijs ontbreekt in het debat: {', '.join(sorted(onbekend))}")
            toets_bewijs(value, toegelaten)
    elif isinstance(data, list):
        for value in data:
            toets_bewijs(value, toegelaten)
