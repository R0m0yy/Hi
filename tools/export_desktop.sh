#!/bin/sh
# Export the desktop builds into build/desktop/<platform>/.
#   tools/export_desktop.sh                 # Linux, Windows and macOS
#   tools/export_desktop.sh Linux           # one preset (names from game/export_presets.cfg)
# Needs Godot 4.4.1 (GODOT, default "godot") and the matching official export
# templates in ~/.local/share/godot/export_templates/4.4.1.stable/.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-godot}
PRESETS=${*:-"Linux Windows macOS"}

"$GODOT" --headless --path "$ROOT/game" --import 2>&1 | grep -E "SCRIPT ERROR" || true
for preset in $PRESETS; do
	case $preset in
		Linux) dir=linux; out=ParadiseUntamed.x86_64 ;;
		Windows) dir=windows; out=ParadiseUntamed.exe ;;
		macOS) dir=macos; out=ParadiseUntamed.zip ;;
		*) echo "unknown preset $preset"; exit 1 ;;
	esac
	mkdir -p "$ROOT/build/desktop/$dir"
	rm -f "$ROOT/build/desktop/$dir/$out"
	echo "== $preset"
	"$GODOT" --headless --path "$ROOT/game" --export-release "$preset" "$ROOT/build/desktop/$dir/$out" 2>&1 \
		| grep -vE "^\s*$|Godot Engine v|Vulkan|savepack|ObjectDB|resources still in use|at: (cleanup|clear)" || true
	test -s "$ROOT/build/desktop/$dir/$out" || { echo "export failed: $preset"; exit 1; }
	cp "$ROOT/tools/export/GODOT_LICENSE.txt" "$ROOT/build/desktop/$dir/"
	cp "$ROOT/docs/LICENSES.md" "$ROOT/build/desktop/$dir/LICENSES.md"
	cp "$ROOT/tools/export/PLAYING.txt" "$ROOT/build/desktop/$dir/"
	ls -la "$ROOT/build/desktop/$dir"
done
