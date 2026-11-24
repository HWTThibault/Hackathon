"""Offline regressietests met fictieve testdata; nooit een echt LLM-endpoint."""
import asyncio
import contextlib
import copy
import io
import json
import os
import re
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from agent_framework import Content, Message

import council
import raadsleden
import validate
from besluitvorming import (
    debat_ids, lees_json, normaliseer_ids, toets_bewijs, toets_routering, toets_schema,
)

PROJECT = council.ROOT
ROLLEN = ["engineer", "oracle", "historian"]
HYP = {"ingreep": None, "mechanisme": None, "verloop": None}


def verdict(run_id="test"):
    return {
        "run_id": run_id, "samenvatting": "Fictieve test; de oorzaak is nog onbekend.",
        "oorzaak": {s: {"bewering": None, "bewijs": [], "zekerheid": 0}
                    for s in ("ingreep", "mechanisme", "verloop")},
        "acties": [{"actie": "Controleer de testmeting.", "reden": "Eerst ontbrekend bewijs verzamelen.",
                    "bewijs": ["ENG-001"]}],
        "risicos": [{"risico": "Een onvolledige diagnose.", "mitigatie": "Verzamel aanvullend bewijs."}],
    }


def trace():
    beurten = []
    for rol in ROLLEN:
        beurten.append({"nr": len(beurten) + 1, "ronde": 0, "spreker": rol,
                        "soort": "bestand", "bestand": f"{rol}/test.md"})
    for rol, record in zip(ROLLEN, ("ENG-001", "ORA-001", "HIS-001")):
        beurten.append({"nr": len(beurten) + 1, "ronde": 1, "spreker": "koning", "soort": "routering",
                        "aan": rol, "vraag": "Wat bewijst je testbron?", "reden": "Ontbrekend perspectief."})
        beurten.append({"nr": len(beurten) + 1, "ronde": 1, "spreker": rol,
                        "soort": "bericht", "tekst": f"{record}: fictieve testwaarneming."})
    return {"run_id": "test", "status": "klaar", "raadsleden": ROLLEN.copy(),
            "beurten": beurten, "geschillen": []}


