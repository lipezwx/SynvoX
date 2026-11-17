# Synvox visual identity

The identity uses two colours, sampled from the brand reference image, and derives everything else from them.

| Token | Hex | Use |
|---|---|---|
| Ink | `#0D1311` | Window canvas, XLSX header fill |
| Cream | `#F6EECA` | Text, accents, primary button, logo |
| Cream Hi | `#FFF8DA` | Hover on cream surfaces |
| Cream Dim | `#CFC699` | Pressed state, muted accents |
| Surface | `#141C19` | Cards, popups |
| Forest | `#2B4A3B` | Hero glow, drop-zone gradient |
| Forest Deep | `#16261F` | Table header |
| Danger | `#E0785A` | Missing or invalid fields (the only non-brand hue) |

## Logo

A rounded-square frame holding an **S** built from two stacked arcs (one continuous stroke), followed by the **SYNVOX** wordmark in a heavy sans-serif. The S nods to *sync*: two halves of one flow.

- `src/synvox_invoice/assets/synvox_icon.svg|png|ico`: app icon (cream on ink)
- `src/synvox_invoice/assets/synvox_logo.png`: horizontal lockup, cream on transparent
- Regenerate everything with `python scripts/make_assets.py`

## Rules

- Cream text on Ink or Forest only. Never put cream text on a light surface.
- Primary action = solid cream button with Ink text. Secondary = ghost (cream at 6% fill, 16% border).
- Keep clear space around the mark equal to the stroke width of the frame ×4.
- Tokens live in `src/synvox_invoice/theme.py`; change colours there, not inline.
