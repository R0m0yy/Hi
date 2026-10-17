class_name MenuBase
extends CanvasLayer
## Shared modal-menu plumbing: a dimmed full-screen backdrop, a centred
## panel, open/close that flags Game.ui_open so the player stops reading
## input, and focus for gamepad navigation.

signal closed

var backdrop: ColorRect
var panel: PanelContainer
var is_open := false


func _init() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false


func _build_frame(min_size: Vector2, dim: float = 0.55) -> VBoxContainer:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.theme = UITheme.get_theme()
	add_child(root)
	backdrop = ColorRect.new()
	backdrop.color = Color(0.01, 0.04, 0.07, dim)
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(backdrop)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(center)
	panel = PanelContainer.new()
	panel.custom_minimum_size = min_size
	var sb := UITheme.panel_box(24)
	sb.set_content_margin_all(28)
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	panel.add_child(col)
	return col


func open() -> void:
	is_open = true
	visible = true
	Game.ui_open = true
	_on_open()
	AudioManager.play("ui_open")


func close() -> void:
	if not is_open:
		return
	is_open = false
	visible = false
	Game.ui_open = _other_menu_open()
	closed.emit()
	AudioManager.play("ui_close")


func _other_menu_open() -> bool:
	for m in get_tree().get_nodes_in_group("menus"):
		if m != self and m.is_open:
			return true
	return false


func _on_open() -> void:
	pass


func _ready() -> void:
	add_to_group("menus")


static func header(text: String, sub: String = "") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	box.add_child(UITheme.label(text, 40, UITheme.INK, true))
	if sub != "":
		box.add_child(UITheme.label(sub, 19, UITheme.INK_DIM))
	return box


static func button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.pressed.connect(cb)
	b.pressed.connect(func() -> void: AudioManager.play("ui_click"))
	return b
