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

1. **Drop PDFs** (one or many) onto the window, or click to browse.
2. **Extraction** reads each PDF and fills the 13 columns of the *Contas a Pagar* model.
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

Scanned PDFs without a text layer are reported, not guessed (OCR is not included).

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

Optional: `pip install PyMuPDF` for better text layout on difficult PDFs. It is used automatically when present.

## Build the installer yourself

Requires Python 3.10+ and [Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`).

```powershell
.\installer\build_installer.ps1 -Version 1.0.0
```

The script creates a venv, runs the tests, regenerates the brand assets, builds the app with PyInstaller
(`installer/synvox.spec`) and compiles `installer/synvox.iss`.
The result is `installer\Output\Synvox-Invoice-Extractor-Setup-1.0.0.exe`.

Pushing a tag such as `v1.0.0` makes the GitHub Actions workflow build the installer and attach it to a release.

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
  app.py         Qt window, drop zone, review table
  theme.py       Synvox design tokens and stylesheet
  paths.py       asset and per-user data locations
  assets/        logo, icon (svg / png / ico)
tests/           pytest suite for the extraction logic
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
