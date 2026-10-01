import json

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.config import TIMEZONE

# ============================================================
# DIRECTORIOS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"

HISTORY_DIR = ROOT / "history"


# ============================================================
# GUARDAR REPORTE
# ============================================================


def save_report(departments, grounding):

    # --------------------------------------------------------
    # Crear directorios si no existen
    # --------------------------------------------------------

    DATA_DIR.mkdir(exist_ok=True)

    HISTORY_DIR.mkdir(exist_ok=True)

    # --------------------------------------------------------
    # Fecha/hora Guatemala
    # --------------------------------------------------------

    now = datetime.now(ZoneInfo(TIMEZONE))

    # --------------------------------------------------------
    # Estadísticas
    # --------------------------------------------------------

    observed = 0
    estimated = 0
    not_found = 0

    for data in departments.values():

        data_type = data.get("data_type")

        if data_type == "observed":

            observed += 1

        elif data_type == "regional_estimate":

            estimated += 1

        elif data_type == "not_found":

            not_found += 1

    # --------------------------------------------------------
    # Construir JSON
    # --------------------------------------------------------

    payload = {
        "schema_version": "1.1",
        "updated_at": now.isoformat(),
        "collection_method": "Gemini + Google Search Grounding",
        "coverage": {
            "total_departments": len(departments),
            "observed": observed,
            "regional_estimate": estimated,
            "not_found": not_found,
            "covered": observed + estimated,
        },
        "departments": departments,
        "research": {
            "queries": grounding.get("queries", []),
            "sources": grounding.get("sources", []),
        },
    }

    # --------------------------------------------------------
    # Archivo actual
    # --------------------------------------------------------

    current_path = DATA_DIR / "current.json"

    # --------------------------------------------------------
    # Archivo histórico
    # --------------------------------------------------------

    history_path = HISTORY_DIR / f"{now:%Y-%m-%d}.json"

    # --------------------------------------------------------
    # Guardar current.json
    # --------------------------------------------------------

    with current_path.open("w", encoding="utf-8") as file:

        json.dump(payload, file, ensure_ascii=False, indent=4)

    # --------------------------------------------------------
    # Guardar histórico
    # --------------------------------------------------------

    with history_path.open("w", encoding="utf-8") as file:

        json.dump(payload, file, ensure_ascii=False, indent=4)

    return (current_path, history_path)
