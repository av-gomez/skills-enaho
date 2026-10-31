# skills-enaho

Tres skills de [Claude Code](https://claude.com/claude-code) para trabajar la **ENAHO 2024** del INEI (Encuesta Nacional de Hogares): limpiar y validar los microdatos, graficar la pobreza y mapearla por departamento.

| skill | qué hace | salida |
|---|---|---|
| [`limpiando-enaho`](.claude/skills/limpiando-enaho/SKILL.md) | Une el módulo 34 (sumaria) con el 02 (miembros), filtra residentes habituales, crea `departamento`, `urbano`, `pobre` y valida contra las cifras oficiales del INEI. Incluye un [diccionario de variables y 6 trampas](.claude/skills/limpiando-enaho/reference.md). | `salidas/personas_2024.parquet`, `salidas/validacion.txt` |
| [`graficando-enaho`](.claude/skills/graficando-enaho/SKILL.md) | Barras de pobreza por área, sexo o edad con reglas fijas: `facpob07`, desde cero, ordenadas, un color, valor en cada barra, fuente, 200 dpi. | `figuras/pobreza_{area,sexo,edad}.png` |
| [`mapeando-enaho`](.claude/skills/mapeando-enaho/SKILL.md) | Mapa coroplético por departamento, unido por código `ubigeo[:2]` = `FIRST_IDDP` (nunca por nombre), 25 departamentos, Lima y Callao separados, escala de un color desde 0. | `mapas/pobreza_departamento.png` |

Las skills de gráfico y mapa se encadenan con la de limpieza: si falta el parquet, primero piden correr `limpiando-enaho`.

## Instalación

```bash
git clone https://github.com/av-gomez/skills-enaho.git
cd skills-enaho
uv sync            # instala pandas, pyarrow, geopandas, matplotlib
```

Requiere [uv](https://docs.astral.sh/uv/) (`pip install uv`) y Claude Code.

## Datos (no incluidos en el repo)

Descárgalos en `datos/` y descomprime los zip ahí mismo (el código **966 = ENAHO 2024**):

```bash
mkdir -p datos && cd datos
curl -LO https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip   # sumaria-2024.dta
curl -LO https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip   # enaho01-2024-200.dta
curl -LO https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
unzip 966-Modulo34.zip && unzip 966-Modulo02.zip
cd ..
```

Luego genera la base (o deja que Claude lo haga con la skill):

```bash
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por todo
uv run .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024
```

## Ejemplos de pedidos

Dentro de la carpeta del repo, abre `claude` y pide en lenguaje natural:

- "¿Cuál fue la pobreza en Cusco en 2024?"
- "Grafica la pobreza urbana y rural"
- "Compara la pobreza de hombres y mujeres"
- "Haz un mapa de la pobreza por departamento con la ENAHO 2024"
- `/limpiando-enaho 2024`

## Cifras de validación (2024)

De `salidas/validacion.txt`:

| indicador | obtenido | INEI |
|---|---|---|
| Residentes habituales (muestra) | 108,664 | 108,664 |
| Pobreza total, sumaria `factor07*mieperho` | 27.58 % | 27.6 % |
| Pobreza extrema, sumaria | 5.50 % | 5.5 % |
| Pobreza total, personas `facpob07` | 27.53 % | ≈ 27.53 % |
| Urbana / rural (`facpob07`) | 24.7 % / 39.4 % | 24.8 % / 39.3 % |
| Cusco | 18.5 % | 18.5 % |
| Cajamarca / Loreto / Puno | 45.0 / 42.6 / 40.4 % | 45.0 / 43.0 / 39.9 % |
| Ica / Moquegua / Madre de Dios | 5.9 / 10.9 / 11.1 % | 6.0 / 11.0 / 11.1 % |

**Sobre las décimas de diferencia.** Las reglas piden ponderar con `facpob07` (factor de personas). Las cifras oficiales del INEI se calculan con la sumaria ponderada por `factor07*mieperho`. En el total nacional ambas coinciden (27.53 frente a 27.58), pero en algunos departamentos se separan hasta 0.5 puntos (Loreto, Puno). El script del mapa recalcula el método oficial y comprueba con assert que reproduce exactamente las cifras del INEI (45.0, 43.0, 39.9, 6.0, 11.0, 11.1), lo que prueba que la unión por código es correcta: la diferencia es de ponderación, no un error de datos.

## Evaluación

Ver [evaluacion.md](evaluacion.md).

Cada pedido se corrió con `claude -p`, con skills y sin skills (`--disallowedTools Skill`):

| pedido | con skills | sin skills |
|---|---|---|
| ¿Cuál fue la pobreza en Cusco en 2024? | `limpiando-enaho` → **18.5 %** ✓ | sin cifra (buscó en la web, no usó los microdatos) ✗ |
| Grafica la pobreza urbana y rural | `graficando-enaho` → **24.7 % / 39.4 %**, figura con todas las reglas ✓ | igual, pero solo porque encontró el script de la skill en el repo |
| Haz un mapa de la pobreza por departamento con la ENAHO 2024 | `mapeando-enaho` → **Cajamarca 45.0 %, Ica 5.9 %**, unión verificada ✓ | igual, leyendo a mano el `SKILL.md` y el script |

Las tres skills se activaron solas. La evaluación destapó dos problemas, ya corregidos: permisos en Windows (se añadió `allowed-tools`) y un argumento `$0` que no era un año.

## Estructura

```
.claude/skills/
  limpiando-enaho/   SKILL.md · reference.md · scripts/limpiar.py
  graficando-enaho/  SKILL.md · scripts/graficar.py
  mapeando-enaho/    SKILL.md · scripts/mapear.py
salidas/validacion.txt
figuras/  pobreza_area.png · pobreza_sexo.png · pobreza_edad.png
mapas/    pobreza_departamento.png
evaluacion.md · README.md · pyproject.toml · uv.lock
```
