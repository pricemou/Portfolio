"""Génère un CV PDF minimal sans dépendance externe."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "docs", "cv-claude-pricemou.pdf")

LINES = [
    "Claude Pricemou",
    "Developpeur Full Stack et Science des donnees",
    "Trois-Rivieres (Quebec)  |  Freelance  |  FR maternel, EN intermediaire",
    "https://claude225.pythonanywhere.com  |  github.com/pricemou  |  linkedin.com/in/pricemou",
    "",
    "FORMATION",
    "- Baccalaureat en informatique (science des donnees), UQTR",
    "- Baccalaureat et BTS en informatique, HEC",
    "- AWS Cloud Practitioner (2024), Azure AI-900 (2024), Big Data UC San Diego, Power BI",
    "- Laureat Meilleur programmeur 2020, Institut Cerco",
    "",
    "PARCOURS",
    "- Freelance Full Stack, Marc Worldwide Transport (depuis mai 2026)",
    "- Stage, Network Pro Service (2026)",
    "- Stage, RabbyTech, Abidjan (2025)",
    "- Groupe Cerco (2019-2022) : front, Python, full stack, chef d'equipe",
    "- Chef d'equipe, Clean International",
    "- Benevole, AEI UQTR",
]


def escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    y = 780
    commands = ["BT", "/F1 11 Tf"]
    for line in LINES:
        size = 18 if line == "Claude Pricemou" else 11
        commands.append(f"/F1 {size} Tf")
        commands.append(f"1 0 0 1 50 {y} Tm ({escape(line)}) Tj")
        y -= 22 if line == "Claude Pricemou" else 16
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        b"4 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    with open(OUT, "wb") as f:
        f.write(pdf)
    print(OUT)


if __name__ == "__main__":
    main()
