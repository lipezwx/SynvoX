"""
synvox_invoice.core
Extraction of invoice data from PDF text + export to the fixed XLSX model.
No GUI code here, so it can be tested or reused from scripts.
"""
import getpass
import os
import re
from datetime import date, datetime

from . import ocr

# ---------------------------------------------------------------
# The pre-determined model (exact header text, including line breaks)
# ---------------------------------------------------------------
HEADERS = [
    "MES DE COMPETENCIA",
    "DATA EMISSÃO",
    "FATURA / NF",
    "VALOR",
    "FORNECEDOR",
    "DATA INCLUSÃO \nPLANILHA",
    "DATA DE\nVENCTO",
    "LANÇADO POR:",
    "PEDIDO",
    "CTE",
    "TIPO\nOPERAÇÃO",
    "DATA LCTO\nCONTAS A PAGAR",
    "ADICIONAL INFORMAÇÃO\nCONTAS A PAGAR",
]
(COMP, EMIS, NF, VAL, FORN, INCL, VENC, LANC, PED, CTE, TIPO, LCTO, ADIC) = range(13)

DATE_COLS = (COMP, EMIS, INCL, VENC, LCTO)
REQUIRED = (COMP, EMIS, NF, VAL, FORN, VENC)   # highlighted in the UI when empty
COL_WIDTHS = [14, 13, 14, 14, 38, 14, 13, 16, 14, 12, 14, 16, 34]


# ---------------------------------------------------------------
# Formatting / parsing helpers (the review table stores plain text)
# ---------------------------------------------------------------
def fmt_date(d):
    return d.strftime("%d/%m/%Y") if d else ""


def fmt_comp(d):
    return d.strftime("%m/%Y") if d else ""


def fmt_money(v):
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_money(s):
    s = re.sub(r"[^\d,.\-]", "", s or "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)


def parse_date(s):
    s = (s or "").strip()
    for f in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def parse_comp(s):
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%m/%Y").date()
    except ValueError:
        return parse_date(s)


def _mk_date(d, m, y):
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


# ---------------------------------------------------------------
# PDF reading
# ---------------------------------------------------------------
OCR_TRIGGER_CHARS = 150     # OCR kicks in when the text layer holds less than this in total
OCR_PAGE_MIN_CHARS = 20     # ...and only pages with fewer characters than this are OCR'd


def _native_pages(path, max_pages):
    """Text of each page from the PDF's own text layer (PyMuPDF if installed, else pypdf)."""
    def _pymupdf():            # optional, best layout quality
        import fitz
        with fitz.open(path) as doc:
            return [pg.get_text() for pg in list(doc)[:max_pages]]

    def _pypdf():              # pure Python, works on any Python version
        from pypdf import PdfReader
        reader = PdfReader(path)
        return [(pg.extract_text() or "") for pg in reader.pages[:max_pages]]

    best = []
    for reader_fn in (_pymupdf, _pypdf):
        try:
            pages = reader_fn()
        except Exception:
            pages = []
        if sum(len(p.strip()) for p in pages) > sum(len(p.strip()) for p in best) or not best:
            best = pages
        if sum(len(p.strip()) for p in best) >= 30:
            break
    return [p.replace("\xa0", " ") for p in best]


def _page_count(path, max_pages):
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(path)
        try:
            return min(len(pdf), max_pages)
        finally:
            pdf.close()
    except Exception:
        return 1


def read_pdf_text_ex(path, max_pages=6, use_ocr=True, on_ocr=None, force_ocr=False):
    """Returns (text, used_ocr).
    The text layer is used when it exists. OCR runs when the PDF has (almost) no text, only on the
    empty pages, or on every page when force_ocr is set (e.g. a garbled text layer)."""
    pages = _native_pages(path, max_pages)
    total = sum(len(p.strip()) for p in pages)
    used, ocr_error = False, None

    if use_ocr and ocr.enabled() and (force_ocr or total < OCR_TRIGGER_CHARS):
        n = len(pages) or _page_count(path, max_pages)
        pages = pages + [""] * (n - len(pages))
        targets = list(range(n)) if force_ocr else \
            [i for i in range(n) if len(pages[i].strip()) < OCR_PAGE_MIN_CHARS]
        if targets:
            if on_ocr:
                on_ocr()
            try:
                found = ocr.ocr_pdf_pages(path, targets)
            except Exception as err:
                ocr_error = err
            else:
                for i, t in found.items():
                    if t.strip():
                        pages[i] = ocr.normalize_ocr_text(t)
                        used = True

    text = "\n".join(pages).replace("\xa0", " ")
    if len(text.strip()) < 30:
        if ocr_error:
            raise ValueError(f"No readable text in this PDF and OCR failed: {ocr_error}")
        if not use_ocr or not ocr.enabled():
            raise ValueError("No readable text in this PDF (scanned image?). Turn OCR on to read it.")
        raise ValueError("OCR could not find any text in this PDF.")
    return text, used


def read_pdf_text(path, max_pages=6):
    """Text only (see read_pdf_text_ex for the OCR flag)."""
    return read_pdf_text_ex(path, max_pages)[0]


# ---------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------
MONEY = r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})"
DATE = r"(\d{2})[/.\-](\d{2})[/.\-](\d{4})"
def _default_user():
    """Who is shown in LANÇADO POR: SYNVOX_USER env var, else the OS user name."""
    try:
        return os.environ.get("SYNVOX_USER") or getpass.getuser()
    except Exception:
        return "Synvox"


