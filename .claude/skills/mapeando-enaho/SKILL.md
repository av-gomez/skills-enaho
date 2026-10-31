---
name: mapeando-enaho
description: "Hace el mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO del INEI. Úsala cuando pidan un mapa, mapear o ver en el territorio la pobreza por departamento o región con la ENAHO."
allowed-tools: Bash(uv run *), PowerShell(uv run *), Read, Glob, Grep
argument-hint: [año]
---

# Mapeando la pobreza de la ENAHO

Si no existe `salidas/personas_2024.parquet` (o el del año pedido), usa primero la skill **limpiando-enaho** para crearlo y validarlo. El mapa necesita también `datos/peru_departamental_simple.geojson`.

## Cómo

Desde la raíz del repositorio:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --anio 2024
```

El script imprime la tabla por departamento, verifica la unión y guarda `mapas/pobreza_departamento.png`. Revisa la imagen y responde con la ruta y las cifras destacadas (más y menos pobres).

## Reglas fijas

- Une por **código**: `ubigeo[:2]` de la ENAHO con `FIRST_IDDP` del geojson, ambos como texto de 2 dígitos. **Nunca por nombre** (tildes, "Lima Provincias", "Prov. Const. del Callao" rompen la unión).
- Exige **25 departamentos y ninguno sin dato** (assert).
- **Lima (15) y Callao (07) separados**.
- Escala de **un solo color, de claro a oscuro, desde 0**. Nunca arcoíris ni paletas divergentes.
- Leyenda **"% de personas"**.
- Pondera con `facpob07`. Guarda en `mapas/pobreza_departamento.png`.

## Verificación 2024

Valores de referencia del INEI (método oficial: sumaria con `factor07*mieperho`): Cajamarca 45.0 %, Loreto 43.0 %, Puno 39.9 %, Ica 6.0 %, Moquegua 11.0 %, Madre de Dios 11.1 %, Cusco 18.5 %. El script los recalcula desde la sumaria y falla si no cuadran a 0.1 puntos. Si no cuadran, **revisa la unión** (ceros a la izquierda, códigos como número). Con `facpob07` algunos se mueven unas décimas (Loreto 42.6 %, Puno 40.4 %): es la ponderación, no un error de unión.
