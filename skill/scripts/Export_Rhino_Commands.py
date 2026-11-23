# Export_Rhino_Commands.py
# Run INSIDE Rhino 9's Python interpreter (e.g. via the Rhino MCP run_python tool),
# not with a standalone Python. Exports every registered command name.
#
# Optional overrides (set as globals before exec):
#   OUT_PATH            - output .txt path
#   INCLUDE_LOCALIZED   - also export localized names (may be identical on en-US builds)
#
# Verified signature on Rhino 9.1.26314.9001:
#   Rhino.Commands.Command.GetCommandNames(bool english, bool loaded) -> String[]
#   loaded=True  -> commands from currently loaded plug-ins
#   loaded=False -> full registered command table (includes not-yet-loaded plug-ins)
# Command names ARE session-cached: a name being present does NOT prove the
# plug-in is loaded or its panel registered. See experiment-log E-016 / E-018.

import os
from Rhino.Commands import Command

_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT_PATH = globals().get("OUT_PATH") or os.path.join(_HERE, "rhino_commands_all.txt")
INCLUDE_LOCALIZED = globals().get("INCLUDE_LOCALIZED", False)

full = sorted(set(Command.GetCommandNames(True, False)))
loaded = sorted(set(Command.GetCommandNames(True, True)))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for n in full:
        f.write(n + "\n")

print("Rhino: %s" % Rhino.RhinoApp.Version)
print("full registered : %d" % len(full))
print("loaded plug-ins : %d" % len(loaded))
print("wrote           : %s" % OUT_PATH)

if INCLUDE_LOCALIZED:
    loc = sorted(set(Command.GetCommandNames(False, False)))
    p2 = os.path.splitext(OUT_PATH)[0] + "_localized.txt"
    with open(p2, "w", encoding="utf-8") as f:
        for n in loc:
            f.write(n + "\n")
    print("localized       : %d -> %s" % (len(loc), p2))