DEFAULT_LANCADO_POR = _default_user()
# a run of digits with the usual separators (spaces, dots, dashes, line breaks) that may hold a 44-digit key
KEY_RUN = re.compile(r"\d(?:[\s.\-]{0,2}\d){43,200}")
UF_CODES = {"11", "12", "13", "14", "15", "16", "17", "21", "22", "23", "24", "25", "26", "27",
            "28", "29", "31", "32", "33", "35", "41", "42", "43", "50", "51", "52", "53"}

VALUE_LABELS = [
    r"valor\s+total\s+da\s+nota",
    r"valor\s+total\s+da\s+nfs-?e",
    r"valor\s+total\s+do\s+servi[cç]o",
    r"valor\s+total\s+da\s+presta[cç][aã]o(?:\s+do\s+servi[cç]o)?",
    r"valor\s+l[ií]quido(?:\s+da\s+nota)?",
    r"total\s+a\s+pagar",
    r"valor\s+a\s+pagar",
    r"valor\s+do\s+documento",
    r"valor\s+da\s+fatura",
    r"valor\s+total",
]
ISSUE_LABELS = [
    r"data\s+(?:e\s+hora\s+)?(?:da\s+|de\s+)?emiss[aã]o",
    r"emitid[ao]\s+em",
    r"emiss[aã]o",
]
DUE_LABELS = [r"data\s+(?:de\s+)?vencimento", r"vencimento", r"venc\."]

NF_PATTERNS = [
    r"n[º°o]\.?\s*[:\-]?\s*(\d{3}\.\d{3}\.\d{3})\b",                 # DANFE style: Nº 261.073.661
    r"\b(\d{3}\.\d{3}\.\d{3})\b",
    r"n[úu]mero\s+da\s+(?:nota|nfs-?e|nf-?e)[^\d]{0,20}(\d[\d.]*)",
    r"nf-?e\s*(?:n[º°o]\.?|num\w*)\s*[:\-]?\s*(\d[\d.]*)",
    r"nota\s+fiscal[^\n\d]{0,40}?n[º°o]\.?\s*[:\-]?\s*(\d[\d.]*)",
    r"\bn[º°]\s*[:\-]?\s*(\d{1,3}(?:\.\d{3})+|\d{3,9})\b",
    r"fatura[^\d\n]{0,20}(\d{3,})",
]
PO_PATTERN = (r"(?:pedido(?:\s+de\s+compras?)?|ped\.?\s*(?:de\s+)?compra|ordem\s+de\s+compra|\bp\.?o\.?)"
              r"\s*(?:n[º°o]\.?)?\s*[:\-#]?\s*(\d{5,12})\b")

_REJECT_NAME = re.compile(
    r"danfe|documento|nota\s+fiscal|destinat|chave|natureza|inscri|endere|"
    r"^s[ée]rie|tomador|cnpj|cpnj|cpf|^\W*$|^(?:ie|cep|nome|raz[aã]o|social|fone|telefone|"
    r"remetente|expedidor|recebedor|munic[ií]pio)\b", re.I)
_COMPANY_WORD = re.compile(
    r"\b(ltda|eireli|epp|s\.?\s?/?\s?a|transportes?|log[ií]stica|ind[úu]stria|com[ée]rcio|servi[cç]os)\b", re.I)