class BewijsTests(unittest.TestCase):
    def test_json_met_codeblok_en_uitleg(self):
        self.assertEqual(lees_json('Antwoord:\n```json\n{"rol": null}\n```'), {"rol": None})

    def test_ongeldig_json(self):
        with self.assertRaises(ValueError):
            lees_json("geen JSON")

    def test_ids_normaliseren_zonder_andere_tekst_te_wijzigen(self):
        data = {"bewijs": ["ORA‑001"], "tekst": "A–B"}
        self.assertEqual(normaliseer_ids(data), {"bewijs": ["ORA-001"], "tekst": "A–B"})

    def test_koning_kan_geen_bewijs_inbrengen(self):
        beurten = trace()["beurten"] + [{"soort": "bericht", "spreker": "koning", "tekst": "ARC-999"}]
        self.assertNotIn("ARC-999", debat_ids(beurten, ROLLEN))

    def test_onbekend_bewijs_wordt_geweigerd(self):
        with self.assertRaises(ValueError):
            toets_bewijs({"bewijs": ["ENG-999"]}, {"ENG-001"})

    def test_onbekend_id_in_vrije_tekst_wordt_geweigerd(self):
        with self.assertRaises(ValueError):
            toets_bewijs({"reden": "Zie ENG-999"}, {"ENG-001"})

    def test_bestaand_bewijs_is_toegelaten(self):
        toets_bewijs(verdict(), {"ENG-001"})

    def test_stellig_oorzaakdeel_zonder_bewijs_faalt_schema(self):
        data = verdict()
        data["oorzaak"]["ingreep"]["bewering"] = "Een onbewezen verklaring."
        schema = json.loads((PROJECT / "schema/verdict.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            toets_schema(data, schema)


class RouteringTests(unittest.TestCase):
    def keuze(self, rol):
        return {"rol": rol, "vraag": None if rol is None else "Wat is je bewijs?",
                "reden": "Toets het ontbrekende perspectief.", "open_vragen": [], "hypothese": HYP}

    def test_stoppen_mag_na_drie_rollen(self):
        toets_routering(self.keuze(None), trace()["beurten"], ROLLEN)

    def test_stoppen_mag_niet_voor_drie_rollen(self):
        with self.assertRaises(ValueError):
            toets_routering(self.keuze(None), [], ROLLEN)

    def test_onbekende_rol_wordt_geweigerd(self):
        with self.assertRaises(ValueError):
            toets_routering(self.keuze("onbekend"), [], ROLLEN)

    def test_vraag_is_verplicht(self):
        data = self.keuze("engineer")
        data["vraag"] = None
        with self.assertRaises(ValueError):
            toets_routering(data, [], ROLLEN)

    def test_laatste_beurten_reserveren_voor_ontbrekende_rollen(self):
        beurten = [{"soort": "bericht", "spreker": "engineer", "tekst": "test"}] * 8
        with self.assertRaises(ValueError):
            toets_routering(self.keuze("engineer"), beurten, ROLLEN)
        toets_routering(self.keuze("oracle"), beurten, ROLLEN)


class SpelregelTests(unittest.TestCase):
    def test_geldige_trace(self):
        self.assertEqual(validate.spelregels(trace()), [])

    def test_routering_is_verplicht(self):
        data = trace()
        data["beurten"][3]["aan"] = "oracle"
        self.assertTrue(any("geen Routering" in f for f in validate.spelregels(data)))

    def test_geen_bron_van_andere_rol(self):
        data = trace()
        data["beurten"][0]["bestand"] = "oracle/test.md"
        self.assertTrue(any("buiten de eigen Rol" in f for f in validate.spelregels(data)))

    def test_koning_mag_geen_bron_lezen(self):
        data = trace()
        data["beurten"][0]["spreker"] = "koning"
        self.assertTrue(validate.spelregels(data))

    def test_beurtenbudget(self):
        data = trace()
        for _ in range(8):
            data["beurten"].extend(copy.deepcopy(data["beurten"][3:5]))
        self.assertTrue(any("Beurtenbudget" in f for f in validate.spelregels(data)))

    def test_niet_afgeronde_run_faalt(self):
        data = trace()
        data["status"] = "fout"
        self.assertTrue(any("niet succesvol" in f for f in validate.spelregels(data)))

    def test_mcp_pad_van_andere_rol_wordt_geweigerd(self):
        data = trace()
        data["beurten"][0].update(soort="toolcall", tool="read", argumenten={},
                                  pad="https://example.invalid/oracle/mcp")
        self.assertTrue(any("eigen MCP-pad" in f for f in validate.spelregels(data)))

    def test_mcp_toolresultaat_moet_succesvol_zijn(self):
        call = Content.from_function_call(call_id="test", name="read", arguments={})
        for exception, verwacht in ((None, True), ("failed", False), ("", False)):
            with self.subTest(exception=exception):
                result = Content.from_function_result(call_id="test", result="testdata", exception=exception)
                response = SimpleNamespace(messages=[Message("assistant", [call]), Message("tool", [result])])
                self.assertEqual(council.bron_geraadpleegd(response), verwacht)
        self.assertFalse(council.bron_geraadpleegd(SimpleNamespace(messages=[Message("assistant", [call])])))


class ModelAntwoordTests(unittest.IsolatedAsyncioTestCase):
    async def test_ongeldig_antwoord_wordt_hersteld_en_verbruik_geteld(self):
        koning = SimpleNamespace(run=AsyncMock(side_effect=[
            SimpleNamespace(text="geen JSON", usage_details={"input_token_count": 5}),
            SimpleNamespace(text='{"ok": true}', usage_details={"input_token_count": 7}),
        ]))
        verbruik = {}
        data = await council.vraag_json(koning, "test", {"type": "object"}, lambda _: None, None, verbruik)
        self.assertTrue(data["ok"])
        self.assertEqual(verbruik["groot"]["invoer"], 12)
        self.assertEqual(koning.run.await_count, 2)

    async def test_drie_foute_antwoorden_stoppen_de_run(self):
        koning = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(text="geen JSON", usage_details={})))
        with self.assertRaisesRegex(ValueError, "na drie pogingen"):
            await council.vraag_json(koning, "test", {"type": "object"}, lambda _: None, None, {})
        self.assertEqual(koning.run.await_count, 3)


