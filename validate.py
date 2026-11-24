"""Toetst verdict.json en trace.json aan de schema's in schema/. Start met `uv run validate`."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from tracebeheer import controleer_uitwisselingen
from besluitvorming import BEURTENBUDGET, ID_STREEP, MIN_ROLLEN, ROLLEN, debat_ids, toets_bewijs

ROOT = Path(__file__).parent
# Modellen schrijven ID's soms met een speciaal koppelteken (bv. U+2011): dat faalt op het schema.
RARE_STREEP = ID_STREEP


def spelregels(trace):
    """Budget, routering, minimale deelname en bronisolatie."""
    fout, toegewezen, aantal = [], None, 0
    bestanden, tools, gesproken = set(), set(), set()
    rollen = trace.get("raadsleden") or []
    if len(rollen) < MIN_ROLLEN:
        fout.append(f"trace.json: minstens {MIN_ROLLEN} Rollen moeten deelnemen")
    if trace.get("status") not in (None, "klaar"):
        fout.append("trace.json: de run is niet succesvol afgerond")
    for nr, b in enumerate(trace.get("beurten") or [], 1):
        spreker = b.get("spreker")
        if b.get("nr") != nr:
            fout.append(f"trace.json: beurtnummer {b.get('nr')} moet {nr} zijn")
        if spreker in ROLLEN and spreker not in rollen:
            fout.append(f"trace.json: {spreker} staat niet in raadsleden")
        if b.get("soort") == "bestand":
            pad = b.get("bestand", "").replace("\\", "/").split("/")
            if spreker not in rollen or len(pad) != 2 or pad[0] != spreker or pad[1] in ("", ".", ".."):
                fout.append(f"trace.json: beurt {b.get('nr')} leest een bron buiten de eigen Rol")
            else:
                bestanden.add(spreker)
        elif b.get("soort") == "toolcall":
            pad = urlsplit(b.get("pad", "")).path.rstrip("/")
            if spreker not in rollen or not pad.endswith(f"/{spreker}/mcp"):
                fout.append(f"trace.json: beurt {b.get('nr')} gebruikt niet het eigen MCP-pad")
            elif toegewezen != spreker:
                fout.append(f"trace.json: toolcall in beurt {b.get('nr')} heeft geen Routering naar die Rol")
            else:
                tools.add(spreker)
        if b.get("soort") == "routering":
            toegewezen = b.get("aan")
            tools.clear()
        elif b.get("soort") == "bericht" and spreker in ROLLEN:
            aantal += 1
            gesproken.add(spreker)
            if toegewezen != b["spreker"]:
                fout.append(f"trace.json: beurt {b.get('nr')} ({b['spreker']}) heeft geen Routering naar die Rol ervoor")
            if spreker not in bestanden and spreker not in tools:
                fout.append(f"trace.json: beurt {b.get('nr')} ({spreker}) heeft geen eigen bron gelezen")
            toegewezen = None
            tools.clear()
    if len(gesproken) < MIN_ROLLEN:
        fout.append(f"trace.json: minstens {MIN_ROLLEN} verschillende Rollen moeten spreken")
    if aantal > BEURTENBUDGET:
        fout.append(f"trace.json: {aantal} Raadslid-beurten, het Beurtenbudget is {BEURTENBUDGET}")
    return fout + controleer_uitwisselingen(trace)


def fouten(naam):
    pad = ROOT / naam
    if not pad.exists():
        return None, [f"{naam} ontbreekt in de root van de repo"]
    try:
        data = json.loads(pad.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return None, [f"{naam} kan niet gelezen worden: {exc}"]
    schema = json.loads((ROOT / "schema" / naam).read_text(encoding="utf-8"))
    return data, [f"{naam}: {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                  for e in Draft202012Validator(schema).iter_errors(data)]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    verdict, f1 = fouten("verdict.json")
    trace, f2 = fouten("trace.json")
    alle = f1 + f2 + (spelregels(trace) if isinstance(trace, dict) and not f2 else [])
    if isinstance(verdict, dict) and isinstance(trace, dict) and verdict.get("run_id") != trace.get("run_id"):
        alle.append("run_id van verdict.json en trace.json verschilt: ze moeten uit dezelfde run komen")
    if not f1 and not f2 and isinstance(verdict, dict) and isinstance(trace, dict):
        try:
            ids = debat_ids(trace["beurten"], trace["raadsleden"])
            toets_bewijs(verdict, ids)
            toets_bewijs(trace["geschillen"], ids)
        except ValueError as exc:
            alle.append(f"Bewijscontrole: {exc}")
    if verdict and RARE_STREEP.search(json.dumps(verdict, ensure_ascii=False)):
        alle.append("verdict.json bevat ID's met een speciaal koppelteken (bv. ORA‑101): vervang het door een gewoon '-'")
    for f in alle:
        print("FOUT", f)
    if isinstance(trace, dict):
        for b in trace.get("beurten") or []:
            if b.get("onbevestigd"):
                print(f"LET OP: beurt {b.get('nr')} ({b.get('spreker')}) noemde ID's die niet in de eigen bron "
                      f"stonden; ze tellen niet als bewijs: {', '.join(b['onbevestigd'])}")
    if isinstance(verdict, dict) and verdict.get("samenvatting") == "TODO":
        print("LET OP: verdict.json is nog het lege sjabloon uit de kit (TODO). Geldig, maar levert geen punten op.")
    print("GROEN: verdict.json en trace.json zijn geldig." if not alle else f"ROOD: {len(alle)} fout(en).")
    sys.exit(1 if alle else 0)


if __name__ == "__main__":
    main()