def _clean_name(s):
    s = re.sub(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", "", s)      # CNPJ
    s = re.split(r"\s{2,}|\bcnpj\b|\bcpnj\b|\bcpf\b|\binscri", s, flags=re.I)[0]
    s = s.strip(" :-–|,.;")
    if re.search(r"\s-\s?[A-Z]{2}$", s):          # "CITY - UF" is an address, not a company
        return ""
    if len(s) < 4 or len(re.findall(r"\d", s)) > 4 or _REJECT_NAME.search(s):
        return ""
    return s


def _key_ok(k):
    """44-digit access key: valid UF, month, model and the mod-11 check digit."""
    if len(k) != 44 or k[:2] not in UF_CODES or not 1 <= int(k[4:6]) <= 12:
        return False
    if k[20:22] not in ("55", "57", "65", "67"):
        return False
    w, t = 2, 0
    for d in reversed(k[:43]):
        t += int(d) * w
        w = w + 1 if w < 9 else 2
    r = t % 11
    return (0 if r < 2 else 11 - r) == int(k[43])


# digits that OCR engines swap for one another
_SWAPS = {"0": "83", "1": "7", "2": "7", "3": "8", "4": "9", "5": "6", "6": "5", "7": "12", "8": "03", "9": "4"}


def _repair_key(k):
    """44 digits that fail the check digit because OCR misread ONE digit: try the usual swaps and
    accept the result only if exactly one candidate is a valid key (otherwise it is ambiguous)."""
    found = set()
    for i, d in enumerate(k):
        for alt in _SWAPS.get(d, ""):
            cand = k[:i] + alt + k[i + 1:]
            if _key_ok(cand):
                found.add(cand)
    return found.pop() if len(found) == 1 else None


def _find_keys(text, repair=False):
    """All valid access keys in the text, in order of appearance, without duplicates.
    repair=True (OCR text) also fixes a single misread digit in a 44-digit run."""
    keys = []
    for m in KEY_RUN.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        hit = False
        for off in range(len(digits) - 43):
            k = digits[off:off + 44]
            if _key_ok(k):
                hit = True
                if k not in keys:
                    keys.append(k)
        if repair and not hit and len(digits) == 44:
            k = _repair_key(digits)
            if k and k not in keys:
                keys.append(k)
    return keys


def _key_number(k):
    return str(int(k[25:34]))


def _find_money(text):
    for lab in VALUE_LABELS:
        m = re.search(lab + r"[^\d]{0,60}?" + MONEY, text, re.I)
        if m:
            return parse_money(m.group(1))
    vals = [parse_money(x) for x in re.findall(MONEY, text)]
    vals = [v for v in vals if v]
    return max(vals) if vals else None


def _find_dates_after(labels, text):
    out = []
    for lab in labels:
        for m in re.finditer(lab + r"[^\d]{0,40}?" + DATE, text, re.I):
            d = _mk_date(m.group(1), m.group(2), m.group(3))
            if d:
                out.append(d)
        if out:
            break
    return out


def _find_supplier(text):
    m = re.search(r"recebemos\s+de\s+(.+?)\s+os\s+(?:produtos|servi)", text, re.I | re.S)
    if m:
        c = _clean_name(" ".join(m.group(1).split()))
        if c:
            return c
    # the issuer's name is normally printed in the page header with a company suffix
    for l in [x.strip() for x in text.splitlines() if x.strip()][:15]:
        if _COMPANY_WORD.search(l):
            c = _clean_name(l)
            if c:
                return c
    labels = (r"(?:nome\s*/\s*raz[aã]o\s+social|raz[aã]o\s+social|nome\s+empresarial|"
              r"prestador(?:\s+de\s+servi[cç]os?)?|emitente|fornecedor|benefici[aá]rio)")
    for m in re.finditer(labels + r"\s*[:\-]?\s*\n?\s*([^\n]+)", text, re.I):
        c = _clean_name(m.group(1))
        if c:
            return c
    lines = [l.strip() for l in text.splitlines()]
    for i, l in enumerate(lines):
        if re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", l):
            for cand in (re.sub(r"\d.*$", "", l), lines[i - 1] if i else ""):
                c = _clean_name(cand)
                if c:
                    return c
            break
    return ""


FATURA_MARK = r"c[óo]d\.?\s*fatura|id\s+fatura|\bFAT\d{6,}"


def _fatura_block(text):
    """Small window around the 'CÓD. FATURA / ID FATURA' summary box (EMISSÃO, VENCIMENTO, VALOR)."""
    m = re.search(FATURA_MARK, text, re.I)
    return text[max(0, m.start() - 200): m.start() + 400] if m else ""


def _fatura_dates(blk):
    """(emissão, vencimento) from the invoice summary box: by label, else by order (emissão first)."""
    def labeled(label):
        m = re.search(label + r"[^\d]{0,25}" + DATE, blk, re.I)
        return _mk_date(*m.groups()) if m else None

    emis, venc = labeled(r"emiss[aã]o"), labeled(r"vencimento")
    dates = [d for d in (_mk_date(*m.groups()) for m in re.finditer(DATE, blk)) if d]
    if not emis and dates:
        emis = dates[0]
    if (not venc or (emis and venc < emis)) and emis:
        venc = next((d for d in dates if d > emis), venc)
    return emis, venc


def _filename_number(filename):
    """Longest 7-12 digit run in the PDF file name (ignoring things that look like dates)."""
    best = ""
    for n in re.findall(r"\d{7,12}", filename or ""):
        if len(n) == 8 and (_mk_date(n[:2], n[2:4], n[4:]) or _mk_date(n[6:], n[4:6], n[:4])):
            continue
        if len(n) > len(best):
            best = n
    return best.lstrip("0")


def parse_text(text, lancado_por="", tipo_default="", today=None, filename="", ocr=False):
    """Returns (row[13 strings], missing_field_names)."""
    today = today or date.today()
    row = [""] * len(HEADERS)

    keys = _find_keys(text, repair=ocr)
    nfe_keys = [k for k in keys if k[20:22] in ("55", "65")]
    cte_keys = [k for k in keys if k[20:22] in ("57", "67")]
    head = text[:1500]
    # CT-e only when the document itself is one (title/header), not when a CT-e is merely mentioned
    # a "fatura" (bill) groups several CT-es/NFs: its own code (FAT...) is the document number
    fat = re.search(r"c[óo]d\.?\s*fatura\D{0,12}?(\d{6,12})|\bFAT\s*(\d{6,12})\b", text, re.I)
    fat_num = ((fat.group(1) or fat.group(2)).lstrip("0")) if fat else ""
    is_fatura = bool(re.search(FATURA_MARK, text, re.I))
    is_cte = (not is_fatura) and bool(re.search(r"dacte|conhecimento\s+de\s+transporte", head, re.I)) and \
        (bool(cte_keys) or not nfe_keys)

    def from_patterns():
        for pat in NF_PATTERNS:
            m = re.search(pat, text, re.I)
            if m:
                n = re.sub(r"\D", "", m.group(1)).lstrip("0")
                if n:
                    return n
        return ""

    if is_fatura:
        row[NF] = fat_num
        key = ""
    elif is_cte:
        # CTE column = the freight document; FATURA / NF = the invoice(s) the freight refers to
        row[CTE] = _key_number(cte_keys[0]) if cte_keys else ""
        if not row[CTE]:
            m = re.search(r"n[úu]mero[^\d]{0,15}(\d{1,9})\b", head, re.I)
            row[CTE] = m.group(1).lstrip("0") if m else ""
        nums = list(dict.fromkeys(_key_number(k) for k in nfe_keys))
        row[NF] = " / ".join(nums)
        key = (cte_keys or [""])[0]
    else:
        key = (nfe_keys or cte_keys or [""])[0]
        row[NF] = _key_number(key) if key else from_patterns()

    # the PDF file name usually carries the document number: trust it when the text confirms it
    name_num = _filename_number(filename)
    flat = re.sub(r"[\s.\-/]", "", text)
    if not (is_fatura and fat_num):
        if name_num and name_num in flat:
            row[NF] = name_num
        elif not row[NF] and name_num:
            row[NF] = name_num

    # dates
    blk = _fatura_block(text) if is_fatura else ""
    fat_emis, fat_venc = _fatura_dates(blk) if blk else (None, None)
    issues = _find_dates_after(ISSUE_LABELS, text)
    emis = fat_emis or (issues[0] if issues else None)
    if not emis:
        m = re.search(DATE, text)
        emis = _mk_date(*m.groups()) if m else None
    row[EMIS] = fmt_date(emis)

    if emis:
        row[COMP] = fmt_comp(emis)
    elif key:
        yy, mm = int(key[2:4]), int(key[4:6])
        if 1 <= mm <= 12:
            row[COMP] = f"{mm:02d}/{2000 + yy}"

    dues = [] if fat_venc else _find_dates_after(DUE_LABELS, text)
    if fat_venc:
        row[VENC] = fmt_date(fat_venc)
    elif dues:
        later = [d for d in dues if not emis or d >= emis]
        row[VENC] = fmt_date((later or dues)[0])

    # amount / supplier / PO
    val = None
    if blk:
        # the summary box prints the amount as "R$ 38.025,75"; dates may sit between label and value
        m = re.search(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})", blk) or \
            re.search(r"\bvalor\b[^\d]{0,15}" + MONEY, blk, re.I)
        val = parse_money(m.group(1)) if m else None
    val = val or _find_money(text)
    row[VAL] = fmt_money(val) if val else ""
    row[FORN] = _find_supplier(text)
    m = re.search(PO_PATTERN, text, re.I)
    row[PED] = m.group(1) if m else ""

    # values that come from the operator / system
    row[INCL] = fmt_date(today)
    row[LANC] = lancado_por or DEFAULT_LANCADO_POR
    row[TIPO] = "Fatura" if is_fatura else ("CTE" if is_cte else (tipo_default or "NF"))

    missing = [HEADERS[i].replace("\n", " ").strip() for i in REQUIRED if not row[i]]
    return row, missing


