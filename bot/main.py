from bot.ai.gemini_service import GeminiService
from bot.prompt import build_research_prompt, build_missing_departments_prompt

from bot.models import ResearchReport

from bot.normalizer import normalize_report

from bot.research_merge import merge_reports

from bot.updater import save_report

VERSION = "3.3.0"


def main():

    print("=" * 70)
    print("GasTrackDataBot")
    print(f"Versión {VERSION}")
    print("=" * 70)

    print()

    try:

        # ====================================================
        # GEMINI
        # ====================================================

        gemini = GeminiService()

        # ====================================================
        # RONDA 1
        # ====================================================

        print("[Gemini] Iniciando investigación nacional...")

        print()

        primary_prompt = build_research_prompt()

        primary_response = gemini.research(primary_prompt)

        print()

        print("[Bot] Procesando investigación principal...")

        primary_report = gemini.parse_report(primary_response, expected_count=22)

        # ====================================================
        # NORMALIZAR SIN PROXIES
        # ====================================================

        primary_departments = normalize_report(primary_report, apply_proxies=False)

        # ====================================================
        # DETECTAR FALTANTES
        # ====================================================

        missing_departments = []

        for department, data in primary_departments.items():

            if data["data_type"] == "not_found":

                missing_departments.append(department)

        print()

        print("=" * 70)
        print("PRIMERA RONDA")
        print("=" * 70)

        print(f"Encontrados: " f"{22 - len(missing_departments)}/22")

        print(f"Faltantes: " f"{len(missing_departments)}/22")

        # ====================================================
        # RONDA 2
        # ====================================================

        if missing_departments:

            print()

            print("=" * 70)
            print("SEGUNDA RONDA DE INVESTIGACIÓN")
            print("=" * 70)

            for department in missing_departments:

                print(f"  - {department}")

            print()

            secondary_prompt = build_missing_departments_prompt(missing_departments)

            secondary_response = gemini.research(secondary_prompt)

            print()

            print("[Bot] Procesando segunda ronda...")

            secondary_report = gemini.parse_report(
                secondary_response, expected_count=len(missing_departments)
            )

        else:

            print()

            print("[Bot] No existen departamentos " "faltantes.")

            secondary_report = ResearchReport(
                research_date=(primary_report.research_date), records=[]
            )

        # ====================================================
        # COMBINAR
        # ====================================================

        print()

        print("[Bot] Combinando investigaciones...")

        merged_records = merge_reports(primary_report, secondary_report)

        merged_report = ResearchReport(
            research_date=(primary_report.research_date), records=merged_records
        )

        # ====================================================
        # NORMALIZAR FINALMENTE
        # ====================================================

        departments = normalize_report(merged_report, apply_proxies=True)

        # ====================================================
        # COBERTURA
        # ====================================================

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

        # ====================================================
        # MOSTRAR COBERTURA
        # ====================================================

        print()

        print("=" * 70)
        print("COBERTURA FINAL GAS TRACK GT")
        print("=" * 70)

        print(f"Observados:             {observed}/22")

        print(f"Referencias regionales: {estimated}/22")

        print(f"Sin datos:              {not_found}/22")

        print(f"Cobertura:              " f"{observed + estimated}/22")

        # ====================================================
        # MOSTRAR RESULTADOS
        # ====================================================

        print()

        print("=" * 70)
        print("DETALLE POR DEPARTAMENTO")
        print("=" * 70)

        for department, data in departments.items():

            print()

            print(department)

            print(f"  Superior: " f"{data.get('superior')}")

            print(f"  Regular:  " f"{data.get('regular')}")

            print(f"  Diésel:   " f"{data.get('diesel')}")

            print(f"  Fecha:    " f"{data.get('price_date')}")

            print(f"  Fuente:   " f"{data.get('source')}")

            print(f"  Estado:   " f"{data.get('freshness')}")

            print(f"  Tipo:     " f"{data.get('data_type')}")

            if data.get("reference_department"):

                print("  Referencia: " f"{data.get('reference_department')}")

        # ====================================================
        # GUARDAR
        # ====================================================

        print()

        print("[Bot] Guardando datos...")

        current_path, history_path = save_report(
            departments, {"queries": [], "sources": []}
        )

        # ====================================================
        # COMPLETADO
        # ====================================================

        print()

        print("=" * 70)
        print("ACTUALIZACIÓN COMPLETADA")
        print("=" * 70)

        print(f"Current: {current_path}")

        print(f"History: {history_path}")

    except Exception as error:

        print()

        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(f"{type(error).__name__}")

        print(str(error))


if __name__ == "__main__":

    main()
