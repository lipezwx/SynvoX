# Changelog

## 1.2.0 (2026-11-23)

- **UI redesign, iOS style**: large title, bigger type everywhere (16 px body, 24 px headings), pill-shaped
  fields and buttons, translucent "glass" surfaces over a soft animated glow. Same Ink/Cream identity and logo.
- Neutral tones now come from an Ink→Cream tonal ramp (same recipe as Raining Md), so surfaces, hairlines and
  captions stay on-brand. New `mix()` helper and `PANEL`, `LINE`, `MUTED`, `SOFT`… tokens in `theme.py`.
- Simpler flow: one big drop zone with a progress spinner and "N left" counter, fields with captions above them,
  an **OCR switch** (replaces the *OCR: on/off* button), an empty state, and a summary + big **Export XLSX**
  button at the bottom.
- Buttons only enable when they make sense (*Remove selected* needs a selection; *Clear all* and *Export* need rows).
- Review list restyled: no grid lines, hairline rows, 54 px rows, headers sized to fit and aligned with their
  data, file names elided with the full path in the tooltip, empty required cells shown as a rounded red wash.
- Window is resizable (drag the bottom-right corner) and sized to fit smaller screens.
- Focus ring only for keyboard navigation.

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
