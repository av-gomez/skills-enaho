"""Mapa de pobreza monetaria por departamento con la ENAHO.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024

Reglas fijas: une por código ubigeo[:2] con FIRST_IDDP (nunca por nombre); 25 departamentos
sin datos faltantes; Lima (15) y Callao (07) separados; escala de un solo color de claro a
oscuro desde 0; leyenda "% de personas"; guarda mapas/pobreza_departamento.png.
"""
import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

RAIZ = Path(__file__).resolve().parents[4]
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
SUMARIA = "sumaria-{anio}.dta"

# Cifras de referencia 2024 (método oficial del INEI) para verificar la unión.
REFERENCIA = {2024: {"06": 45.0, "16": 43.0, "21": 39.9, "11": 6.0, "18": 11.0, "17": 11.1, "08": 18.5}}

CMAP = LinearSegmentedColormap.from_list("un_color", ["#F2F6FA", "#9CB9D6", "#3D6E9E", "#0B2545"])


def tasa_personas(base: pd.DataFrame) -> pd.Series:
    return base.groupby("departamento").apply(
        lambda g: (g["pobre"] * g["facpob07"]).sum() / g["facpob07"].sum() * 100,
        include_groups=False)


def tasa_oficial(anio: int) -> pd.Series | None:
    """Método del INEI: sumaria de hogares ponderada con factor07*mieperho."""
    rutas = sorted((RAIZ / "datos").rglob(SUMARIA.format(anio=anio)))
    if not rutas:
        return None
    s = pd.read_stata(rutas[0], convert_categoricals=False,
                      columns=["ubigeo", "pobreza", "factor07", "mieperho"])
    s["departamento"] = s["ubigeo"].astype(str).str.zfill(6).str[:2]
    s["w"] = s["factor07"] * s["mieperho"]
    return s.groupby("departamento").apply(
        lambda g: ((g["pobreza"] <= 2) * g["w"]).sum() / g["w"].sum() * 100, include_groups=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    anio = ap.parse_args().anio
    parquet = RAIZ / "salidas" / f"personas_{anio}.parquet"
    if not parquet.exists():
        sys.exit(f"ERROR: falta {parquet.relative_to(RAIZ)}. Usa primero la skill limpiando-enaho.")
    if not GEOJSON.exists():
        sys.exit(f"ERROR: falta {GEOJSON.relative_to(RAIZ)} (ver README para descargarlo).")

    base = pd.read_parquet(parquet)
    tasa = tasa_personas(base).rename("pobreza").reset_index()

    geo = gpd.read_file(GEOJSON)
    geo["FIRST_IDDP"] = geo["FIRST_IDDP"].astype(str).str.zfill(2)
    mapa = geo.merge(tasa, left_on="FIRST_IDDP", right_on="departamento", how="left", validate="1:1")

    # Verificaciones de la unión por código.
    assert len(mapa) == 25, f"Se esperaban 25 departamentos y hay {len(mapa)}"
    assert mapa["pobreza"].notna().all(), \
        f"Departamentos sin dato: {mapa.loc[mapa['pobreza'].isna(), 'NOMBDEP'].tolist()}"
    assert {"15", "07"} <= set(mapa["FIRST_IDDP"]), "Lima (15) y Callao (07) deben estar separados"
    assert mapa["FIRST_IDDP"].is_unique

    oficial = tasa_oficial(anio)
    print(f"{'cód':<4}{'departamento':<16}{'facpob07':>9}{'INEI*':>8}{'ref':>7}")
    for _, r in mapa.sort_values("pobreza", ascending=False).iterrows():
        cod = r["FIRST_IDDP"]
        ofi = oficial.get(cod) if oficial is not None else None
        ref = REFERENCIA.get(anio, {}).get(cod)
        print(f"{cod:<4}{r['NOMBDEP'].title():<16}{r['pobreza']:>9.1f}"
              f"{(f'{ofi:.1f}' if ofi is not None else '-'):>8}{(f'{ref:.1f}' if ref else ''):>7}")
    print("* INEI: método oficial (sumaria, factor07*mieperho). El mapa usa facpob07.")
    if oficial is not None and anio in REFERENCIA:
        for cod, ref in REFERENCIA[anio].items():
            assert abs(oficial[cod] - ref) <= 0.1, f"{cod}: {oficial[cod]:.1f} != {ref} (revisa la unión)"
            assert abs(mapa.set_index("FIRST_IDDP").loc[cod, "pobreza"] - ref) <= 0.6, \
                f"{cod}: facpob07 se aleja demasiado de la referencia"
        print("Verificación OK: las cifras de referencia cuadran (unión por código correcta).")

    # Mapa.
    mapa = mapa.to_crs(32718)
    vmax = max(50.0, float(mapa["pobreza"].max()))
    fig, ax = plt.subplots(figsize=(7.2, 9.4))
    mapa.plot(column="pobreza", cmap=CMAP, vmin=0, vmax=vmax, edgecolor="white", linewidth=0.6, ax=ax)
    for _, r in mapa.iterrows():
        if r["FIRST_IDDP"] == "07":
            continue  # Callao es muy pequeño para rotular dentro; va en la nota
        p = r.geometry.representative_point()
        claro = r["pobreza"] > vmax * 0.55
        ax.text(p.x, p.y, f"{r['pobreza']:.1f}", ha="center", va="center", fontsize=7.5,
                color="white" if claro else "#1A1A1A")
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, vmax))
    cax = fig.add_axes([0.10, 0.085, 0.42, 0.016])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("% de personas", fontsize=9)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8)
    callao = mapa.set_index("FIRST_IDDP").loc["07", "pobreza"]
    fig.suptitle(f"Pobreza monetaria por departamento, Perú {anio}", x=0.06, ha="left",
                 fontsize=14, fontweight="bold", y=0.975)
    fig.text(0.06, 0.935, "% de personas en situación de pobreza monetaria", fontsize=9.5, color="#444444")
    fig.text(0.06, 0.03, f"Fuente: INEI, ENAHO {anio}. Ponderado con facpob07. "
             f"Callao (no rotulado): {callao:.1f} %.", fontsize=8, color="#555555")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.12)
    salida = RAIZ / "mapas" / "pobreza_departamento.png"
    salida.parent.mkdir(exist_ok=True)
    fig.savefig(salida, dpi=200)
    plt.close(fig)
    print(f"Guardado: {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
