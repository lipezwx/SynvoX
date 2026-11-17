# Changelog

## 1.1.0 (2026-11-17)

- **OCR** for scanned and image-only PDFs: Tesseract (Portuguese) when installed, otherwise the bundled RapidOCR engine.
- Per-page fallback: only empty pages are OCR'd; garbled text layers get a second OCR pass.
- OCR-aware parsing: digit look-alike correction and single-digit repair of NF-e/CT-e access keys.
- UI: **OCR: on/off** toggle, "running OCR" notice, `· OCR` marker on rows read that way.
- `extract_invoice` now returns `(row, missing, used_ocr)`.
- Installer bundles the OCR models and native libraries (larger download).

## 1.0.0 (2026-11-17)

- Rebranded from PyCallebaut to **Synvox**: new name, logo, icon and a cream-on-ink colour palette.
- Restructured into an installable package (`synvox_invoice`) with tests.
- Logs and export default now go to per-user folders instead of next to the executable.
- `LANÇADO POR` defaults to the `SYNVOX_USER` environment variable, or the OS user name.
- Exported XLSX header uses the Synvox palette.
- Added PyInstaller spec, Inno Setup installer and a GitHub Actions workflow that builds it.
