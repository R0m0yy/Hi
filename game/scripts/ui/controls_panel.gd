class_name ControlsPanel
extends VBoxContainer
## The control guide: keyboard/mouse and gamepad side by side.

const ROWS := [
	["Move", "WASD / arrow keys", "Left stick"],
	["Run (uses stamina)", "Shift", "LT or click left stick"],
	["Jump", "Space", "A"],
	["Interact (gather, open, board, cook)", "E", "X"],
	["Use the selected tool / eat / place", "Left mouse", "RT"],
	["Dive (hold, in deep water)", "Ctrl or C", "B"],
	["Cancel (fishing, building)", "Right mouse or Q", "B"],
	["Rotate while building", "R", "D-pad right"],
	["Hotbar slot", "1 – 6, Z / X", "LB / RB"],
	["Pack and crafting", "Tab or I", "Y"],
	["Camera zoom", "Mouse wheel, + / –", "D-pad up / down"],
	["Pause menu", "Esc", "Start"],
	["Quick save / load", "F5 / F9", "Pause menu"],
	["Boat: throttle / steer / step off", "W S / A D / E", "Left stick / X"],
	["Fishing", "Hold to charge, release to cast; press on the bite; hold to reel", ""],
]


func _init() -> void:
	add_theme_constant_override("separation", 6)
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 28)
	grid.add_theme_constant_override("v_separation", 8)
	for h in ["Action", "Keyboard & mouse", "Gamepad"]:
		grid.add_child(UITheme.label(h, 18, UITheme.ACCENT, true))
	for r in ROWS:
		grid.add_child(UITheme.label(r[0], 19))
		grid.add_child(UITheme.label(r[1], 19, UITheme.SAND))
		grid.add_child(UITheme.label(r[2], 19, UITheme.SAND))
	add_child(grid)
