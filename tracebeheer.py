"""Leg echte uitwisselingen vast tijdens de run, zonder modelredeneringen te verzinnen."""
from datetime import datetime


def registreer_beurt(trace, ronde, spreker, soort, **velden):
    beurten = trace["beurten"]
    beurt = {"nr": len(beurten) + 1, "ronde": ronde, "spreker": spreker, "soort": soort,
             "tijdstip": datetime.now().astimezone().isoformat(timespec="milliseconds"), **velden}
    rollen = trace["raadsleden"]
    if spreker in rollen and soort in ("bericht", "toolcall"):
        routering = next((b for b in reversed(beurten) if b["soort"] == "routering"), None)
        if routering and routering.get("aan") == spreker:
            beurt["in_antwoord_op"] = routering["nr"]
    if spreker in rollen and soort == "bericht":
        beurt["ontvangers"] = ["koning", *[r for r in rollen if r != spreker]]
        beurt["context_beurten"] = [b["nr"] for b in beurten
                                    if b["soort"] == "bericht" and b["spreker"] in rollen]
    beurten.append(beurt)
    return beurt


def controleer_uitwisselingen(trace):
    """Controleer expliciete relaties; oudere traces zonder extra velden blijven leesbaar."""
    fouten, gezien = [], {}
    rollen = trace.get("raadsleden", [])
    for b in trace.get("beurten", []):
        nr, spreker = b.get("nr"), b.get("spreker")
        if "in_antwoord_op" in b:
            vraag = gezien.get(b["in_antwoord_op"])
            if not vraag or vraag.get("soort") != "routering" or vraag.get("aan") != spreker:
                fouten.append(f"trace.json: beurt {nr} verwijst niet naar een eerdere vraag aan {spreker}")
        for context_nr in b.get("context_beurten", []):
            context = gezien.get(context_nr)
            if not context or context.get("soort") != "bericht" or context.get("spreker") not in rollen:
                fouten.append(f"trace.json: beurt {nr} heeft geen eerdere Raadslid-bijdrage als context: {context_nr}")
        ontvangers = b.get("ontvangers")
        if ontvangers is not None and (len(ontvangers) != len(set(ontvangers))
                                      or set(ontvangers) - {"koning", "mens", *rollen}):
            fouten.append(f"trace.json: beurt {nr} heeft ongeldige ontvangers")
        gezien[nr] = b
    return fouten
