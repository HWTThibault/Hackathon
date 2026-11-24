"""Een trace legt vraag, antwoord en ontvangers vast op het moment van de run."""
import unittest
from datetime import datetime

from tracebeheer import controleer_uitwisselingen, registreer_beurt
from validate import spelregels


class UitwisselingTests(unittest.TestCase):
    def setUp(self):
        self.trace = {"run_id": "test", "raadsleden": ["engineer", "oracle", "historian"],
                      "beurten": [], "geschillen": []}

    def test_antwoord_en_bronverzoek_zijn_gekoppeld_aan_de_vraag(self):
        route = registreer_beurt(self.trace, 1, "koning", "routering", aan="engineer",
                                vraag="Welke waarneming bewijst je bron?", reden="Meetbaar bewijs ontbreekt.")
        tool = registreer_beurt(self.trace, 1, "engineer", "toolcall", tool="lees_kennisbron",
                               argumenten={}, pad="https://example.invalid/engineer/mcp")
        antwoord = registreer_beurt(self.trace, 1, "engineer", "bericht", tekst="Een testwaarneming.")
        self.assertEqual(tool["in_antwoord_op"], route["nr"])
        self.assertEqual(antwoord["in_antwoord_op"], route["nr"])
        self.assertEqual(antwoord["ontvangers"], ["koning", "oracle", "historian"])
        self.assertIsNotNone(datetime.fromisoformat(antwoord["tijdstip"]).tzinfo)

    def test_context_verwijst_naar_eerdere_bijdragen(self):
        eerste = registreer_beurt(self.trace, 1, "engineer", "bericht", tekst="Eerste bijdrage.")
        registreer_beurt(self.trace, 1, "koning", "routering", aan="oracle", vraag="Toets dit.", reden="Kruiscontrole.")
        tweede = registreer_beurt(self.trace, 1, "oracle", "bericht", tekst="Tweede bijdrage.")
        self.assertEqual(tweede["context_beurten"], [eerste["nr"]])

    def test_geen_verzonnen_relatie_bij_verkeerde_routering(self):
        registreer_beurt(self.trace, 1, "koning", "routering", aan="oracle", vraag="Vraag.", reden="Reden.")
        antwoord = registreer_beurt(self.trace, 1, "engineer", "bericht", tekst="Bijdrage.")
        self.assertNotIn("in_antwoord_op", antwoord)

    def test_volledige_trace_met_uitwisselingen_volgt_spelregels(self):
        for rol in self.trace["raadsleden"]:
            registreer_beurt(self.trace, 0, rol, "bestand", bestand=f"{rol}/test.md")
            registreer_beurt(self.trace, 1, "koning", "routering", aan=rol, vraag="Vraag.", reden="Reden.")
            registreer_beurt(self.trace, 1, rol, "bericht", tekst="Bijdrage.")
        self.assertEqual(spelregels(self.trace), [])

    def test_toekomstig_antwoord_of_context_wordt_geweigerd(self):
        registreer_beurt(self.trace, 1, "engineer", "bericht", tekst="Bijdrage.", in_antwoord_op=99)
        self.trace["beurten"][0]["context_beurten"] = [99]
        fouten = controleer_uitwisselingen(self.trace)
        self.assertEqual(len(fouten), 2)

    def test_niet_deelnemende_ontvanger_wordt_geweigerd(self):
        registreer_beurt(self.trace, 1, "engineer", "bericht", tekst="Bijdrage.")
        self.trace["beurten"][0]["ontvangers"] = ["onbekend"]
        self.assertEqual(len(controleer_uitwisselingen(self.trace)), 1)
