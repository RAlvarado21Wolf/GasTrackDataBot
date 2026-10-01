# bot/normalizer.py

from datetime import datetime
from zoneinfo import ZoneInfo

from bot.config import TIMEZONE, DEPARTMENTS
from bot.regional import apply_regional_proxies

# ============================================================
# CALCULAR ANTIGÜEDAD
# ============================================================


def calculate_age_days(price_date):

    if price_date is None:
        return None

    try:

        price_day = datetime.strptime(price_date, "%Y-%m-%d").date()

    except ValueError:

        return None

    today = datetime.now(ZoneInfo(TIMEZONE)).date()

    return (today - price_day).days


# ============================================================
# DETERMINAR FRESCURA
# ============================================================


def calculate_freshness(age_days):

    if age_days is None:

        return "unknown"

    if age_days <= 7:

        return "recent"

    if age_days <= 30:

        return "aging"

    return "historical"


# ============================================================
# NORMALIZAR REPORTE
# ============================================================


def normalize_report(report, apply_proxies=True):

    departments = {}

    # --------------------------------------------------------
    # Procesar registros recibidos
    # --------------------------------------------------------

    for record in report.records:

        age_days = calculate_age_days(record.price_date)

        freshness = calculate_freshness(age_days)

        # ----------------------------------------------------
        # Determinar si realmente tiene datos
        # ----------------------------------------------------

        has_price = (
            record.superior is not None
            or record.regular is not None
            or record.diesel is not None
        )

        if has_price:

            data_type = "observed"

        else:

            data_type = "not_found"

        departments[record.department] = {
            "superior": record.superior,
            "regular": record.regular,
            "diesel": record.diesel,
            "price_date": record.price_date,
            "modality": record.modality,
            "source": record.source,
            "source_type": record.source_type,
            "source_url": record.source_url,
            "age_days": age_days,
            "freshness": freshness,
            "data_type": data_type,
            "reference_department": None,
            "reference_age_days": None,
            "reference_freshness": None,
        }

    # --------------------------------------------------------
    # Garantizar los 22 departamentos
    # --------------------------------------------------------

    for department in DEPARTMENTS:

        if department not in departments:

            departments[department] = {
                "superior": None,
                "regular": None,
                "diesel": None,
                "price_date": None,
                "modality": None,
                "source": None,
                "source_type": None,
                "source_url": None,
                "age_days": None,
                "freshness": "unknown",
                "data_type": "not_found",
                "reference_department": None,
                "reference_age_days": None,
                "reference_freshness": None,
            }

    # --------------------------------------------------------
    # Aplicar proxies solamente si se solicita
    # --------------------------------------------------------

    if apply_proxies:

        departments = apply_regional_proxies(departments)

    return departments
