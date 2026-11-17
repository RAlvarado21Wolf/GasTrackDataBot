import unittest

from bot.config import DEPARTMENTS
from bot.mem_service import find_report_url, parse_report_text
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


if __name__ == "__main__":
    unittest.main()
