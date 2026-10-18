class_name MainMenu
extends MenuBase
## Title screen over the live island: continue, new game, controls,
## settings, quit.

var _continue: Button
var _pages := {}
var _main: VBoxContainer


func _ready() -> void:
	super._ready()
	layer = 12
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.theme = UITheme.get_theme()
	add_child(root)
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = """
shader_type canvas_item;
void fragment() {
	float l = smoothstep(0.75, 0.0, UV.x);
	COLOR = vec4(0.02, 0.07, 0.11, 0.78 * l);
}"""
	var mat := ShaderMaterial.new()
	mat.shader = sh
	shade.material = mat
	root.add_child(shade)
	var col := VBoxContainer.new()
	col.position = Vector2(120, 170)
	col.custom_minimum_size = Vector2(620, 0)
	col.add_theme_constant_override("separation", 14)
	root.add_child(col)
	var title := UITheme.label("PARADISE", 112, UITheme.INK, true)
	title.add_theme_constant_override("line_spacing", -30)
	col.add_child(title)
	var title2 := UITheme.label("UNTAMED", 112, UITheme.ACCENT, true)
	col.add_child(title2)
	col.add_child(UITheme.label("A castaway's tropical survival adventure", 26, UITheme.INK_DIM))
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 30)
	col.add_child(spacer)
	_main = VBoxContainer.new()
	_main.add_theme_constant_override("separation", 12)
	_main.custom_minimum_size = Vector2(420, 0)
	_continue = MenuBase.button("Continue", _on_continue)
	_main.add_child(_continue)
	_main.add_child(MenuBase.button("New game", _on_new))
	_main.add_child(MenuBase.button("Controls", func() -> void: _show("controls")))
	_main.add_child(MenuBase.button("Settings", func() -> void: _show("settings")))
	# A browser tab cannot be closed by the page, so the web build has no Quit.
	if not OS.has_feature("web"):
		_main.add_child(MenuBase.button("Quit", func() -> void: get_tree().quit()))
	col.add_child(_main)
	var controls_page := PanelContainer.new()
	var csb := UITheme.panel_box(20)
	controls_page.add_theme_stylebox_override("panel", csb)
	var cbox := VBoxContainer.new()
	cbox.add_child(ControlsPanel.new())
	cbox.add_child(MenuBase.button("Back", func() -> void: _show("")))
	controls_page.add_child(cbox)
	col.add_child(controls_page)
	_pages["controls"] = controls_page
	var settings_page := PanelContainer.new()
	settings_page.add_theme_stylebox_override("panel", UITheme.panel_box(20))
	var settings := SettingsPanel.new()
	settings.back_pressed.connect(func() -> void: _show(""))
	settings_page.add_child(settings)
	col.add_child(settings_page)
	_pages["settings"] = settings_page
	var credit := UITheme.label("Godot 4 · original art · v0.3", 16, UITheme.INK_DIM)
	credit.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	credit.offset_left = 120
	credit.offset_top = -50
	root.add_child(credit)
	_show("")


func _show(page: String) -> void:
	_main.visible = page == ""
	for k in _pages:
		_pages[k].visible = k == page
	if page == "":
		_continue.disabled = not SaveManager.has_save()
		var first := _main.get_child(0 if not _continue.disabled else 1) as Button
		first.grab_focus.call_deferred()


func _on_open() -> void:
	_show("")


func _on_continue() -> void:
	close()
	SaveManager.load_and_restart()


func _on_new() -> void:
	close()
	Game.reset()
	Game.pending_start = "new"
	get_tree().reload_current_scene()
