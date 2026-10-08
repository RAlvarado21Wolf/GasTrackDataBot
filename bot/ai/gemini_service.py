# bot/ai/gemini_service.py

import json
import random
import time

from google import genai
from google.genai import types

from bot.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
)

from bot.models import ResearchReport


class GeminiService:

    # ========================================================
    # INICIALIZACIÓN
    # ========================================================

    def __init__(self):

        self.model = GEMINI_MODEL

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print(f"[Gemini] Modelo: {self.model}")

    # ========================================================
    # INVESTIGACIÓN
    # ========================================================

    def research(self, prompt):

        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                print(
                    f"[Gemini] Intento "
                    f"{attempt}/{MAX_RETRIES}"
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(

                        # ------------------------------------
                        # Temperatura baja:
                        # queremos datos, no creatividad.
                        # ------------------------------------

                        temperature=0,

                        # ------------------------------------
                        # Google Search Grounding
                        # ------------------------------------

                        tools=[
                            types.Tool(
                                google_search=types.GoogleSearch()
                            )
                        ],
                    ),
                )

                # ====================================================
                # VALIDAR RESPUESTA
                # ====================================================

                if response is None:

                    raise RuntimeError(
                        "Gemini devolvió una respuesta vacía."
                    )

                response_text = response.text

                if not response_text:

                    raise RuntimeError(
                        "Gemini devolvió texto vacío."
                    )

                print(
                    "[Gemini] Investigación completada."
                )

                return response_text

            except Exception as error:

                last_error = error

                status_code = self._get_status_code(
                    error
                )

                print()

                print(
                    f"[Gemini] Error en intento "
                    f"{attempt}: "
                    f"{type(error).__name__}"
                )

                print(str(error))

                # ====================================================
                # DETERMINAR SI ES REINTENTABLE
                # ====================================================

                if not self._is_retryable_error(
                    error,
                    status_code
                ):

                    print(
                        "[Gemini] El error no parece "
                        "transitorio. "
                        "No se reintentará."
                    )

                    raise

                # ====================================================
                # ÚLTIMO INTENTO
                # ====================================================

                if attempt >= MAX_RETRIES:

                    print()

                    print(
                        "[Gemini] Se alcanzó el máximo "
                        "de reintentos."
                    )

                    print(
                        "[Gemini] La investigación "
                        "no pudo completarse."
                    )

                    raise

                # ====================================================
                # EXPONENTIAL BACKOFF
                # ====================================================

                delay = min(
                    INITIAL_RETRY_DELAY
                    * (2 ** (attempt - 1)),
                    MAX_RETRY_DELAY
                )

                # Pequeña variación para evitar
                # múltiples solicitudes simultáneas.

                jitter = random.uniform(0, 1)

                total_delay = delay + jitter

                print(
                    f"[Gemini] Error transitorio. "
                    f"Reintentando en "
                    f"{total_delay:.1f} segundos..."
                )

                time.sleep(total_delay)

        # ========================================================
        # SEGURIDAD
        # ========================================================

        if last_error is not None:

            raise last_error

        raise RuntimeError(
            "La investigación de Gemini "
            "terminó sin resultado."
        )

    # ========================================================
    # DETECTAR ERRORES TRANSITORIOS
    # ========================================================

    def _is_retryable_error(
        self,
        error,
        status_code=None
    ):

        # ====================================================
        # ERRORES HTTP TRANSITORIOS
        # ====================================================

        if status_code in (
            408,
            429,
            500,
            502,
            503,
            504,
        ):

            return True

        # ====================================================
        # NOMBRE DE LA EXCEPCIÓN
        # ====================================================

        error_type = type(error).__name__.lower()

        retryable_exception_names = [
            "remoteprotocolerror",
            "connectionerror",
            "connectionreseterror",
            "connectionabortederror",
            "timeout",
            "timeouterror",
            "readtimeout",
            "connecttimeout",
            "networkerror",
        ]

        for exception_name in retryable_exception_names:

            if exception_name in error_type:

                return True

        # ====================================================
        # MENSAJE DEL ERROR
        # ====================================================

        message = str(error).lower()

        retry_keywords = [

            # ------------------------------------
            # HTTP / Gemini
            # ------------------------------------

            "408",
            "429",
            "500",
            "502",
            "503",
            "504",

            "unavailable",
            "high demand",
            "temporarily",
            "temporarily unavailable",

            "rate limit",
            "resource exhausted",

            # ------------------------------------
            # Conexiones
            # ------------------------------------

            "remoteprotocolerror",
            "server disconnected",
            "disconnected without sending a response",

            "connection reset",
            "connection aborted",
            "connection error",

            "connection refused",
            "connection closed",

            "broken pipe",

            # ------------------------------------
            # Timeout
            # ------------------------------------

            "timeout",
            "timed out",
            "read timeout",
            "connect timeout",

            # ------------------------------------
            # Problemas temporales de red
            # ------------------------------------

            "temporary failure",
            "temporary error",
            "network error",
        ]

        for keyword in retry_keywords:

            if keyword in message:

                return True

        return False

    # ========================================================
    # OBTENER STATUS CODE
    # ========================================================

    def _get_status_code(
        self,
        error
    ):

        # ----------------------------------------------------
        # Algunos errores exponen .code
        # ----------------------------------------------------

        code = getattr(
            error,
            "code",
            None
        )

        if isinstance(code, int):

            return code

        # ----------------------------------------------------
        # Algunos errores exponen response.status_code
        # ----------------------------------------------------

        response = getattr(
            error,
            "response",
            None
        )

        if response is not None:

            status_code = getattr(
                response,
                "status_code",
                None
            )

            if isinstance(status_code, int):

                return status_code

        return None

    # ========================================================
    # PARSEAR REPORTE
    # ========================================================

    def parse_report(
        self,
        response_text,
        expected_count=None
    ):

        if not response_text:

            raise ValueError(
                "La respuesta de Gemini está vacía."
            )

        text = response_text.strip()

        # ========================================================
        # LIMPIAR MARKDOWN
        # ========================================================

        if text.startswith("```json"):

            text = text[7:]

        elif text.startswith("```"):

            text = text[3:]

        if text.endswith("```"):

            text = text[:-3]

        text = text.strip()

        # ========================================================
        # CONVERTIR JSON
        # ========================================================

        try:

            data = json.loads(text)

        except json.JSONDecodeError as error:

            print()

            print(
                "[Gemini] La respuesta "
                "no contiene JSON válido."
            )

            print()

            print(
                text[:2000]
            )

            raise ValueError(
                "Gemini no devolvió JSON válido."
            ) from error

        # ========================================================
        # VALIDAR CON PYDANTIC
        # ========================================================

        try:

            report = ResearchReport.model_validate(
                data
            )

        except Exception as error:

            raise ValueError(
                "El reporte de Gemini no "
                "cumple el esquema esperado."
            ) from error

        # ========================================================
        # VALIDAR CANTIDAD
        # ========================================================

        if expected_count is not None:

            if len(report.records) != expected_count:

                raise ValueError(
                    "Gemini devolvió "
                    f"{len(report.records)} registros. "
                    f"Se esperaban "
                    f"{expected_count}."
                )

        return report

    # ========================================================
    # EXTRAER FUENTES
    # ========================================================

    def extract_grounding_sources(
        self,
        response
    ):

        return {
            "queries": [],
            "sources": []
        }