class RaadslidBeurtTests(unittest.IsolatedAsyncioTestCase):
    lid = SimpleNamespace(NAAM="Engineer", ROL="engineer")

    @staticmethod
    def antwoord(tekst, messages=()):
        return SimpleNamespace(text=tekst, messages=list(messages), usage_details={"input_token_count": 1})

    @staticmethod
    def mcp_berichten(resultaat):
        call = Content.from_function_call(call_id="c", name="zoek", arguments='{"q": "test"}')
        return [Message("assistant", [call]),
                Message("tool", [Content.from_function_result(call_id="c", result=resultaat)])]

    async def test_onbekend_id_krijgt_herkansing(self):
        agent = SimpleNamespace(run=AsyncMock(side_effect=[
            self.antwoord("ENG-999 verzonnen."), self.antwoord("ENG-001 uit mijn bron."),
        ]))
        calls, tekst, onbevestigd = await council.laat_spreken(
            self.lid, None, agent, "vraag", None, {}, {"ENG-001"}, set())
        self.assertEqual((tekst, onbevestigd, calls), ("ENG-001 uit mijn bron.", [], []))
        self.assertIn("ENG-999", agent.run.await_args_list[1].args[0])

    async def test_hardnekkig_onbekend_id_wordt_onbevestigd(self):
        agent = SimpleNamespace(run=AsyncMock(return_value=self.antwoord("ENG-999 en ORA-001.")))
        _, _, onbevestigd = await council.laat_spreken(
            self.lid, None, agent, "vraag", None, {}, set(), {"ORA-001"})
        self.assertEqual(onbevestigd, ["ENG-999"])

    async def test_ids_uit_mcp_resultaat_zijn_eigen_bron(self):
        agent = SimpleNamespace(run=AsyncMock(return_value=self.antwoord(
            "ENG‑002 gelezen.", self.mcp_berichten("ENG-002: testrecord"))))
        eigen = set()
        calls, _, onbevestigd = await council.laat_spreken(
            self.lid, "https://x.invalid/engineer/mcp", agent, "vraag", None, {}, eigen, set())
        self.assertEqual((onbevestigd, eigen, calls), ([], {"ENG-002"}, [("zoek", {"q": "test"})]))

    async def test_mcp_zonder_toolgebruik_krijgt_herkansing_en_breekt_daarna_af(self):
        agent = SimpleNamespace(run=AsyncMock(return_value=self.antwoord("Zonder bron.")))
        with self.assertRaisesRegex(RuntimeError, "MCP-bron"):
            await council.laat_spreken(self.lid, "https://x.invalid/engineer/mcp", agent, "v", None, {}, set(), set())
        self.assertEqual(agent.run.await_count, council.POGINGEN_RAADSLID)

    async def test_frameworkmelding_is_geen_bijdrage_en_herkansing_krijgt_verse_sessie(self):
        mcp = "https://x.invalid/engineer/mcp"
        oud, nieuw = object(), object()
        agent = SimpleNamespace(run=AsyncMock(side_effect=[
            self.antwoord("Function invocation limit reached before a final answer could be produced.",
                          self.mcp_berichten("ENG-002: testrecord")),
            self.antwoord("ENG-002 gelezen.", self.mcp_berichten("ENG-002: testrecord")),
        ]))
        _, tekst, _ = await council.laat_spreken(
            self.lid, mcp, agent, "kort", None, {}, set(), set(), oud, lambda: (nieuw, "volledig debat"))
        self.assertEqual(tekst, "ENG-002 gelezen.")
        tweede = agent.run.await_args_list[1]
        self.assertIs(tweede.kwargs["session"], nieuw)
        self.assertIn("volledig debat", tweede.args[0])

    def test_onbevestigde_ids_tellen_niet_als_bewijs(self):
        beurten = [{"soort": "bericht", "spreker": "engineer", "tekst": "ENG-001 en ENG-999",
                    "onbevestigd": ["ENG-999"]}]
        self.assertEqual(debat_ids(beurten, ROLLEN), {"ENG-001"})

    def test_ids_in_ge_escapete_brontekst(self):
        self.assertEqual(council.bron_ids("rij\\nENG-015,14,x\\nENG-016,15"), {"ENG-015", "ENG-016"})
        self.assertEqual(council.bron_ids("XENG-001 en ENG-0012"), set())

    def test_toolresultaat_als_lijst_van_content(self):
        result = Content.from_function_result(call_id="c", result=[Content.from_text("ENG-003,dag 2")])
        result.result = [Content.from_text("ENG-003,dag 2")]  # vorm zoals MCP die levert
        response = SimpleNamespace(messages=[Message("tool", [result])])
        self.assertEqual(council.bron_ids(council.toolresultaten(response)), {"ENG-003"})

    def test_koning_mag_geen_premisse_verzinnen(self):
        beurten = [{"soort": "bericht", "spreker": "engineer", "tekst": "ENG-001 om 04:15 op dag 22."}]
        keuze = {"rol": "oracle", "vraag": "Wat gebeurde om 14:32?", "reden": "Toetsen.", "open_vragen": [], "hypothese": HYP}
        with self.assertRaisesRegex(ValueError, "14:32"):
            toets_routering(keuze, beurten, ROLLEN)
        with self.assertRaisesRegex(ValueError, "ORA-007"):
            toets_routering({**keuze, "vraag": "Wat zegt ORA-007?"}, beurten, ROLLEN)
        toets_routering({**keuze, "vraag": "Wat zag je om 04:15 rond ENG-001?"}, beurten, ROLLEN)

    def test_hypothese_mag_geen_onbekende_ids_bevatten(self):
        beurten = [{"soort": "bericht", "spreker": "engineer", "tekst": "ENG-001 op dag 22."}]
        keuze = {"rol": "oracle", "vraag": "Wat zie je rond ENG-001?", "reden": "Toetsen.", "open_vragen": [],
                 "hypothese": {**HYP, "ingreep": "Een ingreep (ENG-002)."}}
        with self.assertRaisesRegex(ValueError, "ENG-002"):
            toets_routering(keuze, beurten, ROLLEN)

    def test_budget_op_dwingt_stoppen_af(self):
        beurten = [{"soort": "bericht", "spreker": r, "tekst": "t"} for r in ROLLEN] * 4
        with self.assertRaisesRegex(ValueError, "Beurtenbudget"):
            toets_routering({"rol": "engineer", "vraag": "v", "reden": "r", "open_vragen": [], "hypothese": HYP}, beurten, ROLLEN)


