"""Añade mercado y comparación previa al JSON actual sin alterar la fecha del combustible."""

import json
from pathlib import Path

from bot.config import DEPARTMENTS
from bot.market_service import fetch_market
from bot.updater import DATA_DIR, HISTORY_DIR


def _previous_observed(department, current_date):
    for path in sorted(HISTORY_DIR.glob("????-??-??.json"), reverse=True):
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        record = snapshot.get("departments", {}).get(department, {})
        price_date = record.get("price_date")
        if (
            record.get("data_type") == "observed"
            and price_date and current_date and price_date < current_date
            and record.get("regular") is not None
        ):
            return {
                "price_date": price_date,
                "regular": record.get("regular"),
                "superior": record.get("superior"),
                "diesel": record.get("diesel"),
                "source": record.get("source"),
                "source_url": record.get("source_url"),
            }
    return None


def enrich_current():
    path = DATA_DIR / "current.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    for name in DEPARTMENTS:
        record = current.get("departments", {}).get(name)
        if record:
            record["previous"] = _previous_observed(name, record.get("price_date"))

    market = dict(current.get("market") or {})
    market.update(fetch_market())
    current["market"] = market

    encoded = json.dumps(current, ensure_ascii=False, indent=4)
    if path.read_text(encoding="utf-8") != encoded:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(path)
        print("[Bot] Indicadores y precios anteriores actualizados.")
