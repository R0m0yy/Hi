class_name SettingsPanel
extends VBoxContainer
## Volume sliders and display options, saved to user://settings.cfg.

signal back_pressed


func _init() -> void:
	add_theme_constant_override("separation", 12)
	add_child(UITheme.label("Settings", 28, UITheme.INK, true))
	for key in ["music", "sfx", "ambience"]:
		var row := HBoxContainer.new()
		var l := UITheme.label({"music": "Music", "sfx": "Sound effects", "ambience": "Ocean and wind"}[key], 20)
		l.custom_minimum_size = Vector2(260, 0)
		row.add_child(l)
		var s := HSlider.new()
		s.min_value = 0.0
		s.max_value = 1.0
		s.step = 0.05
		s.custom_minimum_size = Vector2(360, 30)
		s.value = SaveManager.settings.get(key, 0.8)
		s.value_changed.connect(func(v: float) -> void:
			SaveManager.settings[key] = v
			SaveManager.apply_settings())
		row.add_child(s)
		add_child(row)
	var fs := CheckButton.new()
	fs.text = "Fullscreen"
	fs.button_pressed = SaveManager.settings.get("fullscreen", false)
	fs.toggled.connect(func(on: bool) -> void:
		SaveManager.settings["fullscreen"] = on
		SaveManager.apply_settings())
	add_child(fs)
	var hints := CheckButton.new()
	hints.text = "Show objectives"
	hints.button_pressed = SaveManager.settings.get("objectives", true)
	hints.toggled.connect(func(on: bool) -> void:
		SaveManager.settings["objectives"] = on
		SaveManager.apply_settings())
	add_child(hints)
	add_child(MenuBase.button("Back", func() -> void:
		SaveManager.save_settings()
		back_pressed.emit()))
