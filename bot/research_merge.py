# bot/research_merge.py


def merge_reports(primary_report, secondary_report):
    """
    Combina la investigación principal con la segunda ronda.

    La segunda ronda solamente puede completar departamentos
    que no tenían datos en la primera.
    """

    records = {}

    # ========================================================
    # PRIMERA RONDA
    # ========================================================

    for record in primary_report.records:

        records[record.department] = record

    # ========================================================
    # SEGUNDA RONDA
    # ========================================================

    for record in secondary_report.records:

        current = records.get(record.department)

        if current is None:

            records[record.department] = record

            continue

        # ----------------------------------------------------
        # Determinar si la primera ronda tenía precio
        # ----------------------------------------------------

        current_has_price = (
            current.superior is not None
            or current.regular is not None
            or current.diesel is not None
        )

        # ----------------------------------------------------
        # Determinar si segunda ronda tiene precio
        # ----------------------------------------------------

        secondary_has_price = (
            record.superior is not None
            or record.regular is not None
            or record.diesel is not None
        )

        # ----------------------------------------------------
        # Solo reemplazar si la primera ronda no tenía datos
        # ----------------------------------------------------

        if not current_has_price and secondary_has_price:

            records[record.department] = record

    return list(records.values())
