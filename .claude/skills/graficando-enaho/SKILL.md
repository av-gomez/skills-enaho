---
name: graficando-enaho
description: "Grafica la pobreza monetaria de la ENAHO del INEI por área (urbana/rural), sexo o grupo de edad, en barras ponderadas listas para informe. Úsala cuando pidan graficar, visualizar o comparar la pobreza urbana y rural, de hombres y mujeres o por edades en el Perú."
allowed-tools: Bash(uv run *), PowerShell(uv run *), Read, Glob, Grep
argument-hint: [area|sexo|edad|todo] [año]
---

# Graficando la pobreza de la ENAHO

Si no existe `salidas/personas_2024.parquet` (o el del año pedido), usa primero la skill **limpiando-enaho** para crearlo y validarlo.

## Cómo

Desde la raíz del repositorio:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por area      # o sexo, edad, todo
uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por todo --anio 2024
```

El script imprime las cifras de cada barra y guarda `figuras/pobreza_<por>.png`. Responde con esas cifras y la ruta de la figura. Revisa la imagen antes de entregarla.

## Reglas fijas (no las cambies aunque el pedido sea informal)

- Pondera **siempre** con `facpob07`: `sum(pobre * facpob07) / sum(facpob07) * 100`.
- Barras **desde cero** y **ordenadas** de mayor a menor.
- **Un solo color** para todas las barras.
- **Valor escrito** en cada barra, con un decimal.
- **Título que dice qué y cuándo** (p. ej. "Pobreza monetaria por área de residencia, Perú 2024").
- Nota al pie **"Fuente: INEI, ENAHO 2024"** (con el año que corresponda).
- **PNG a 200 dpi** en `figuras/`.

Si piden un corte que el script no tiene, sigue estas mismas reglas en un script nuevo y consulta `../limpiando-enaho/reference.md` para los códigos de las variables.

## Cifras esperadas 2024 (verificación)

- Área: urbana ≈ 24.8 %, rural ≈ 39.3 % (con `facpob07` sale 24.7 % y 39.4 %; la cifra oficial del INEI usa `factor07*mieperho` en la sumaria).
