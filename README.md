# GasTrackDataBot

Publica precios promedio de gasolina superior, regular y diésel por departamento de Guatemala, en quetzales por galón.

## Fuentes y actualización

El flujo diario de GitHub Actions consulta primero el [informe nacional del Ministerio de Energía y Minas](https://mem.gob.gt/que-hacemos/hidrocarburos/comercializacion-downstream/precios-combustible-nacionales/). Extrae la tabla de **autoservicio** del PDF enlazado. Cuando el PDF es escaneado y no contiene texto, Gemini lee visualmente su primera página. Solo publica si obtiene los 22 departamentos, los tres precios, la fecha de monitoreo y el enlace al informe. Si el mismo informe ya está guardado, conserva la fecha de actualización anterior.

Si el informe no está disponible, el bot usa Gemini con Google Search como respaldo. Esa vía requiere `GEMINI_API_KEY` en el entorno y valida nombres, rangos, fechas y URL de fuente. Nunca presenta una referencia regional como precio observado. Si no encuentra al menos un precio observado de los últimos siete días, falla la ejecución y deja intacto `data/current.json`.

Los precios oficiales son **promedios departamentales**, no precios de cada estación ni precios en tiempo real. La fecha de `price_date` corresponde a la medición; `updated_at` indica cuándo se publicó el archivo. La web debe mostrar ambas.

## Ejecución local

```powershell
python -m pip install -r requirements.txt
python -m bot.main
python -m unittest discover -s tests -v
```

Gemini se usa para leer informes oficiales escaneados y como respaldo de investigación si el informe no está disponible; configure `GEMINI_API_KEY` como variable de entorno. El flujo programado usa el secreto de GitHub con ese nombre.

`data/current.json` y `history/YYYY-MM-DD.json` se publican desde este repositorio. `current.json` también incluye el precio observado anterior de cada departamento y dos indicadores de mercado con fechas propias: tipo de cambio GTQ/USD de la página del Banco de Guatemala y petróleo WTI en USD/barril de la U.S. Energy Information Administration. El WTI es una referencia de petróleo crudo, no un precio de gasolina guatemalteca.
