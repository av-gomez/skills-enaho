# Referencia ENAHO: variables y trampas

## Diccionario de variables

| variable | módulo | significado | valores / notas |
|---|---|---|---|
| `conglome` | ambos | conglomerado | texto de 6 dígitos con ceros |
| `vivienda` | ambos | vivienda dentro del conglomerado | texto de 3 dígitos |
| `hogar` | ambos | hogar dentro de la vivienda | texto de 2 dígitos |
| `codperso` | 02 | número de orden de la persona | texto de 2 dígitos |
| `ubigeo` | ambos | ubicación geográfica | texto de 6 dígitos: `DDPPdd` (departamento, provincia, distrito). `ubigeo[:2]` = departamento |
| `estrato` | ambos | estrato geográfico | 1–5 = área urbana; 6–8 = área rural |
| `dominio` | ambos | dominio geográfico | 1 Costa norte, 2 Costa centro, 3 Costa sur, 4 Sierra norte, 5 Sierra centro, 6 Sierra sur, 7 Selva, 8 Lima Metropolitana |
| `pobreza` | 34 | pobreza monetaria del hogar | **1 pobre extremo, 2 pobre no extremo, 3 no pobre** |
| `mieperho` | 34 | total de miembros del hogar | excluye trabajadores del hogar y pensionistas |
| `factor07` | 34 | factor de expansión del hogar | para cifras de personas desde la sumaria: `factor07 * mieperho` |
| `facpob07` | 02 | factor de expansión de la persona | **úsalo para toda cifra de personas en la base limpia** |
| `p203` | 02 | relación de parentesco con el jefe | 0 panel, 1 jefe/a, 2 esposo/a, 3 hijo/a, 4 yerno/nuera, 5 nieto/a, 6 padres/suegros, 7 otros parientes, 8 trabajador del hogar, 9 pensionista, 10 otros no parientes, 11 hermano/a |
| `p204` | 02 | ¿es miembro del hogar? | 1 sí, 2 no |
| `p205` | 02 | ¿estuvo ausente 30 días o más? | 1 sí, 2 no |
| `p206` | 02 | ¿estuvo presente 30 días o más? (no miembros) | 1 sí, 2 no |
| `p207` | 02 | sexo | 1 hombre, 2 mujer |
| `p208a` | 02 | edad en años cumplidos | 0–98 |
| `anio` | ambos | año de la encuesta | en el archivo original se llama `aÑo` |
| `mes` | ambos | mes de la entrevista | texto `01`–`12` |

Residente habitual = `(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`.

Códigos de departamento (`ubigeo[:2]`): 01 Amazonas, 02 Áncash, 03 Apurímac, 04 Arequipa, 05 Ayacucho, 06 Cajamarca, 07 Callao, 08 Cusco, 09 Huancavelica, 10 Huánuco, 11 Ica, 12 Junín, 13 La Libertad, 14 Lambayeque, 15 Lima, 16 Loreto, 17 Madre de Dios, 18 Moquegua, 19 Pasco, 20 Piura, 21 Puno, 22 San Martín, 23 Tacna, 24 Tumbes, 25 Ucayali.

## Las 6 trampas

1. **Ceros a la izquierda.** `ubigeo`, `conglome`, `vivienda`, `hogar` y `codperso` son códigos, no números. Si se leen como enteros, `"080101"` se vuelve `80101` y `ubigeo[:2]` da `"80"` en vez de `"08"`: las uniones y los mapas fallan en silencio. Léelos siempre como texto y rellena con `zfill`.
2. **La columna `aÑo`.** El nombre lleva Ñ y según el lector aparece como `aÑo`, `año` o un carácter roto. El script la renombra a `anio`; no la busques por su nombre original.
3. **No todos son residentes.** El módulo 02 incluye visitantes y ausentes. Antes de cualquier cifra de población hay que quedarse solo con residentes habituales (filtro de arriba). En 2024: 117,721 filas → 108,664 residentes.
4. **Uniones que duplican.** La sumaria es de hogares y el módulo 02 de personas. Une personas → hogar por `conglome`, `vivienda`, `hogar` con `validate="m:1"`; si el lado del hogar tuviera llaves repetidas, la unión multiplicaría personas. Comprueba que el número de filas no cambie.
5. **Las encuestas no son personas.** Cada fila representa a muchas personas. Contar filas (`mean()` sin pesos) da cifras sesgadas. Pondera siempre: `facpob07` en la base de personas, o `factor07 * mieperho` si trabajas directo con la sumaria (es el método de la cifra oficial). Las dos ponderaciones difieren en unas décimas en algunos departamentos.
6. **La pobreza es una categoría.** `pobreza` vale 1, 2 o 3: su promedio no significa nada. Crea indicadores (`pobre = pobreza <= 2`, `pobre_extremo = pobreza == 1`) y promedia esos con los pesos.

## Cifras de validación 2024 (INEI)

- Pobreza monetaria total: **27.6 %** (sumaria, `factor07*mieperho`: 27.58 %; personas, `facpob07`: 27.53 %).
- Pobreza extrema: **5.5 %**.
- Residentes habituales en la muestra: **108,664**.
