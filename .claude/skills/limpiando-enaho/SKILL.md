---
name: limpiando-enaho
description: "Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, sexo o edad."
allowed-tools: Bash(uv run *), PowerShell(uv run *), Read, Glob, Grep
argument-hint: [año]
---

# Limpiando la ENAHO

Convierte los microdatos de la ENAHO (INEI) en una base de **personas residentes** con su condición de pobreza y su factor de expansión, validada contra las cifras oficiales.

## Pasos

1. **Comprueba los datos.** Deben existir en `datos/` los módulos 34 (sumaria) y 02 (miembros del hogar) del año pedido, descomprimidos (`sumaria-<año>.dta` y `enaho01-<año>-200.dta`). Si faltan los zip, pide al usuario que los baje del INEI (https://proyectos.inei.gob.pe/microdatos/; el código de encuesta **966 = 2024**):
   - `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip`
   - `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip`

   y que los descomprima dentro de `datos/`. Si no se indica año, usa 2024.

2. **Corre exactamente**, desde la raíz del repositorio:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0
   ```

   `$0` debe ser un año de 4 dígitos (p. ej. `2024`). Al invocar esta skill pasa **solo el año** como argumento. Si el argumento recibido está vacío o no es un año, sustitúyelo por `2024` antes de correr el comando (nunca pases texto como `--anio Calcular`).

3. **Lee `salidas/validacion.txt`.** Si la pobreza difiere de la cifra oficial del INEI en más de 0.1 puntos (o el script termina con error de assert, o `ESTADO` no es `OK`), **detente** y explica qué falló. No respondas con cifras de una base que no validó.

4. **Responde usando `salidas/personas_$0.parquet`.** Toda cifra se pondera con `facpob07` (factor de expansión de personas): `sum(pobre * facpob07) / sum(facpob07) * 100`. Nunca cuentes filas sin ponderar. Indica que la cifra es ponderada y la fuente (INEI, ENAHO <año>).

5. **Antes de usar una variable que no está en la base** (o si dudas del significado de un código), lee [reference.md](reference.md): diccionario de variables y las 6 trampas de la ENAHO.

## Qué contiene la base

Una fila por persona residente habitual, con llaves (`conglome`, `vivienda`, `hogar`, `codperso`), `ubigeo`, `dominio`, `estrato`, características del módulo 02 (`p203`, `p207`, `p208a`, …), variables del hogar de la sumaria (`pobreza`, `mieperho`, `factor07`, `linea`, `linpe`, `gashog2d`, `inghog1d`) y derivadas:

| variable | definición |
|---|---|
| `departamento` | `ubigeo[:2]` como texto (`"08"` = Cusco, `"15"` = Lima, `"07"` = Callao) |
| `urbano` | `estrato <= 5` |
| `pobre` | `pobreza <= 2` (extremo o no extremo) |
| `pobre_extremo` | `pobreza == 1` |

## Ejemplo

Pobreza en Cusco 2024:

```python
import pandas as pd
b = pd.read_parquet("salidas/personas_2024.parquet")
c = b[b.departamento == "08"]
print((c.pobre * c.facpob07).sum() / c.facpob07.sum() * 100)   # 18.5
```
