# bot/config.py

import os

from dotenv import load_dotenv

# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

load_dotenv()


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Modelo principal
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================
# CONFIGURACIÓN DE INVESTIGACIÓN
# ============================================================

MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "5"))

INITIAL_RETRY_DELAY = float(os.getenv("GEMINI_INITIAL_RETRY_DELAY", "3"))

MAX_RETRY_DELAY = float(os.getenv("GEMINI_MAX_RETRY_DELAY", "30"))


# ============================================================
# ZONA HORARIA
# ============================================================

TIMEZONE = "America/Guatemala"


# ============================================================
# DEPARTAMENTOS
# ============================================================

DEPARTMENTS = [
    "Alta Verapaz",
    "Baja Verapaz",
    "Chimaltenango",
    "Chiquimula",
    "El Progreso",
    "Escuintla",
    "Guatemala",
    "Huehuetenango",
    "Izabal",
    "Jalapa",
    "Jutiapa",
    "Petén",
    "Quetzaltenango",
    "Quiché",
    "Retalhuleu",
    "Sacatepéquez",
    "San Marcos",
    "Santa Rosa",
    "Sololá",
    "Suchitepéquez",
    "Totonicapán",
    "Zacapa",
]


# ============================================================
# VALIDACIONES
# ============================================================

if not GEMINI_API_KEY:

    raise RuntimeError("No se encontró GEMINI_API_KEY en el archivo .env")
