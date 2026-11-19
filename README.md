<p align="center">
  <img src="docs/logo.png" alt="Synvox" height="90">
</p>

<h1 align="center">Synvox Invoice Extractor</h1>

<p align="center">
  Drop invoice PDFs, review what was read, export to a fixed Excel model.<br>
  A desktop app for accounts-payable teams. Reads Brazilian NF-e, CT-e, NFS-e and freight "fatura" PDFs.
</p>

<p align="center">
  <img src="docs/screenshot.png" alt="Synvox Invoice Extractor" width="860">
</p>

## What it does

1. **Drop PDFs** (one or many) onto the window, or click to browse. Text PDFs and scanned images both work.
2. **Extraction** reads each PDF (with **OCR** when it has no text layer) and fills the 13 columns of the *Contas a Pagar* model.
3. **Review** in an editable table. Required cells left empty are highlighted so nothing slips through.
4. **Export XLSX**. If the target file already exists, new rows are appended below the last filled row.

### What gets extracted

| Column | How it is found |
|---|---|
| FATURA / NF | 44-digit access key (validated with the mod-11 check digit), else label patterns, else the PDF file name |
| CTE | For CT-e documents, the freight document number from its key; the NF column then lists the invoices it refers to |
| VALOR | Labelled totals (`Valor total da nota`, `Total a pagar`, ...) with a safe fallback |
| DATA EMISSÃO / MÊS DE COMPETÊNCIA | Issue date labels; competence is derived from it, or from the key if no date is printed |
| DATA DE VENCTO | Due-date labels, rejecting due dates earlier than the issue date |
| FORNECEDOR | "Recebemos de ...", the page header, or a labelled issuer / provider field |
| PEDIDO | Purchase-order patterns |
| TIPO OPERAÇÃO | `NF`, `CTE`, `Fatura` detected; otherwise the default chosen in the app |
| LANÇADO POR / DATA INCLUSÃO | The operator field and today's date |

## OCR (scanned and image-only PDFs)

Many suppliers send scans or photos saved as PDF. Synvox reads these automatically:

- **When it runs**: if a PDF has (almost) no text layer, only the empty pages are OCR'd. It also runs as a second
  chance when the text layer exists but is garbage (broken fonts) and the normal parse finds almost nothing;
  the more complete reading wins.
- **Engines** (best available is picked automatically):
  1. **Tesseract** with the Portuguese model, if installed (best accuracy on accents).
  2. **RapidOCR**, bundled with the installer: offline, no setup, no internet.
- **OCR-aware parsing**: look-alike characters inside numbers are fixed (`O`→`0`, `l`→`1`, `S`→`5`), and an access
  key with a single misread digit is repaired using its check digit, but only when exactly one fix is valid.
- **In the app**: rows read with OCR are tagged `· OCR` in the *Source PDF* column and show a "double-check" hint.
  The **OCR: on/off** button next to the filters turns it off (scanned PDFs are then rejected with a clear message).
- **Speed**: about 1 to 2 s per page with Tesseract, 5 to 10 s with RapidOCR (the first file also loads the models).

| Setting | Effect |
|---|---|
| `SYNVOX_OCR=0` | Disable OCR entirely |
| `SYNVOX_OCR_ENGINE=tesseract` or `rapidocr` | Force one engine (default `auto`) |
| `SYNVOX_TESSERACT=C:\path\tesseract.exe` | Point to a Tesseract install in a custom location |

To use Tesseract on Windows, install it from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and tick
the **Portuguese** language data during setup. Synvox finds it automatically.

OCR output is never perfect on poor scans: always review the highlighted cells before exporting.

## Install (Windows)

Download `Synvox-Invoice-Extractor-Setup-<version>.exe` from the
[Releases](../../releases) page (or from the **Build** workflow artifacts) and run it.
It installs per user by default, adds a Start Menu entry and an optional desktop shortcut, and has a normal uninstaller.

## Run from source

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python -m synvox_invoice        # with PYTHONPATH=src, or: pip install -e .
```

Optional: `pip install PyMuPDF` for better text layout on difficult PDFs, and Tesseract (+ `por` language pack) for the most accurate OCR. Both are used automatically when present.

## Build the installer yourself

**Easiest:** double-click `BUILD-INSTALLER.bat`. It installs Python and Inno Setup with winget if missing, builds the app and opens `installer\Output` with the finished setup `.exe`.

Manual route:

Requires Python 3.10+ and [Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`).

```powershell
.\installer\build_installer.ps1 -Version 1.1.0
```

The script creates a venv, runs the tests, regenerates the brand assets, builds the app with PyInstaller
(`installer/synvox.spec`) and compiles `installer/synvox.iss`.
The result is `installer\Output\Synvox-Invoice-Extractor-Setup-1.1.0.exe`.

Pushing a tag such as `v1.1.0` makes the GitHub Actions workflow build the installer and attach it to a release.

## Configuration

| Setting | Where |
|---|---|
| Default *LANÇADO POR* | `SYNVOX_USER` environment variable, else the OS user name (editable in the app) |
| Raw-text dumps for diagnosing a bad extraction | `%LOCALAPPDATA%\Synvox\InvoiceExtractor\logs` |
| Default export location | `Documents\Contas_a_Pagar.xlsx` |

## Project layout

```
src/synvox_invoice/
  core.py        PDF text extraction, field parsing, XLSX export (no GUI code)
  ocr.py         OCR engines (Tesseract, RapidOCR), page rendering, OCR text clean-up
  app.py         Qt window, drop zone, review table
  theme.py       Synvox design tokens and stylesheet
  paths.py       asset and per-user data locations
  assets/        logo, icon (svg / png / ico)
tests/           pytest suite: extraction logic and OCR (builds a scanned PDF on the fly)
installer/       PyInstaller spec, Inno Setup script, build script
scripts/         make_assets.py (generates the logo and icons)
docs/            brand guide, screenshot
```

## Develop

```bash
pip install -r requirements-dev.txt
pytest
python scripts/make_assets.py   # after changing the logo
```

## Brand

Two-colour identity, ink `#0D1311` and cream `#F6EECA`. See [docs/BRAND.md](docs/BRAND.md).

## License

[MIT](LICENSE)
