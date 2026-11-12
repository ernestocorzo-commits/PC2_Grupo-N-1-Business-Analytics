"""
Genera dashboard/data.js a partir de los CSV exportados por el notebook PC2
(canciones, chart_diario, rotacion_diaria, modelo_*, segmentos, kpis).

Uso (desde la carpeta DATA):  python dashboard/build_data.py
Vuelve a ejecutarlo cada vez que se re-exporten los CSV del notebook.
"""
import csv
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")


def leer(nombre):
    with open(os.path.join(BASE, nombre), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except ValueError:
        return v
    return int(x) if x.is_integer() and abs(x) < 1e12 else round(x, 4)


def limpiar(filas, texto=()):
    return [{k: (v if k in texto else num(v)) for k, v in fila.items()} for fila in filas]


canciones = limpiar(
    leer("canciones.csv"),
    texto=("cancion", "artistas", "tipo_artista", "pais_origen", "macro_genero",
           "segmento", "supera_7_dias", "permanencia_conocida", "primera_fecha", "ultima_fecha"),
)
# Códigos ISO que el diccionario PAISES_NOMBRE del notebook no traduce
PAISES_EXTRA = {"SE": "Suecia", "NI": "Nicaragua", "JM": "Jamaica", "IT": "Italia", "BE": "Bélgica"}

for c in canciones:
    c["cancion"] = c["cancion"] or "(sin título)"
    c["artistas"] = c["artistas"] or "(sin dato)"
    c["pais_origen"] = PAISES_EXTRA.get(c["pais_origen"], c["pais_origen"])

# chart_diario en formato compacto: [indice_fecha, puesto, id_cancion]
chart = leer("chart_diario.csv")
fechas = sorted({r["fecha"] for r in chart})
idx = {f: i for i, f in enumerate(fechas)}
chart_rows = [[idx[r["fecha"]], int(r["puesto"]), int(r["id_cancion"])] for r in chart]

data = {
    "kpis": limpiar(leer("kpis.csv"), texto=("fuente", "indicador", "unidad")),
    "segmentos": limpiar(leer("segmentos.csv"), texto=("segmento", "Género dominante", "Ejemplos")),
    "factores": limpiar(leer("modelo_factores.csv"), texto=("factor", "bloque", "significativo")),
    "bloques": limpiar(leer("modelo_bloques.csv"), texto=("bloque",)),
    "rotacion": limpiar(leer("rotacion_diaria.csv"), texto=("fecha", "tipo")),
    "canciones": canciones,
    "fechas": fechas,
    "chart": chart_rows,
}

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// Archivo generado por build_data.py. No editar a mano.\n")
    f.write("window.DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

# Control de coherencia con los KPIs del notebook
por_id = {c["id_cancion"]: c for c in canciones}
gen = Counter(por_id[r[2]]["macro_genero"] for r in chart_rows)
tipo = Counter(por_id[r[2]]["tipo_artista"] for r in chart_rows)
total = len(chart_rows)
print(f"data.js escrito: {len(canciones)} canciones, {total} filas de chart, {fechas[0]} a {fechas[-1]}")
print("Cuota por macro-género (% de días-puesto):")
for g, n in gen.most_common():
    print(f"  {g}: {100 * n / total:.2f}%")
print("Cuota por tipo de artista:")
for g, n in tipo.most_common():
    print(f"  {g}: {100 * n / total:.2f}%")
