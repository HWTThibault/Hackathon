"""De viewer mag een run niet onderbreken door een korte Windows-bestandsblokkering."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import council


class TraceSchrijvenTests(unittest.TestCase):
    def test_tijdelijke_blokkering_behoudt_oude_trace_tot_nieuwe_klaar_is(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(council, "ROOT", Path(tmp)):
            pad = Path(tmp) / "trace.json"
            pad.write_text('{"status": "oud"}', encoding="utf-8")
            replace = os.replace
            pogingen = []

            def kort_geblokkeerd(bron, doel):
                pogingen.append(1)
                if len(pogingen) < 3:
                    self.assertEqual(json.loads(pad.read_text(encoding="utf-8"))["status"], "oud")
                    raise PermissionError("Tijdelijk geopend door een lezer")
                return replace(bron, doel)

            with patch("os.replace", side_effect=kort_geblokkeerd), patch.object(council.time, "sleep"):
                council.bewaar("trace.json", {"status": "klaar", "tekst": "Volledige uitvoer"})
            self.assertEqual(json.loads(pad.read_text(encoding="utf-8"))["tekst"], "Volledige uitvoer")

    def test_blijvende_blokkering_verliest_geen_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(council, "ROOT", Path(tmp)):
            pad = Path(tmp) / "trace.json"
            pad.write_text('{"status": "oud"}', encoding="utf-8")
            with patch("os.replace", side_effect=PermissionError("Blokkering")), patch.object(council.time, "sleep"):
                with self.assertRaises(PermissionError):
                    council.bewaar("trace.json", {"status": "nieuw"})
            self.assertEqual(json.loads(pad.read_text(encoding="utf-8"))["status"], "oud")
            self.assertEqual(json.loads(pad.with_suffix(".json.tmp").read_text(encoding="utf-8"))["status"], "nieuw")
