"""Reconstruye Folio_XML -> NAR a partir de los artefactos del bot Mixup (02/10/2026).

Uso: python reconstruir_nar.py <carpeta_con_archivos_extraidos> <salida.csv>

Fuentes, por prioridad (todas "evidencia directa"; no se infiere ningún NAR):
  1. tabla_portal_*.csv        -> respuesta del portal (folio, respuesta, NAR)
  2. log_*.txt                 -> líneas "Folio: X - NAR: N" y "factura es: X Y el NAR es:N"
  3. TRANSCRIPCION_PNG         -> NAR leídos a mano de screenshot_261002_1100.png
"""
import csv, glob, os, re, sys

# Transcrito visualmente de screenshot_261002_1100.png (11:20 a. m.). VERIFICAR contra la imagen.
TRANSCRIPCION_PNG = {
    "F000189331": "3837747377", "F000189332": "3837747384", "F000189333": "3837747391",
    "F000189334": "3837747407", "F000189335": "3837747411", "F000189336": "3837747424",
    "F000189337": "3837747439", "F000189338": "3837747442", "F000189339": "3837747451",
    "F000189340": "3837747465", "F000189341": "3837747479", "F000189342": "3837747484",
    "F000189343": "3837747499", "F000189344": "3837747502", "F000189345": "3837747511",
    "F000189346": "3837747523", "F000189347": "3837747539", "F000189348": "3837747546",
    "F000189349": "3837747551", "F000189350": "3837747566",
}
NAR_RE = re.compile(r"\b3837\d{6}\b")


def leer(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main(src, out):
    nars, fuente = {}, {}

    def add(folio, nar, origen):
        if nar and NAR_RE.fullmatch(nar):
            if folio in nars and nars[folio] != nar:
                raise SystemExit(f"Conflicto {folio}: {nars[folio]} vs {nar} ({origen})")
            nars.setdefault(folio, nar)
            fuente.setdefault(folio, origen)

    for p in sorted(glob.glob(os.path.join(src, "tabla_portal_*.csv"))):
        for row in csv.reader(open(p, encoding="utf-8", errors="replace")):
            if len(row) >= 5 and row[1].endswith(".xml"):
                add(row[1][:-4], row[-1].strip(), os.path.basename(p))
    for p in sorted(glob.glob(os.path.join(src, "log_*.txt"))):
        t = leer(p)
        for m in re.finditer(r"Folio: (F\d+) - NAR: (\d+)", t):
            add(m[1], m[2], os.path.basename(p))
        for m in re.finditer(r"factura es: (F\d+) Y el NAR es:(\d+)", t):
            add(m[1], m[2], os.path.basename(p))
    for f, n in TRANSCRIPCION_PNG.items():
        add(f, n, "screenshot_261002_1100.png (transcrito)")

    folios = sorted(set(leer(os.path.join(src, "folios_261002_1100.txt")).strip().split(",")))
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Folio_XML", "Folio_NAR", "Fuente", "Estado"])
        for fo in folios:
            if fo in nars:
                w.writerow([fo, nars[fo], fuente[fo], "OK"])
            else:
                w.writerow([fo, "", "", "SIN_NAR: portal respondió 'Acuse no Generado' (ya enviado antes)"])
    ok = sum(1 for f in folios if f in nars)
    print(f"{len(folios)} folios, {ok} con NAR, {len(folios)-ok} sin NAR")


if __name__ == "__main__":
    main(*sys.argv[1:3])
