import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from synvox_invoice import core, ocr  # noqa: E402
from test_core import make_key  # noqa: E402

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def _font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


@pytest.fixture
def scanned_pdf(tmp_path):
    """An image-only PDF (no text layer) that looks like a slightly skewed scanned DANFE."""
    key = make_key(number="000261073", yymm="2611")
    img = Image.new("RGB", (1654, 2339), "white")
    d = ImageDraw.Draw(img)
    y = 120
    lines = [("ACME TRANSPORTES LTDA", True), ("DANFE - Documento Auxiliar da Nota Fiscal", False),
             ("Recebemos de ACME TRANSPORTES LTDA os produtos constantes da nota", False),
             ("Chave de acesso", False), (" ".join(key[i:i + 4] for i in range(0, 44, 4)), False),
             ("Data de emissão 05/11/2026", False), ("Data de vencimento 20/11/2026", False),
             ("Valor total da nota R$ 1.234,56", False), ("Pedido de compra 4500123456", False)]
    for text, bold in lines:
        d.text((120, y), text, fill="black", font=_font(44 if bold else 34, bold))
        y += 110
    path = tmp_path / "scan_261073.pdf"
    img.rotate(0.6, fillcolor="white").save(str(path), "PDF", resolution=200)
    return str(path)


def _engines():
    names = []
    if ocr.TesseractEngine.create():
        names.append("tesseract")
    if ocr.RapidOcrEngine.create():
        names.append("rapidocr")
    return names


@pytest.fixture(autouse=True)
def _fresh_engine(monkeypatch):
    monkeypatch.delenv("SYNVOX_OCR_ENGINE", raising=False)
    monkeypatch.delenv("SYNVOX_OCR", raising=False)
    ocr.reset_engine()
    yield
    ocr.reset_engine()


# ---- pure logic (no engine needed) --------------------------------
def test_normalize_only_touches_number_like_tokens():
    assert ocr.normalize_ocr_text("Valor 1.2O4,56 ref SOBRE 4500l23456") == "Valor 1.204,56 ref SOBRE 4500123456"
    assert ocr.normalize_ocr_text("TRANSPORTES LTDA") == "TRANSPORTES LTDA"


def test_boxes_to_text_groups_lines_in_reading_order():
    box = lambda x, y: [[x, y], [x + 80, y], [x + 80, y + 20], [x, y + 20]]
    result = [(box(300, 102), "1.234,56", 0.9), (box(10, 100), "Valor total", 0.9),
              (box(10, 200), "Pedido", 0.9)]
    assert ocr.boxes_to_text(result) == "Valor total  1.234,56\nPedido"


def test_repair_key_fixes_single_misread_digit_and_refuses_ambiguity():
    key = make_key(number="000261073", yymm="2611")
    bad = key[:30] + ("8" if key[30] != "8" else "3") + key[31:]
    assert not core._key_ok(bad)
    repaired = core._repair_key(bad)
    # either it recovers the true key, or it refuses; it must never invent a different valid one
    assert repaired in (None, key)
    assert core._find_keys(bad, repair=False) == []


def test_ocr_can_be_disabled(monkeypatch, scanned_pdf):
    monkeypatch.setenv("SYNVOX_OCR", "0")
    with pytest.raises(ValueError, match="OCR"):
        core.extract_invoice(scanned_pdf)


def test_use_ocr_false_rejects_scanned_pdf(scanned_pdf):
    with pytest.raises(ValueError, match="OCR"):
        core.extract_invoice(scanned_pdf, use_ocr=False)


# ---- end to end, once per installed engine -------------------------
@pytest.mark.parametrize("engine", ["tesseract", "rapidocr"])
def test_scanned_pdf_end_to_end(engine, scanned_pdf, monkeypatch):
    if engine not in _engines():
        pytest.skip(f"{engine} not installed")
    pytest.importorskip("pypdfium2")
    monkeypatch.setenv("SYNVOX_OCR_ENGINE", engine)
    ocr.reset_engine()

    started = []
    row, missing, used = core.extract_invoice(scanned_pdf, "Ana", "NF", on_ocr=lambda: started.append(1))

    assert used and started == [1]
    assert missing == []
    assert row[core.NF] == "261073"
    assert row[core.EMIS] == "05/11/2026"
    assert row[core.VENC] == "20/11/2026"
    assert row[core.VAL] == "1.234,56"
    assert row[core.PED] == "4500123456"
    assert "ACME" in row[core.FORN]


def _text_pdf(path, lines):
    """Minimal one-page PDF with a real text layer (no extra libraries needed)."""
    content = "BT /F1 12 Tf 50 780 Td 16 TL " + " ".join(f"({l}) '" for l in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    with open(path, "wb") as f:
        f.write(out)


def test_text_pdf_does_not_trigger_ocr(tmp_path):
    path = str(tmp_path / "text.pdf")
    _text_pdf(path, ["ACME TRANSPORTES LTDA", "Data de emissao 05/11/2026",
                     "Data de vencimento 20/11/2026", "Valor total da nota R$ 99,90",
                     "Texto longo para garantir que a camada de texto tenha caracteres suficientes " * 3])
    started = []
    row, missing, used = core.extract_invoice(path, on_ocr=lambda: started.append(1))
    assert not used and not started
    assert row[core.VAL] == "99,90"
    assert row[core.VENC] == "20/11/2026"
