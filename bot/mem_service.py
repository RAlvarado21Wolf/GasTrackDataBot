"""Lectura estricta del informe departamental oficial del MEM."""

import io
import re
import unicodedata
from datetime import date
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter

from bot.config import DEPARTMENTS
from bot.models import PriceRecord, ResearchReport

MEM_PAGE = (
    "https://mem.gob.gt/que-hacemos/hidrocarburos/"
    "comercializacion-downstream/precios-combustible-nacionales/"
)
REPORT_LABEL = "informe de precios de combustibles a nivel nacional"
PRICE = r"(?:Q\s*)?(\d{1,3}[.,]\d{2})"


def _fold(value):
    value = unicodedata.normalize("NFKD", value)
    return "".join(c for c in value if not unicodedata.combining(c)).casefold()


def find_report_url(html):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a", href=True):
        if REPORT_LABEL in _fold(link.get_text(" ", strip=True)):
            url = urljoin(MEM_PAGE, link["href"])
            if urlparse(url).hostname in {"mem.gob.gt", "www.mem.gob.gt"} and urlparse(url).path.lower().endswith(".pdf"):
                return url
    raise ValueError("No se encontró el informe departamental PDF en el MEM")


def parse_report_text(text, source_url):
    """Extrae solo la primera tabla de autoservicio, con 22 filas completas."""
    marker = re.search(r"MODALIDAD\s*:\s*AUTO\s*SERVICIO", text, re.I)
    if not marker:
        raise ValueError("El PDF no contiene la tabla de autoservicio")
    header = text[:marker.start()]
    dates = re.findall(r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(20\d{2})", header, re.I)
    if not dates:
        raise ValueError("No se encontró la fecha de monitoreo del MEM")
    months = {name: i for i, name in enumerate(
        "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1
    )}
    day, month, year = dates[-1]
    price_date = date(int(year), months[month.lower()], int(day)).isoformat()

    section = text[marker.end():]
    end = re.search(r"MODALIDAD\s*:\s*SERVICIO\s+COMPLETO|COMPARATIVO\s+DE\s+PRECIOS", section, re.I)
    if end:
        section = section[:end.start()]
    records = []
    for department in DEPARTMENTS:
        # Los nombres y tres precios pueden caer en líneas separadas en el PDF.
        name = re.escape(department).replace(r"\ ", r"\s+")
        match = re.search(
            rf"(?<!\w){name}(?!\w)\s+{PRICE}\s+{PRICE}\s+{PRICE}(?!\s+{PRICE})",
            section, re.I,
        )
        if not match:
            raise ValueError(f"Fila incompleta o ausente en el MEM: {department}")
        values = [float(value.replace(",", ".")) for value in match.groups()[:3]]
        records.append(PriceRecord(
            department=department, superior=values[0], regular=values[1],
            diesel=values[2], price_date=price_date, modality="autoservicio",
            source="Ministerio de Energía y Minas", source_type="mem", source_url=source_url,
        ))
    return ResearchReport(research_date=price_date, records=records)


def fetch_mem_report(session=None):
    session = session or requests.Session()
    page = session.get(MEM_PAGE, timeout=25)
    page.raise_for_status()
    pdf_url = find_report_url(page.text)
    pdf = session.get(pdf_url, timeout=35)
    pdf.raise_for_status()
    if not pdf.content.startswith(b"%PDF") or len(pdf.content) > 12_000_000:
        raise ValueError("El informe del MEM no es un PDF válido")
    reader = PdfReader(io.BytesIO(pdf.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages[:2])
    if text.strip():
        return parse_report_text(text, pdf_url)

    # Algunos informes del MEM son imágenes escaneadas y no contienen texto.
    # Gemini puede leer la primera página visualmente; se valida igual que el texto.
    first_page = PdfWriter()
    first_page.add_page(reader.pages[0])
    first_page_bytes = io.BytesIO()
    first_page.write(first_page_bytes)
    from bot.ai.gemini_service import GeminiService

    return GeminiService().extract_mem_pdf(first_page_bytes.getvalue(), pdf_url)
