"""Build the midterm report PDF from the HTML deck.

Usage:
    python scripts/build_report.py

Edit docs/report/report_meta.json first (group, members, URLs).
"""

import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "docs" / "report"
TEMPLATE = REPORT_DIR / "report_template.html"
META = REPORT_DIR / "report_meta.json"
HTML_OUT = REPORT_DIR / "Skyline_Weather_期中專題報告.html"
PDF_OUT = REPORT_DIR / "Skyline_Weather_期中專題報告.pdf"
PREVIEW_DIR = REPORT_DIR / "preview"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def build_html():
    meta = json.loads(META.read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, value in meta.items():
        html = html.replace("{{" + key + "}}", value)
    HTML_OUT.write_text(html, encoding="utf-8")
    return HTML_OUT


def build_pdf(html_path):
    if not CHROME.exists():
        raise SystemExit("Chrome not found; install Chrome or edit the CHROME path.")
    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={PDF_OUT}",
        html_path.resolve().as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(f"Chrome print failed ({result.returncode})")
    if not PDF_OUT.exists() or PDF_OUT.stat().st_size < 10000:
        raise SystemExit("PDF was not created.")
    return PDF_OUT


def make_previews(pdf_path):
    import pymupdf

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    pages = []
    for index, page in enumerate(doc):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4), alpha=False)
        out = PREVIEW_DIR / f"slide-{index + 1:02d}.png"
        pix.save(out)
        pages.append(out)
    # contact sheet
    from PIL import Image, ImageDraw

    cols, rows = 3, 6
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (cols * thumb_w + 40, rows * (thumb_h + 26) + 20), "#16283A")
    draw = ImageDraw.Draw(sheet)
    for index, page_path in enumerate(pages):
        image = Image.open(page_path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        x = 10 + (index % cols) * (thumb_w + 10)
        y = 10 + (index // cols) * (thumb_h + 26)
        sheet.paste(image, (x, y))
        draw.text((x + 4, y + thumb_h + 4), f"{index + 1:02d}", fill="#D9E4F0")
    sheet.save(PREVIEW_DIR / "contact-sheet.png")
    print(f"PDF pages: {len(doc)}")
    print(f"Preview: {PREVIEW_DIR / 'contact-sheet.png'}")


def main():
    html = build_html()
    pdf = build_pdf(html)
    make_previews(pdf)
    print(f"HTML: {html}")
    print(f"PDF:  {pdf}")


if __name__ == "__main__":
    main()
