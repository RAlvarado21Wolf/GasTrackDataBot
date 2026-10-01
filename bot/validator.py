from datetime import datetime

from bot.config import DEPARTMENTS, MIN_FUEL_PRICE, MAX_FUEL_PRICE


def validate_report(report):

    errors = []
    warnings = []

    records = report.records

    # ---------------------------------
    # 22 registros obligatorios
    # ---------------------------------

    if len(records) != 22:

        errors.append(f"Se esperaban 22 registros; " f"se recibieron {len(records)}.")

    names = [record.department for record in records]

    # ---------------------------------
    # Duplicados
    # ---------------------------------

    duplicates = {name for name in names if names.count(name) > 1}

    if duplicates:

        errors.append("Departamentos duplicados: " + ", ".join(sorted(duplicates)))

    # ---------------------------------
    # Faltantes
    # ---------------------------------

    missing = [department for department in DEPARTMENTS if department not in names]

    if missing:

        errors.append("Departamentos faltantes: " + ", ".join(missing))

    complete = 0

    # ---------------------------------
    # Validación individual
    # ---------------------------------

    for record in records:

        if record.department not in DEPARTMENTS:

            errors.append(f"Departamento desconocido: " f"{record.department}")

        prices = [record.superior, record.regular, record.diesel]

        if all(price is not None for price in prices):
            complete += 1

        for price in prices:

            if price is None:
                continue

            if not (MIN_FUEL_PRICE <= price <= MAX_FUEL_PRICE):

                errors.append(
                    f"{record.department}: " f"precio fuera de rango ({price})."
                )

        # Superior normalmente no debería
        # ser menor que Regular.

        if (
            record.superior is not None
            and record.regular is not None
            and record.superior < record.regular
        ):

            warnings.append(f"{record.department}: " "Superior es menor que Regular.")

        # ---------------------------------
        # Fecha
        # ---------------------------------

        if record.price_date:

            try:

                datetime.strptime(record.price_date, "%Y-%m-%d")

            except ValueError:

                errors.append(
                    f"{record.department}: "
                    f"fecha inválida "
                    f"({record.price_date})."
                )

        # ---------------------------------
        # Fuente
        # ---------------------------------

        if any(price is not None for price in prices):

            if not record.source:

                errors.append(f"{record.department}: " "tiene precios pero no fuente.")

            if not record.price_date:

                warnings.append(f"{record.department}: " "tiene precios pero no fecha.")

    return {
        "valid": len(errors) == 0,
        "records": len(records),
        "complete": complete,
        "errors": errors,
        "warnings": warnings,
    }
