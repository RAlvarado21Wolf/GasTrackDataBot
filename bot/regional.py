# bot/regional.py


# ============================================================
# REFERENCIAS REGIONALES TEMPORALES
# ============================================================
#
# Estas referencias NO significan que los departamentos tengan
# necesariamente los mismos precios.
#
# Son utilizadas únicamente cuando no encontramos un precio
# directamente observado.
#
# Para V1:
#
# Guatemala       -> referencia central/nacional
# Quetzaltenango  -> referencia occidental
# Sacatepéquez    -> referencia altiplano/central
#
# Este mapa puede mejorarse posteriormente cuando GasTrack
# tenga más datos reales.
# ============================================================

REGIONAL_PROXIES = {
    # Occidente
    "Huehuetenango": "Quetzaltenango",
    "San Marcos": "Quetzaltenango",
    "Totonicapán": "Quetzaltenango",
    "Quiché": "Quetzaltenango",
    "Suchitepéquez": "Quetzaltenango",
    "Retalhuleu": "Quetzaltenango",
    # Altiplano / centro
    "Chimaltenango": "Sacatepéquez",
    "Sololá": "Sacatepéquez",
    # Oriente
    # NOTA:
    # Se utilizan como proxy temporal.
    # No implica equivalencia geográfica.
    "Chiquimula": "Sacatepéquez",
    "Zacapa": "Sacatepéquez",
    "Jalapa": "Sacatepéquez",
    "Jutiapa": "Sacatepéquez",
    "El Progreso": "Sacatepéquez",
    # Costa / sur
    "Escuintla": "Sacatepéquez",
    "Santa Rosa": "Sacatepéquez",
    # Norte
    "Alta Verapaz": "Guatemala",
    "Baja Verapaz": "Guatemala",
    "Petén": "Guatemala",
    "Izabal": "Guatemala",
}


def apply_regional_proxies(departments):
    """
    Completa departamentos sin datos observados utilizando
    temporalmente otra fuente departamental.

    Nunca reemplaza un dato observado.
    """

    result = {}

    # --------------------------------------------------------
    # Primero copiamos todos los departamentos
    # --------------------------------------------------------

    for department, data in departments.items():

        item = dict(data)

        item.setdefault("data_type", "observed")

        item.setdefault("reference_department", None)

        item.setdefault("reference_age_days", None)

        item.setdefault("reference_freshness", None)

        result[department] = item

    # --------------------------------------------------------
    # Aplicar referencias
    # --------------------------------------------------------

    for department, reference in REGIONAL_PROXIES.items():

        current = result.get(department)
        source = result.get(reference)

        if current is None:
            continue

        if source is None:
            continue

        # Si ya tenemos un precio observado, NO lo tocamos.
        if (
            current.get("superior") is not None
            or current.get("regular") is not None
            or current.get("diesel") is not None
        ):
            continue

        # La referencia tampoco tiene datos.
        if (
            source.get("superior") is None
            and source.get("regular") is None
            and source.get("diesel") is None
        ):
            continue

        # ----------------------------------------------------
        # Copiar datos de referencia
        # ----------------------------------------------------

        current["superior"] = source.get("superior")
        current["regular"] = source.get("regular")
        current["diesel"] = source.get("diesel")

        current["price_date"] = source.get("price_date")
        current["modality"] = source.get("modality")

        current["source"] = source.get("source")
        current["source_type"] = source.get("source_type")
        current["source_url"] = source.get("source_url")

        # ----------------------------------------------------
        # Marcar explícitamente como estimación regional
        # ----------------------------------------------------

        current["data_type"] = "regional_estimate"

        current["reference_department"] = reference

        current["reference_age_days"] = source.get("age_days")

        current["reference_freshness"] = source.get("freshness")

    return result
