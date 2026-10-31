"""Limpia la ENAHO (módulos 34 sumaria y 02 miembros) y arma una base de personas.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Salidas:
    salidas/personas_<anio>.parquet
    salidas/validacion.txt
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
TEXTO = LLAVES_PERSONA + ["ubigeo"]
ANCHO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Cifras oficiales del INEI para validar (porcentaje de personas).
OFICIAL = {
    2024: {"residentes": 108_664, "pobreza": 27.6, "pobreza_extrema": 5.5},
}
TOLERANCIA = 0.1

# Variables de la sumaria que se agregan a cada persona.
VARS_SUMARIA = ["pobreza", "mieperho", "factor07", "linea", "linpe", "gashog2d", "inghog1d"]


def buscar(patron: str) -> Path:
    hallados = sorted(DATOS.rglob(patron))
    if not hallados:
        sys.exit(f"ERROR: no encontré {patron} dentro de {DATOS}. "
                 "Descarga y descomprime los módulos del INEI (código 966 = 2024).")
    return hallados[0]


def leer(ruta: Path) -> pd.DataFrame:
    # Paso 1: sin convertir categorías; llaves y ubigeo como texto con ceros a la izquierda.
    df = pd.read_stata(ruta, convert_categoricals=False)
    # Paso 2: columnas en minúscula; la columna año (con Ñ, a veces mal codificada) pasa a anio.
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={c: "anio" for c in df.columns if re.fullmatch(r"a.{1,2}o", c)})
    for c in TEXTO:
        if c in df.columns:
            s = df[c]
            if pd.api.types.is_numeric_dtype(s):
                s = s.astype("Int64").astype(str)
            df[c] = s.astype(str).str.strip().str.zfill(ANCHO[c])
    return df


def ponderada(valor: pd.Series, peso: pd.Series) -> float:
    return float((valor * peso).sum() / peso.sum() * 100)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", default="2024")
    valor = str(ap.parse_args().anio).strip()
    if not re.fullmatch(r"\d{4}", valor):
        sys.exit(f"ERROR: --anio debe ser un año de 4 dígitos (p. ej. 2024); recibí {valor!r}.")
    anio = int(valor)
    SALIDAS.mkdir(exist_ok=True)

    sumaria = leer(buscar(f"sumaria-{anio}.dta"))
    miembros = leer(buscar(f"enaho01-{anio}-200.dta"))
    n_miembros = len(miembros)

    # Paso 3: solo residentes habituales.
    residente = ((miembros["p204"] == 1) & (miembros["p205"] == 2)) | \
                ((miembros["p204"] == 2) & (miembros["p206"] == 1))
    personas = miembros.loc[residente].copy()
    n_residentes = len(personas)

    # Paso 4: unión persona -> hogar (muchos a uno; si duplica, falla).
    sum_vars = sumaria[LLAVES_HOGAR + [v for v in VARS_SUMARIA if v in sumaria.columns]]
    base = personas.merge(sum_vars, on=LLAVES_HOGAR, how="left", validate="m:1", indicator=True)

    # Paso 5: variables derivadas.
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2
    base["pobre_extremo"] = base["pobreza"] == 1

    # Paso 6: validaciones.
    assert not base.duplicated(LLAVES_PERSONA).any(), "Hay llaves de persona duplicadas"
    assert len(base) == n_residentes, "La unión cambió el número de filas"
    assert (base["_merge"] == "both").all(), \
        f"{(base['_merge'] != 'both').sum()} personas sin hogar en la sumaria"
    base = base.drop(columns="_merge")

    peso_sum = sumaria["factor07"] * sumaria["mieperho"]
    pob_sum = ponderada(sumaria["pobreza"] <= 2, peso_sum)
    ext_sum = ponderada(sumaria["pobreza"] == 1, peso_sum)
    pob_per = ponderada(base["pobre"], base["facpob07"])
    ext_per = ponderada(base["pobre_extremo"], base["facpob07"])
    urb = base[base["urbano"]]; rur = base[~base["urbano"]]
    pob_urb = ponderada(urb["pobre"], urb["facpob07"])
    pob_rur = ponderada(rur["pobre"], rur["facpob07"])
    por_dep = (base.groupby("departamento")
                   .apply(lambda g: ponderada(g["pobre"], g["facpob07"]), include_groups=False)
                   .round(1))

    lineas = [
        f"VALIDACIÓN ENAHO {anio}",
        f"Miembros en el módulo 02: {n_miembros:,}",
        f"Residentes habituales: {n_residentes:,}",
        f"Hogares en la sumaria: {len(sumaria):,}",
        f"Filas tras la unión: {len(base):,} (sin pérdidas ni duplicados)",
        "",
        "Pobreza monetaria (% de personas)",
        f"  Sumaria, factor07*mieperho:  pobreza total {pob_sum:.2f}  | extrema {ext_sum:.2f}",
        f"  Personas, facpob07:          pobreza total {pob_per:.2f}  | extrema {ext_per:.2f}",
        f"  Área (personas, facpob07):   urbana {pob_urb:.1f}  | rural {pob_rur:.1f}",
        "",
        "Pobreza por departamento (personas, facpob07, código ubigeo[:2])",
    ] + [f"  {d}: {v:.1f}" for d, v in por_dep.items()]

    ofi = OFICIAL.get(anio)
    estado = "SIN CIFRA OFICIAL CARGADA PARA ESTE AÑO: revisa a mano"
    if ofi:
        lineas += ["", f"Cifras oficiales INEI {anio}: pobreza {ofi['pobreza']} | extrema "
                       f"{ofi['pobreza_extrema']} | residentes {ofi['residentes']:,}"]
        diff_p = abs(pob_sum - ofi["pobreza"]); diff_e = abs(ext_sum - ofi["pobreza_extrema"])
        lineas.append(f"Diferencia con el INEI: pobreza {diff_p:.2f} pts | extrema {diff_e:.2f} pts "
                      f"(tolerancia {TOLERANCIA})")
        ok = n_residentes == ofi["residentes"] and diff_p <= TOLERANCIA and diff_e <= TOLERANCIA
        estado = "OK" if ok else "FALLÓ"
    lineas += ["", f"ESTADO: {estado}"]
    (SALIDAS / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))

    if ofi:
        assert n_residentes == ofi["residentes"], f"Residentes {n_residentes} != {ofi['residentes']}"
        assert abs(pob_sum - ofi["pobreza"]) <= TOLERANCIA, f"Pobreza {pob_sum:.2f} != {ofi['pobreza']}"
        assert abs(ext_sum - ofi["pobreza_extrema"]) <= TOLERANCIA, \
            f"Pobreza extrema {ext_sum:.2f} != {ofi['pobreza_extrema']}"

    # Paso 7: guardar.
    salida = SALIDAS / f"personas_{anio}.parquet"
    base.to_parquet(salida, index=False)
    print(f"\nGuardado: {salida.relative_to(RAIZ)} ({len(base):,} filas, {base.shape[1]} columnas)")


if __name__ == "__main__":
    main()
