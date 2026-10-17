class_name PauseMenu
extends MenuBase
## Pause: resume, save, load, controls, settings, back to the title, quit.
## Pausing stops the world (SceneTree.paused).

var _pages := {}
var _main_buttons: VBoxContainer
var _status: Label


func _ready() -> void:
	super._ready()
	var col := _build_frame(Vector2(980, 0), 0.6)
	col.add_child(MenuBase.header("Paused"))
	_main_buttons = VBoxContainer.new()
	_main_buttons.add_theme_constant_override("separation", 10)
	_main_buttons.add_child(MenuBase.button("Resume", close))
	_main_buttons.add_child(MenuBase.button("Save game", _save))
	_main_buttons.add_child(MenuBase.button("Load last save", _load))
	_main_buttons.add_child(MenuBase.button("Controls", func() -> void: _show("controls")))
	_main_buttons.add_child(MenuBase.button("Settings", func() -> void: _show("settings")))
	_main_buttons.add_child(MenuBase.button("Save and return to title", _to_title))
	_main_buttons.add_child(MenuBase.button("Save and quit", _quit))
	col.add_child(_main_buttons)
	_status = UITheme.label("", 19, UITheme.SAND)
	col.add_child(_status)
	var controls := VBoxContainer.new()
	controls.add_child(ControlsPanel.new())
	controls.add_child(MenuBase.button("Back", func() -> void: _show("")))
	col.add_child(controls)
	_pages["controls"] = controls
	var settings := SettingsPanel.new()
	settings.back_pressed.connect(func() -> void: _show(""))
	col.add_child(settings)
	_pages["settings"] = settings
	_show("")


func _show(page: String) -> void:
	_main_buttons.visible = page == ""
	for k in _pages:
		_pages[k].visible = k == page
	if page == "":
		(_main_buttons.get_child(0) as Button).grab_focus.call_deferred()


func _on_open() -> void:
	get_tree().paused = true
	_status.text = ""
	_show("")


func close() -> void:
	super.close()
	get_tree().paused = false


func _unhandled_input(event: InputEvent) -> void:
	if not Game.is_playing() and not is_open:
		return
	if event.is_action_pressed("pause"):
		if is_open:
			close()
		elif not Game.ui_open:
			open()
		get_viewport().set_input_as_handled()


func _save() -> void:
	_status.text = "Game saved." if SaveManager.save_game() else "Could not save."


func _load() -> void:
	if not SaveManager.has_save():
		_status.text = "There is no save yet."
		return
	close()
	SaveManager.load_and_restart()


func _to_title() -> void:
	SaveManager.save_game()
	close()
	Game.set_state("menu")
	Game.pending_start = ""
	get_tree().reload_current_scene()


func _quit() -> void:
	SaveManager.save_game()
	get_tree().quit()
