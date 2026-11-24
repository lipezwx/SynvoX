# Synvox visual identity

The identity uses two colours, sampled from the brand reference image, and derives everything else from them.
The neutral steps are plain mixes of Ink and Cream, the same recipe Raining Md uses, so the two apps share one family.

| Token | Hex | Use |
|---|---|---|
| Ink | `#0D1311` | Window canvas, XLSX header fill |
| Cream | `#F6EECA` | Text, accents, primary button, logo |
| Cream Hi | `#FFF8DA` | Hover on cream surfaces |
| Cream Dim | `#CFC699` | Pressed state, muted accents |
| Surface | `#141C19` | Cards, popups |
| Forest | `#2B4A3B` | Ambient glow behind the glass (Synvox-only accent) |
| Forest Deep | `#16261F` | Deep glow |
| Danger | `#E0785A` | Missing or invalid fields (the only non-brand hue) |

### Tonal ramp (Ink → Cream)

| Token | Mix | Use |
|---|---|---|
| Panel | 5% | Resting cards |
| Panel 2 | 9% | Raised cards |
| Hover | 10% | Hover fills |
| Press | 17% | Pressed fills |
| Line | 15% | Hairlines |
| Dim | 30% | De-emphasised text |
| Muted | 50% | Captions, hints, placeholders |
| Soft | 74% | Secondary text |

## Logo

A rounded-square frame holding an **S** built from two stacked arcs (one continuous stroke), followed by the **SYNVOX** wordmark in a heavy sans-serif. The S nods to *sync*: two halves of one flow.

- `src/synvox_invoice/assets/synvox_icon.svg|png|ico`: app icon (cream on ink)
- `src/synvox_invoice/assets/synvox_logo.png`: horizontal lockup, cream on transparent
- Regenerate everything with `python scripts/make_assets.py`

## Interface

The app follows an iOS-like language: big type, pills, translucent glass, little chrome.

| Element | Spec |
|---|---|
| Screen title | 40 px bold, with a 16 px greeting above it |
| Card titles, counts | 24 px semibold |
| Body, inputs, buttons, table | 16 px (table 15 px) |
| Captions, column headers | 13 px semibold, uppercase, Muted |
| Fields and buttons | 46 px tall pills (fully rounded) |
| Primary button | 58 px tall pill, solid cream, Ink text, soft cream glow |
| Cards and drop zone | 28 to 32 px radius |
| Glass | cream veil (≈14% at the top, ≈5% at the bottom) with a 1 px rim light that is brighter at the top |

## Rules

- Cream text on Ink or Forest only. Never put cream text on a light surface.
- One primary action per screen: the solid cream pill. Secondary = glass pill. Never two cream pills side by side.
- Disabled controls fade to about 40%; do not hide them, so the layout never jumps.
- Show a focus ring for keyboard focus only, never after a mouse click.
- Danger is for missing data only, shown as a soft rounded wash, never as a solid block.
- Keep clear space around the mark equal to the stroke width of the frame ×4.
- Tokens live in `src/synvox_invoice/theme.py`; change colours there, not inline.
