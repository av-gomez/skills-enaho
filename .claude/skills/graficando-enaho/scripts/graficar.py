"""Grafica la pobreza monetaria de la ENAHO por área, sexo o edad.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --por todo --anio 2024

Reglas fijas: pondera con facpob07; barras desde cero y ordenadas de mayor a menor;
un solo color; valor escrito en cada barra; título con qué y cuándo;
nota "Fuente: INEI, ENAHO <año>"; PNG a 200 dpi en figuras/.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
COLOR = "#1F4E79"

GRUPOS_EDAD = [(0, 14, "0 a 14 años"), (15, 29, "15 a 29 años"), (30, 44, "30 a 44 años"),
               (45, 64, "45 a 64 años"), (65, 200, "65 años a más")]

TITULOS = {
    "area": "Pobreza monetaria por área de residencia",
    "sexo": "Pobreza monetaria por sexo",
    "edad": "Pobreza monetaria por grupo de edad",
}


def categoria(base: pd.DataFrame, por: str) -> pd.Series:
    if por == "area":
        return base["urbano"].map({True: "Urbana", False: "Rural"})
    if por == "sexo":
        return base["p207"].map({1: "Hombres", 2: "Mujeres"})
    if por == "edad":
        edad = base["p208a"]
        out = pd.Series(pd.NA, index=base.index, dtype="object")
        for lo, hi, nombre in GRUPOS_EDAD:
            out[(edad >= lo) & (edad <= hi)] = nombre
        return out
    raise ValueError(por)


def pobreza_por(base: pd.DataFrame, por: str) -> pd.Series:
    cat = categoria(base, por)
    d = base.assign(cat=cat).dropna(subset=["cat"])
    tasa = d.groupby("cat").apply(
        lambda g: (g["pobre"] * g["facpob07"]).sum() / g["facpob07"].sum() * 100,
        include_groups=False)
    return tasa.sort_values(ascending=False)


def graficar(tasa: pd.Series, por: str, anio: int) -> Path:
    fig, ax = plt.subplots(figsize=(8, 1.6 + 0.62 * len(tasa)))
    orden = tasa.iloc[::-1]                      # mayor arriba
    barras = ax.barh(orden.index, orden.values, color=COLOR, height=0.62)
    for b, v in zip(barras, orden.values):
        ax.text(b.get_width() + tasa.max() * 0.012, b.get_y() + b.get_height() / 2,
                f"{v:.1f} %", va="center", ha="left", fontsize=11, color="#222222")
    ax.set_xlim(0, tasa.max() * 1.18)            # siempre desde cero
    ax.set_xlabel("% de personas en situación de pobreza monetaria", fontsize=9, color="#444444")
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=11)
    ax.tick_params(axis="x", labelsize=9, colors="#444444")
    ax.set_title(f"{TITULOS[por]}, Perú {anio}", loc="left", fontsize=13, fontweight="bold", pad=12)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {anio}. Cifras ponderadas con el factor de expansión "
             "de personas (facpob07).", fontsize=8, color="#555555", ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    salida = RAIZ / "figuras" / f"pobreza_{por}.png"
    salida.parent.mkdir(exist_ok=True)
    fig.savefig(salida, dpi=200)
    plt.close(fig)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--por", choices=["area", "sexo", "edad", "todo"], default="todo")
    ap.add_argument("--anio", type=int, default=2024)
    a = ap.parse_args()
    parquet = RAIZ / "salidas" / f"personas_{a.anio}.parquet"
    if not parquet.exists():
        sys.exit(f"ERROR: falta {parquet.relative_to(RAIZ)}. Usa primero la skill limpiando-enaho.")
    base = pd.read_parquet(parquet)
    for por in (["area", "sexo", "edad"] if a.por == "todo" else [a.por]):
        tasa = pobreza_por(base, por)
        ruta = graficar(tasa, por, a.anio)
        print(f"{ruta.relative_to(RAIZ)}: " + " | ".join(f"{k} {v:.1f} %" for k, v in tasa.items()))


if __name__ == "__main__":
    main()