class VolledigeRunTests(unittest.TestCase):
    def test_echte_framework_met_lokaal_gesimuleerd_endpoint(self):
        """Oefen HTTP, modelkeuzes, bronnen, synthese, bestanden en CLI-validator samen."""
        requests, route_index, small_index = [], [0], [0]

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(request)
                prompt = request["messages"][-1]["content"]
                if request["model"] == "test-klein":
                    record = ("ENG-001", "ORA-001", "HIS-001", "ENG-001")[small_index[0]]
                    small_index[0] += 1
                    antwoord = f"{record}: fictieve testwaarneming; de oorzaak is nog onbekend."
                elif "Kies wie nu spreekt" in prompt:
                    index = route_index[0]
                    route_index[0] += 1
                    volgorde = [*ROLLEN, "engineer"]  # de Engineer spreekt twee keer: sessiegeheugen
                    antwoord = json.dumps({
                        "rol": volgorde[index] if index < 4 else None,
                        "vraag": "Wat staat in je eigen testbron?" if index < 4 else None,
                        "reden": "Ontbrekend perspectief toetsen." if index < 4 else "Beschikbare testkennis is verzameld.",
                        "open_vragen": ["Wat is de oorzaak?"], "hypothese": HYP,
                    })
                else:
                    run_id = re.search(r'Gebruik run_id "([^"]+)"', prompt).group(1)
                    antwoord = json.dumps({"verdict": verdict(run_id), "geschillen": []})
                payload = json.dumps({
                    "id": "test-completion", "object": "chat.completion", "created": 1,
                    "model": request["model"],
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": antwoord},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        with tempfile.TemporaryDirectory() as tmp, ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            root = Path(tmp)
            bronnen = root / "kennisbronnen"
            (root / "schema").mkdir()
            for naam in ("trace.json", "verdict.json"):
                (root / "schema" / naam).write_bytes((PROJECT / "schema" / naam).read_bytes())
            for rol, record in zip(ROLLEN, ("ENG-001", "ORA-001", "HIS-001")):
                (bronnen / rol).mkdir(parents=True)
                (bronnen / rol / "test.md").write_text(
                    f"Alleen fictieve testdata voor {rol}. {record}: fictieve testwaarneming.", encoding="utf-8")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            env = {"OPENAI_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
                   "OPENAI_API_KEY": "test", "MODEL_KLEIN": "test-klein", "MODEL_GROOT": "test-groot"}
            try:
                with patch.dict(os.environ, env, clear=True), patch.object(council, "ROOT", root), \
                     patch.object(council, "KENNISBRONNEN", bronnen), patch.object(validate, "ROOT", root), \
                     contextlib.redirect_stdout(io.StringIO()):
                    asyncio.run(council.run())
                    with self.assertRaises(SystemExit) as einde:
                        validate.main()
                    self.assertEqual(einde.exception.code, 0)
                uitvoer = json.loads((root / "trace.json").read_text(encoding="utf-8"))
                besluit = json.loads((root / "verdict.json").read_text(encoding="utf-8"))
                self.assertEqual(uitvoer["status"], "klaar")
                self.assertEqual(besluit["run_id"], uitvoer["run_id"])
                self.assertEqual(uitvoer["beurten"][-2]["aan"], None)
                self.assertEqual(uitvoer["verbruik"]["groot"]["beurten"], 6)
                self.assertEqual(len(requests), 10)
                # Tweede Engineer-beurt: eerdere vraag en antwoord zitten in de sessie, het prompt is alleen het nieuwe.
                engineer = [r for r in requests if r["model"] == "test-klein"
                            and "Engineer" in r["messages"][0]["content"]]
                self.assertEqual(len(engineer), 2)
                tweede = engineer[1]["messages"]
                self.assertTrue(any(m["role"] == "assistant" and "ENG-001" in str(m["content"]) for m in tweede))
                self.assertIn("Nieuw in het debat", tweede[-1]["content"])
                self.assertNotIn("Debat tot nu toe", tweede[-1]["content"])
                # De Koning ziet geen ruwe bestanden; elke Rol ziet alleen het eigen bronbestand.
                for request in requests:
                    systeem = request["messages"][0]["content"]
                    if request["model"] == "test-groot":
                        self.assertNotIn("Alleen fictieve testdata", systeem + request["messages"][-1]["content"])
                    else:
                        self.assertEqual(systeem.count("Alleen fictieve testdata"), 1)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
