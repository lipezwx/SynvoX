# Changelog

## 1.0.0 (2026-11-17)

- Rebranded from PyCallebaut to **Synvox**: new name, logo, icon and a cream-on-ink colour palette.
- Restructured into an installable package (`synvox_invoice`) with tests.
- Logs and export default now go to per-user folders instead of next to the executable.
- `LANÇADO POR` defaults to the `SYNVOX_USER` environment variable, or the OS user name.
- Exported XLSX header uses the Synvox palette.
- Added PyInstaller spec, Inno Setup installer and a GitHub Actions workflow that builds it.
