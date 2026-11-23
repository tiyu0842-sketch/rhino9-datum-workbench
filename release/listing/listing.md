# Datum Plane Tools — Rhino 9

**Short description (for the listing card):**
Create datum planes on any face or from three points, align CPlane + gumball to them, and work on sloped surfaces as if they were top view. Includes two eye-friendly clay display modes for reading surface flow.

---

## What it does

Datum Plane Tools brings a SolidWorks-style datum plane workflow to Rhino 9:

- **Create a datum plane** from three points, or by clicking directly on a planar face of a solid/polysurface — no modifier keys needed.
- **Align automatically**: the construction plane and gumball snap to the datum, its origin sits at the face's area centroid, X/Y follow the face UV directions, Z is the normal.
- **Switch between datums** by picking an existing one or entering its number; switching never creates a duplicate.
- **5th normal viewport**: splits the Top viewport vertically and aims the camera perpendicular to the datum plane — model on the slope as if it were a top view.
- **Exit cleanly**: restores the exact original CPlane, gumball alignment and all construction-plane settings, per viewport. Leftover datums from older sessions are self-healed on exit.

### Two observation display modes

Both use directional three-tone clay shading (highlight / midtone / shadow, no blown-out white) and are meant for **reading surface curvature and flow**:

| Mode | Isocurve density | Use |
|---|---|---|
| Alias EyeCare (light) | 0 (edges only) | Clean, quiet view |
| Alias EyeCare Dark | 1 (one internal isocurve) | Read surface flow on a dark background |

Each mode can be applied with `AliasStyle` (menu I / J) and fully restored with `AliasStyleRestore` (M). Isocurve density is also adjustable at any time via `AliasStyle → Density` (K).

## Commands

`JZ` / `DatumPlane` opens a single letter-coded menu:

| Key | Action | Key | Action |
|---|---|---|---|
| A | Three-point datum | F | Lock datum |
| B | Pick planar face | G | 5th normal viewport |
| C | Pick existing datum | H | Restore / exit |
| D | Recall by number | N | Close 5th viewport |
| E | Save current plane | | |

Display modes are separate commands: `AliasStyleLight` / `AliasStyleDark` / `AliasStyleRestore`.

All functions also have standalone commands for toolbar buttons or scripts. Prompts are bilingual (Chinese / English).

## Requirements

- Rhino 9 (Windows), .NET 8
- Install via `.yak` (the legacy `.rhi` installer cannot load .NET 8 plugins)

## Install

1. Download `DatumPlane_v2_8.yak`.
2. In Rhino, run `_PackageManager` → *Install from file…* and choose the `.yak`, **or** simply drag the `.yak` onto an open Rhino window.
3. Restart Rhino.

The included toolbar group "基准面工具" should appear automatically. If the buttons are missing, run `JZ` — every command is available from the menu.

## License

MIT. Free for personal and commercial use.
