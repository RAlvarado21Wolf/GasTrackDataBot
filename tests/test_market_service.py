import unittest
from unittest.mock import patch

from bot.market_service import parse_exchange_rate, parse_wti


class MarketServiceTests(unittest.TestCase):
    @patch("bot.market_service._recent", return_value=True)
    def test_exchange_rate_keeps_five_decimals_and_date(self, _recent):
        html = "<p>Tipo de Cambio de Referencia vigente para el martes, 17 de noviembre de 2026</p><strong>7.63985</strong>"
        result = parse_exchange_rate(html)
        self.assertEqual(result["value"], 7.63985)
        self.assertEqual(result["date"], "2026-11-17")
        self.assertEqual(result["unit"], "GTQ/USD")

    @patch("bot.market_service._recent", return_value=True)
    def test_wti_uses_closing_date_and_barrel_unit(self, _recent):
        html = "<p>Wholesale Spot Petroleum Prices, 11/16/26 Close</p><table><tr><td>Crude Oil ($/barrel)</td><td>WTI</td><td>89.24</td><td>-3.0</td></tr></table>"
        result = parse_wti(html)
        self.assertEqual(result["value"], 89.24)
        self.assertEqual(result["date"], "2026-11-16")
        self.assertEqual(result["unit"], "USD/barrel")


if __name__ == "__main__":
    unittest.main()
