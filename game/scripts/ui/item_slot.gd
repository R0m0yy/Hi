class_name ItemSlot
extends Button
## One inventory square: icon, stack count, tool durability bar. Used by the
## hotbar, the pack and storage panels.

signal slot_pressed(slot: ItemSlot)

var index := -1
var inventory: Inventory
var highlight := false:
	set(v):
		highlight = v
		queue_redraw()
var hotkey := ""

var _icon_rect: TextureRect
var _count: Label
var _key: Label


func _init(size_px: int = 84) -> void:
	custom_minimum_size = Vector2(size_px, size_px)
	focus_mode = Control.FOCUS_ALL
	toggle_mode = false
	_icon_rect = TextureRect.new()
	_icon_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_icon_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_icon_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_icon_rect.offset_left = 8
	_icon_rect.offset_top = 8
	_icon_rect.offset_right = -8
	_icon_rect.offset_bottom = -8
	_icon_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_icon_rect)
	_count = UITheme.label("", 20)
	_count.add_theme_font_override("font", load("res://assets/fonts/Nunito-ExtraBold.woff2"))
	_count.add_theme_constant_override("outline_size", 6)
	_count.add_theme_color_override("font_outline_color", Color(0.03, 0.09, 0.13))
	_count.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	_count.offset_left = -44
	_count.offset_top = -30
	_count.offset_right = -8
	_count.offset_bottom = -4
	_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_count.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_count)
	_key = UITheme.label("", 15, UITheme.INK_DIM)
	_key.position = Vector2(8, 3)
	_key.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_key)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.11, 0.16, 0.78)
	sb.border_color = Color(1, 1, 1, 0.12)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(14)
	add_theme_stylebox_override("normal", sb)
	var hover := sb.duplicate()
	hover.border_color = UITheme.SAND
	add_theme_stylebox_override("hover", hover)
	add_theme_stylebox_override("pressed", hover)
	add_theme_stylebox_override("focus", UITheme.focus_box())
	pressed.connect(func() -> void: slot_pressed.emit(self))


func bind(inv: Inventory, i: int, key_label: String = "") -> void:
	inventory = inv
	index = i
	hotkey = key_label
	refresh()


func refresh() -> void:
	var s = inventory.get_slot(index) if inventory else null
	_key.text = hotkey
	if s == null:
		_icon_rect.texture = null
		_count.text = ""
		tooltip_text = ""
	else:
		_icon_rect.texture = ItemDB.icon(s["id"])
		_count.text = str(s["count"]) if int(s["count"]) > 1 else ""
		var def := ItemDB.item(s["id"])
		tooltip_text = "%s\n%s" % [def.get("name", s["id"]), def.get("desc", "")]
	queue_redraw()


func _draw() -> void:
	var s = inventory.get_slot(index) if inventory else null
	if highlight:
		var r := Rect2(Vector2.ZERO, size).grow(-1)
		draw_rect(r, Color(UITheme.ACCENT, 0.18), true)
		var sb := StyleBoxFlat.new()
		sb.draw_center = false
		sb.border_color = UITheme.ACCENT
		sb.set_border_width_all(3)
		sb.set_corner_radius_all(14)
		draw_style_box(sb, Rect2(Vector2.ZERO, size))
	if s != null and s.has("dur"):
		var frac := clampf(float(s["dur"]) / maxf(ItemDB.max_durability(s["id"]), 1.0), 0.0, 1.0)
		var w := size.x - 20.0
		draw_rect(Rect2(10, size.y - 10, w, 4), Color(0, 0, 0, 0.45))
		var c := UITheme.GOOD if frac > 0.4 else (UITheme.SAND if frac > 0.2 else UITheme.CORAL)
		draw_rect(Rect2(10, size.y - 10, w * frac, 4), c)
