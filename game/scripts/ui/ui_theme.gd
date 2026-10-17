class_name UITheme
extends RefCounted
## The game's UI look: deep-ocean glass panels with a warm sand edge, cream
## text, lagoon-turquoise accents (art bible palette). Built in code so
## every screen shares one Theme.

const INK := Color("fff8e3")
const INK_DIM := Color(1.0, 0.973, 0.89, 0.66)
const PANEL := Color(0.055, 0.14, 0.2, 0.86)
const PANEL_LIGHT := Color(0.09, 0.21, 0.29, 0.9)
const EDGE := Color(0.914, 0.769, 0.541, 0.55)
const ACCENT := Color("4fd6d0")
const SAND := Color("e9c48a")
const CORAL := Color("e8675a")
const GOOD := Color("8fd694")
const STAT_COLORS := {
	"health": Color("e8675a"), "hunger": Color("f2a33a"), "thirst": Color("4fb7e8"),
	"stamina": Color("cfe06a"), "oxygen": Color("a6f0ff"),
}

static var _theme: Theme
static var display_font: Font
static var body_font: Font
static var body_bold: Font


static func get_theme() -> Theme:
	if _theme:
		return _theme
	display_font = load("res://assets/fonts/Fredoka-SemiBold.woff2")
	body_font = load("res://assets/fonts/Nunito-Bold.woff2")
	body_bold = load("res://assets/fonts/Nunito-ExtraBold.woff2")
	var t := Theme.new()
	t.default_font = body_font
	t.default_font_size = 22
	t.set_color("font_color", "Label", INK)
	t.set_color("font_outline_color", "Label", Color(0.02, 0.07, 0.1, 0.7))
	t.set_constant("outline_size", "Label", 0)
	t.set_stylebox("panel", "PanelContainer", panel_box())
	t.set_stylebox("panel", "Panel", panel_box())
	# Buttons
	t.set_stylebox("normal", "Button", button_box(PANEL_LIGHT, EDGE))
	t.set_stylebox("hover", "Button", button_box(Color(0.13, 0.3, 0.38, 0.95), SAND))
	t.set_stylebox("pressed", "Button", button_box(Color(0.2, 0.45, 0.5, 0.95), ACCENT))
	t.set_stylebox("focus", "Button", focus_box())
	t.set_stylebox("disabled", "Button", button_box(Color(0.06, 0.12, 0.16, 0.7), Color(1, 1, 1, 0.12)))
	t.set_color("font_color", "Button", INK)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_color("font_focus_color", "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", Color(1, 1, 1, 0.35))
	t.set_font("font", "Button", display_font)
	t.set_font_size("font_size", "Button", 24)
	# Sliders, check boxes
	t.set_stylebox("slider", "HSlider", _flat(Color(1, 1, 1, 0.15), 6))
	t.set_stylebox("grabber_area", "HSlider", _flat(ACCENT, 6))
	t.set_stylebox("grabber_area_highlight", "HSlider", _flat(ACCENT.lightened(0.2), 6))
	t.set_color("font_color", "CheckButton", INK)
	t.set_font("font", "CheckButton", body_font)
	# Scroll
	t.set_stylebox("panel", "ScrollContainer", StyleBoxEmpty.new())
	t.set_stylebox("scroll", "VScrollBar", _flat(Color(1, 1, 1, 0.06), 6))
	t.set_stylebox("grabber", "VScrollBar", _flat(Color(1, 1, 1, 0.3), 6))
	t.set_stylebox("grabber_highlight", "VScrollBar", _flat(Color(1, 1, 1, 0.45), 6))
	t.set_stylebox("grabber_pressed", "VScrollBar", _flat(ACCENT, 6))
	# Tooltips
	t.set_stylebox("panel", "TooltipPanel", panel_box(10))
	t.set_color("font_color", "TooltipLabel", INK)
	_theme = t
	return t


static func panel_box(radius: int = 18) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = PANEL
	sb.border_color = EDGE
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(18)
	sb.shadow_color = Color(0, 0, 0, 0.25)
	sb.shadow_size = 10
	sb.shadow_offset = Vector2(0, 4)
	sb.anti_aliasing = true
	return sb


static func button_box(bg: Color, border: Color) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(14)
	sb.content_margin_left = 22
	sb.content_margin_right = 22
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	return sb


static func focus_box() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.draw_center = false
	sb.border_color = ACCENT
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(16)
	sb.expand_margin_left = 3
	sb.expand_margin_right = 3
	sb.expand_margin_top = 3
	sb.expand_margin_bottom = 3
	return sb


static func _flat(c: Color, radius: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = c
	sb.set_corner_radius_all(radius)
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	return sb


static func label(text: String, size: int = 22, color: Color = INK, display := false) -> Label:
	get_theme()
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if display:
		l.add_theme_font_override("font", display_font)
	return l


## A rounded key-cap label for prompts ("E", "LMB", "RT").
static func keycap(text: String, size: int = 20) -> PanelContainer:
	get_theme()
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = INK
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 2
	sb.content_margin_bottom = 2
	p.add_theme_stylebox_override("panel", sb)
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", body_bold)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color("10232f"))
	p.add_child(l)
	return p
