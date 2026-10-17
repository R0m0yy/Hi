extends Node
## Registers the default input map at startup so bindings live in one
## readable place (and can later be rebound through InputMap).
## Keyboard + mouse and gamepad (Xbox layout names; other pads map to the
## same physical positions). Also tracks which device was used last so
## prompts can show the matching glyphs.

signal device_changed(using_gamepad: bool)

const KEYS := {
	"move_forward": [KEY_W, KEY_UP],
	"move_back": [KEY_S, KEY_DOWN],
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"sprint": [KEY_SHIFT],
	"jump": [KEY_SPACE],
	"dive": [KEY_CTRL, KEY_C],
	"interact": [KEY_E],
	"inventory": [KEY_TAB, KEY_I],
	"pause": [KEY_ESCAPE],
	"cancel": [KEY_Q],
	"rotate_build": [KEY_R],
	"hotbar_1": [KEY_1],
	"hotbar_2": [KEY_2],
	"hotbar_3": [KEY_3],
	"hotbar_4": [KEY_4],
	"hotbar_5": [KEY_5],
	"hotbar_6": [KEY_6],
	"hotbar_next": [KEY_X],
	"hotbar_prev": [KEY_Z],
	"zoom_in": [KEY_EQUAL, KEY_KP_ADD],
	"zoom_out": [KEY_MINUS, KEY_KP_SUBTRACT],
	"quick_save": [KEY_F5],
	"quick_load": [KEY_F9],
}

const MOUSE := {
	"use_tool": [MOUSE_BUTTON_LEFT],
	"cancel": [MOUSE_BUTTON_RIGHT],
	"zoom_in": [MOUSE_BUTTON_WHEEL_UP],
	"zoom_out": [MOUSE_BUTTON_WHEEL_DOWN],
}

const PAD_BUTTONS := {
	"jump": [JOY_BUTTON_A],
	"interact": [JOY_BUTTON_X],
	"cancel": [JOY_BUTTON_B],
	"dive": [JOY_BUTTON_B],
	"inventory": [JOY_BUTTON_Y],
	"pause": [JOY_BUTTON_START],
	"sprint": [JOY_BUTTON_LEFT_STICK],
	"hotbar_prev": [JOY_BUTTON_LEFT_SHOULDER],
	"hotbar_next": [JOY_BUTTON_RIGHT_SHOULDER],
	"rotate_build": [JOY_BUTTON_DPAD_RIGHT],
	"zoom_in": [JOY_BUTTON_DPAD_UP],
	"zoom_out": [JOY_BUTTON_DPAD_DOWN],
}

## action: [axis, direction]
const PAD_AXES := {
	"move_left": [JOY_AXIS_LEFT_X, -1.0],
	"move_right": [JOY_AXIS_LEFT_X, 1.0],
	"move_forward": [JOY_AXIS_LEFT_Y, -1.0],
	"move_back": [JOY_AXIS_LEFT_Y, 1.0],
	"use_tool": [JOY_AXIS_TRIGGER_RIGHT, 1.0],
	"sprint": [JOY_AXIS_TRIGGER_LEFT, 1.0],
}

## Short labels for prompts: action -> [keyboard, gamepad]
const GLYPHS := {
	"interact": ["E", "X"],
	"use_tool": ["LMB", "RT"],
	"cancel": ["RMB", "B"],
	"jump": ["Space", "A"],
	"dive": ["Ctrl", "B"],
	"sprint": ["Shift", "LT"],
	"inventory": ["Tab", "Y"],
	"rotate_build": ["R", "→"],
	"pause": ["Esc", "Start"],
	"hotbar_next": ["X", "RB"],
	"hotbar_prev": ["Z", "LB"],
}

var using_gamepad := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for action in KEYS:
		_ensure(action)
		for key in KEYS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
	for action in MOUSE:
		_ensure(action)
		for button in MOUSE[action]:
			var ev := InputEventMouseButton.new()
			ev.button_index = button
			InputMap.action_add_event(action, ev)
	for action in PAD_BUTTONS:
		_ensure(action)
		for button in PAD_BUTTONS[action]:
			var ev := InputEventJoypadButton.new()
			ev.button_index = button
			InputMap.action_add_event(action, ev)
	for action in PAD_AXES:
		_ensure(action)
		var ev := InputEventJoypadMotion.new()
		ev.axis = PAD_AXES[action][0]
		ev.axis_value = PAD_AXES[action][1]
		InputMap.action_add_event(action, ev)
	InputMap.action_set_deadzone("use_tool", 0.4)
	InputMap.action_set_deadzone("sprint", 0.4)
	for action in ["move_left", "move_right", "move_forward", "move_back"]:
		InputMap.action_set_deadzone(action, 0.2)


func _input(event: InputEvent) -> void:
	var pad := event is InputEventJoypadButton or (event is InputEventJoypadMotion and absf(event.axis_value) > 0.3)
	var kbm := event is InputEventKey or event is InputEventMouseButton
	if pad and not using_gamepad:
		using_gamepad = true
		device_changed.emit(true)
	elif kbm and using_gamepad:
		using_gamepad = false
		device_changed.emit(false)


## The key or button name to show for an action in prompts.
func glyph(action: String) -> String:
	var g: Array = GLYPHS.get(action, [action, action])
	return g[1] if using_gamepad else g[0]


func _ensure(action: StringName) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