def extract_invoice(path, lancado_por="", tipo_default="", dump_dir=None, use_ocr=True, on_ocr=None):
    """Returns (row, missing_field_names, used_ocr).
    on_ocr is called (no arguments) right before OCR starts, so a UI can say "running OCR..."."""
    name = os.path.basename(path)
    text, used = read_pdf_text_ex(path, use_ocr=use_ocr, on_ocr=on_ocr)
    row, missing = parse_text(text, lancado_por, tipo_default, filename=name, ocr=used)

    # A text layer can exist and still be garbage (broken fonts). If the parse found almost nothing,
    # OCR the pages and keep whichever reading is more complete.
    if not used and use_ocr and ocr.enabled() and len(missing) >= 2:
        try:
            text2, used2 = read_pdf_text_ex(path, use_ocr=True, on_ocr=on_ocr, force_ocr=True)
            row2, missing2 = parse_text(text2, lancado_por, tipo_default, filename=name, ocr=used2)
            if used2 and len(missing2) < len(missing):
                text, row, missing, used = text2, row2, missing2, True
        except Exception:
            pass

    if dump_dir:                      # keep the raw text so a bad extraction can be diagnosed
        try:
            os.makedirs(dump_dir, exist_ok=True)
            with open(os.path.join(dump_dir, name + (".ocr.txt" if used else ".txt")), "w",
                      encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass
    return row, missing, used


# ---------------------------------------------------------------
# Export
# ---------------------------------------------------------------
def convert_row(row):
    """Text cells -> typed Excel values. Raises ValueError naming the bad column."""
    out = []
    for i, raw in enumerate(row):
        s = (raw or "").strip()
        name = HEADERS[i].replace("\n", " ").strip()
        if not s:
            out.append(None)
        elif i == COMP:
            d = parse_comp(s)
            if not d:
                raise ValueError(f"{name}: invalid value '{s}' (use MM/YYYY)")
            out.append(d)
        elif i in DATE_COLS:
            d = parse_date(s)
            if not d:
                raise ValueError(f"{name}: invalid date '{s}' (use DD/MM/YYYY)")
            out.append(d)
        elif i == VAL:
            try:
                out.append(parse_money(s))
            except ValueError:
                raise ValueError(f"{name}: invalid amount '{s}'")
        elif i in (NF, PED, CTE) and s.isdigit():
            out.append(int(s))
        else:
            out.append(s)
    return out


def export_xlsx(rows, path):
    """Writes rows in the model. If the file exists, rows are appended.
    Returns (rows_written, appended: bool)."""
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    typed = [convert_row(r) for r in rows]     # validate everything before touching the file

    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    appended = os.path.exists(path)

    if appended:
        wb = load_workbook(path)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Synvox Invoices"

    if ws.cell(1, 1).value is None:
        for c, h in enumerate(HEADERS, 1):
            cell = ws.cell(1, c, h)
            cell.font = Font(bold=True, color="F6EECA")
            cell.fill = PatternFill("solid", fgColor="0D1311")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
            ws.column_dimensions[cell.column_letter].width = COL_WIDTHS[c - 1]
        ws.row_dimensions[1].height = 45
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{ws.cell(1, len(HEADERS)).column_letter}1"

    last = ws.max_row
    while last > 1 and all(c.value is None for c in ws[last]):
        last -= 1

    for n, vals in enumerate(typed, last + 1):
        for c, v in enumerate(vals, 1):
            cell = ws.cell(n, c, v)
            cell.border = border
            i = c - 1
            if i == COMP:
                cell.number_format = "mm/yyyy"
            elif i in DATE_COLS:
                cell.number_format = "dd/mm/yyyy"
            elif i == VAL:
                cell.number_format = "#,##0.00"
            if i in DATE_COLS or i in (NF, PED, CTE, TIPO):
                cell.alignment = Alignment(horizontal="center")

    wb.save(path)
    return len(typed), appended
