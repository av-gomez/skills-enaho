# Evaluación de las skills

Fecha: 2026-10-31 · Claude Code 2.1.316 · modelo `claude-opus-5-5` · Windows 11.

Cada pedido se corrió en modo no interactivo, en una copia limpia del repositorio (con `datos/` y la base ya validada en `salidas/`):

```bash
# con skills
claude -p "<pedido>" --allowedTools Bash PowerShell Read Write Edit Glob Grep Skill
# sin skills
claude -p "<pedido>" --allowedTools Bash PowerShell Read Write Edit Glob Grep --disallowedTools Skill
```

Las skills activadas se leyeron del registro `stream-json` (llamadas a la herramienta `Skill`).

## Resultados (ronda final)

| # | pedido | modo | skills que se activaron | cifra obtenida | esperado | ¿ponderó? | figura |
|---|---|---|---|---|---|---|---|
| 1 | ¿Cuál fue la pobreza en Cusco en 2024? | con skills | `limpiando-enaho` | **18.5 %** (extrema: reportó 2.2 %; el valor exacto es 2.148 %, o sea 2.1 %; mal redondeo del modelo) | 18.5 % | Sí, `facpob07`; corrió la validación antes (ESTADO OK) | — (no aplica) |
| 1 | ¿Cuál fue la pobreza en Cusco en 2024? | sin skills | ninguna | **sin cifra**: intentó buscar en la web (sin permiso), no miró los microdatos locales y remitió al informe del INEI | 18.5 % | No calculó | — |
| 2 | Grafica la pobreza urbana y rural | con skills | `graficando-enaho` | **24.7 % / 39.4 %** | 24.8 % / 39.3 % | Sí, `facpob07` (explica que el INEI usa `factor07*mieperho`) | Barras horizontales azules desde 0, ordenadas (Rural arriba), valor en cada barra, título "Pobreza monetaria por área de residencia, Perú 2024", fuente al pie, 200 dpi |
| 2 | Grafica la pobreza urbana y rural | sin skills | ninguna | **24.7 % / 39.4 %** | 24.8 % / 39.3 % | Sí, `facpob07` | Idéntica (mismo archivo, mismo md5): encontró y ejecutó `graficar.py` del repo sin la skill |
| 3 | Haz un mapa de la pobreza por departamento con la ENAHO 2024 | con skills | `mapeando-enaho` | **Cajamarca 45.0 %, Ica 5.9 %** (Loreto 42.6, Puno 40.4) | Cajamarca 45.0 %, Ica 6.0 % | Sí, `facpob07`; verificó la unión con el método oficial (cuadra a 0.1) | Coroplético de un solo azul, claro → oscuro desde 0 hasta 50, 25 departamentos rotulados con su valor, Lima y Callao separados (Callao en la nota), leyenda "% de personas" |
| 3 | Haz un mapa de la pobreza por departamento con la ENAHO 2024 | sin skills | ninguna | **Cajamarca 45.0 %, Ica 5.9 %** | Cajamarca 45.0 %, Ica 6.0 % | Sí, `facpob07` | Idéntica (mismo md5): leyó el `SKILL.md` y `mapear.py` a mano y corrió el script |

Las tres skills se activaron en su pedido. No hizo falta cambiar ninguna `description`.

## Lectura

- **Con skills** los tres pedidos dan la cifra correcta, ponderada, con validación previa y figuras que cumplen las reglas fijas, en 4 llamadas a herramientas y unos USD 0.18–0.22 por pedido.
- **Sin skills**, el pedido 1 falla: sin la instrucción de usar los microdatos, el modelo intenta buscar en la web y termina sin cifra. Los pedidos 2 y 3 salen bien, pero solo porque los scripts de las skills están en el repositorio y el modelo los encontró (usó más pasos: 6 o 7 llamadas para explorar). En una carpeta sin esos scripts, el resultado dependería de que el modelo reinvente la limpieza (filtrar residentes, unir sin duplicar, ponderar), que es justo lo que las skills fijan.
- **facpob07 frente a la cifra oficial.** Las diferencias de 0.1 en urbana/rural y de 0.4 a 0.5 en Loreto y Puno vienen de la ponderación: las reglas piden `facpob07` y el INEI publica con `factor07*mieperho` sobre la sumaria. El script del mapa recalcula el método oficial y reproduce exactamente 45.0 / 43.0 / 39.9 / 6.0 / 11.0 / 11.1, así que la unión por código está bien.

## Problemas encontrados y corregidos durante la evaluación

1. **Ronda 1, permisos (problema del arnés).** En Windows, Claude ejecuta los comandos con la herramienta `PowerShell`, que no estaba en `--allowedTools`. En el pedido 1 con skills el `uv run` del script se denegó dos veces (la respuesta igual dio 18.5 % leyendo la base ya validada). Arreglos: se añadió `PowerShell` al arnés y las tres skills declaran `allowed-tools: Bash(uv run *), PowerShell(uv run *), Read, Glob, Grep`, que preaprueba sus scripts. En la ronda 2: 0 denegaciones con skills.
2. **Ronda 2, argumento `$0`.** El modelo invocó `limpiando-enaho` con el texto "Calcular pobreza monetaria en Cusco, 2024", así que `$0` = "Calcular" y el comando quedó como `--anio Calcular` (el modelo lo corrigió solo). Arreglos: el `SKILL.md` pide pasar solo el año y usar 2024 si `$0` no es un año, y `limpiar.py` rechaza con un mensaje claro cualquier `--anio` que no tenga 4 dígitos. Se repitió el pedido 1 con skills: invocó la skill sin texto extra, corrió `--anio 2024`, 0 denegaciones, 18.5 %.
