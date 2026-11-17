"""Indicadores públicos con fecha, unidad y fuente propias."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from bot.config import TIMEZONE

BANGUAT_URL = "https://www.banguat.gob.gt/tipo_cambio/"
EIA_URL = "https://www.eia.gov/TODAYINENERGY/prices.php"
MONTHS = {name: i for i, name in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1
)}


def _recent(day):
    age = (datetime.now(ZoneInfo(TIMEZONE)).date() - day).days
    return 0 <= age <= 7


def parse_exchange_rate(html):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    match = re.search(
        r"Tipo de Cambio de Referencia vigente para el\s+"
        r"(?:\w+,\s*)?(\d{1,2}) de (\w+) de (20\d{2})\s+"
        r"(\d{1,2}\.\d{4,5})",
        text, re.I,
    )
    if not match:
        raise ValueError("No se encontró tipo de cambio y fecha en Banguat")
    day = datetime(int(match[3]), MONTHS[match[2].lower()], int(match[1])).date()
    value = float(match[4])
    if not 5 <= value <= 12 or not _recent(day):
        raise ValueError("Tipo de cambio fuera de rango o antiguo")
    return {
        "value": value, "date": day.isoformat(), "unit": "GTQ/USD",
        "source": "Banco de Guatemala", "source_url": BANGUAT_URL,
    }


def parse_wti(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Wholesale Spot Petroleum Prices,\s*(\d{1,2}/\d{1,2}/\d{2})\s*Close", text, re.I)
    if not match:
        raise ValueError("No se encontró fecha de cierre WTI en EIA")
    day = datetime.strptime(match[1], "%m/%d/%y").date()
    row = next((tr.get_text(" ", strip=True) for tr in soup.find_all("tr") if re.search(r"\bWTI\b", tr.get_text(" ", strip=True))), "")
    price = re.search(r"\bWTI\s+\$?(\d{1,3}(?:\.\d{1,2})?)\b", row)
    if not price:
        raise ValueError("No se encontró precio WTI en EIA")
    value = float(price[1])
    if not 10 <= value <= 300 or not _recent(day):
        raise ValueError("Precio WTI fuera de rango o antiguo")
    return {
        "value": value, "date": day.isoformat(), "unit": "USD/barrel",
        "benchmark": "WTI", "source": "U.S. Energy Information Administration",
        "source_url": EIA_URL,
    }


def fetch_market(session=None):
    session = session or requests.Session()
    result = {}
    for name, url, parser in (
        ("exchange_rate", BANGUAT_URL, parse_exchange_rate),
        ("international_price", EIA_URL, parse_wti),
    ):
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            result[name] = parser(response.text)
        except (requests.RequestException, ValueError, KeyError) as error:
            print(f"[Mercado] {name} no disponible: {error}")
    return result
