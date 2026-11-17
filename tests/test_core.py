import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# core has no Qt import, so these tests run without PySide6 installed
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "synvox_core", os.path.join(os.path.dirname(__file__), "..", "src", "synvox_invoice", "core.py"))
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)


def make_key(uf="35", yymm="2610", cnpj="12345678000195", model="55", serie="001",
             number="000123456", tp="1", code="12345678"):
    """Build a syntactically valid 44-digit access key (with the mod-11 check digit)."""
    base = f"{uf}{yymm}{cnpj}{model}{serie}{number}{tp}{code}"
    assert len(base) == 43
    w, t = 2, 0
    for d in reversed(base):
        t += int(d) * w
        w = w + 1 if w < 9 else 2
    r = t % 11
    return base + str(0 if r < 2 else 11 - r)


def test_money_roundtrip():
    assert core.fmt_money(38025.75) == "38.025,75"
    assert core.parse_money("R$ 38.025,75") == 38025.75
    assert core.parse_money("") is None


def test_dates():
    assert core.parse_date("05/11/2026") == date(2026, 11, 5)
    assert core.parse_date("05/11/26") == date(2026, 11, 5)
    assert core.parse_comp("11/2026") == date(2026, 11, 1)
    assert core.parse_date("nope") is None


def test_key_validation():
    k = make_key()
    assert core._key_ok(k)
    assert not core._key_ok(k[:-1] + str((int(k[-1]) + 1) % 10))   # wrong check digit
    assert core._key_number(k) == "123456"


def test_find_keys_with_separators():
    k = make_key()
    spaced = " ".join(k[i:i + 4] for i in range(0, 44, 4))
    assert core._find_keys(f"Chave de acesso\n{spaced}\n") == [k]


def test_parse_nfe_text():
    k = make_key(number="000261073", yymm="2611")
    text = (
        "ACME TRANSPORTES LTDA\n"
        f"Chave de acesso {k}\n"
        "Data de emissão 05/11/2026\n"
        "Data de vencimento 20/11/2026\n"
        "Valor total da nota R$ 1.234,56\n"
        "Pedido de compra 4500123456\n"
        "Texto de relleno para passar o minimo de caracteres do leitor.\n"
    )
    row, missing = core.parse_text(text, "Ana", "NF", today=date(2026, 11, 17))
    assert row[core.NF] == "261073"
    assert row[core.EMIS] == "05/11/2026"
    assert row[core.COMP] == "11/2026"
    assert row[core.VENC] == "20/11/2026"
    assert row[core.VAL] == "1.234,56"
    assert row[core.PED] == "4500123456"
    assert row[core.FORN] == "ACME TRANSPORTES LTDA"
    assert row[core.LANC] == "Ana"
    assert row[core.INCL] == "17/11/2026"
    assert row[core.TIPO] == "NF"
    assert missing == []


def test_parse_fatura_text():
    text = (
        "TRANSPORTES EXEMPLO LTDA\n"
        "CÓD. FATURA 00123456\n"
        "EMISSÃO 01/11/2026 VENCIMENTO 30/11/2026\n"
        "VALOR R$ 38.025,75\n"
        "Conjunto de conhecimentos de transporte agrupados nesta fatura.\n"
    )
    row, _ = core.parse_text(text, today=date(2026, 11, 17))
    assert row[core.TIPO] == "Fatura"
    assert row[core.NF] == "123456"
    assert row[core.EMIS] == "01/11/2026"
    assert row[core.VENC] == "30/11/2026"
    assert row[core.VAL] == "38.025,75"


def test_missing_fields_reported():
    row, missing = core.parse_text("x" * 40, today=date(2026, 11, 17))
    assert "VALOR" in missing and "FORNECEDOR" in missing


def test_convert_row_rejects_bad_values():
    row = [""] * len(core.HEADERS)
    row[core.EMIS] = "31/02/2026"
    with pytest.raises(ValueError):
        core.convert_row(row)


def test_export_creates_then_appends(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    row = [""] * len(core.HEADERS)
    row[core.COMP], row[core.EMIS], row[core.NF] = "11/2026", "05/11/2026", "261073"
    row[core.VAL], row[core.FORN], row[core.VENC] = "1.234,56", "ACME LTDA", "20/11/2026"
    path = str(tmp_path / "out.xlsx")

    assert core.export_xlsx([row], path) == (1, False)
    assert core.export_xlsx([row, row], path) == (2, True)

    ws = openpyxl.load_workbook(path).active
    assert ws.max_row == 4                      # header + 3 rows
    assert ws.cell(2, core.VAL + 1).value == 1234.56
    assert ws.cell(2, core.NF + 1).value == 261073
    assert ws.cell(1, 1).fill.fgColor.rgb.endswith("0D1311")   # Synvox header colour
