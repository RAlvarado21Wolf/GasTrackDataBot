import unittest
from unittest.mock import patch

from bot.config import DEPARTMENTS
from bot.mem_service import find_report_url, parse_report_text, fetch_mem_report, MEM_PAGE
from bot.validator import validate_report


class MemServiceTests(unittest.TestCase):
    def test_finds_official_pdf_link(self):
        html = '<a href="/wp-content/uploads/report.pdf">Informe de precios de combustibles a nivel nacional</a>'
        self.assertEqual(
            find_report_url(html),
            "https://mem.gob.gt/wp-content/uploads/report.pdf",
        )

    def test_parses_all_departments_with_date_and_source(self):
        rows = "\n".join(f"{name} Q33.19 Q30.86 Q41.49" for name in DEPARTMENTS)
        text = (
            "Fecha del Monitoreo del lunes, 9 de noviembre de 2026 "
            "al miércoles, 11 de noviembre de 2026\n"
            f"MODALIDAD: AUTOSERVICIO\n{rows}\nMODALIDAD: SERVICIO COMPLETO"
        )
        report = parse_report_text(text, "https://mem.gob.gt/report.pdf")
        self.assertEqual(len(report.records), 22)
        self.assertEqual(report.records[0].price_date, "2026-11-11")
        self.assertEqual(report.records[0].regular, 30.86)
        self.assertEqual(report.records[-1].department, "Zacapa")
        self.assertTrue(validate_report(report)["valid"])

    def test_rejects_partial_report(self):
        text = "Fecha del Monitoreo: 11 de noviembre de 2026\nMODALIDAD: AUTOSERVICIO\nGuatemala Q33.19 Q30.86 Q41.49"
        with self.assertRaisesRegex(ValueError, "Fila incompleta"):
            parse_report_text(text, "https://mem.gob.gt/report.pdf")

    def test_uses_direct_pdf_when_index_returns_403(self):
        source_url = "https://mem.gob.gt/wp-content/uploads/2026/11/report.pdf"

        class Response:
            def __init__(self, status, content=b""):
                self.status_code = status
                self.content = content

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise __import__("requests").HTTPError(str(self.status_code))

        class Session:
            headers = {}

            def get(self, url, timeout):
                if url == MEM_PAGE:
                    return Response(403)
                return Response(200, b"%PDF test") if url == source_url else Response(404)

        with patch("bot.mem_service.CURRENT_PATH") as current, patch("bot.mem_service._parse_pdf", return_value="report") as parse:
            current.exists.return_value = True
            current.read_text.return_value = '{"departments":{"Guatemala":{"source_type":"mem","source_url":"' + source_url + '"}}}'
            self.assertEqual(fetch_mem_report(Session()), "report")
            parse.assert_called_once_with(b"%PDF test", source_url)


if __name__ == "__main__":
    unittest.main()
