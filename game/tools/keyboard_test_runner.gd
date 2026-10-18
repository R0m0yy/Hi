extends Node
## See keyboard_test.gd.

var failures := 0
var world: GameWorld


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	Game.reset()
	Game.pending_start = "new"
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await get_tree().create_timer(1.0).timeout
	world = get_tree().current_scene
	var inv := world.inventory_menu
	var pause := world.pause_menu

	await _key(KEY_TAB)
	_check(inv.is_open, "Tab opens the pack")
	await _key(KEY_TAB)
	_check(not inv.is_open, "Tab closes the pack again (with a slot focused)")

	await _key(KEY_TAB)
	await _key(KEY_ESCAPE)
	_check(not inv.is_open, "Escape closes the pack")
	_check(not pause.is_open, "that Escape does not also open the pause menu")

	await _key(KEY_I)
	_check(inv.is_open, "I opens the pack")
	await _key(KEY_I)
	_check(not inv.is_open, "I closes the pack")

	await _key(KEY_ESCAPE)
	_check(pause.is_open, "Escape opens the pause menu")
	await _key(KEY_ESCAPE)
	_check(not pause.is_open, "Escape closes the pause menu")
	_check(Game.is_playing() and not Game.ui_open, "back in play with no menu open")

	print("keyboard_test: %s (%d failure(s))" % ["PASS" if failures == 0 else "FAIL", failures])
	get_tree().quit(1 if failures else 0)


func _key(code: Key) -> void:
	for pressed in [true, false]:
		var ev := InputEventKey.new()
		ev.keycode = code
		ev.physical_keycode = code
		ev.pressed = pressed
		Input.parse_input_event(ev)
		await get_tree().process_frame
		await get_tree().process_frame


func _check(ok: bool, what: String) -> void:
	print("  [%s] %s" % ["ok" if ok else "FAIL", what])
	if not ok:
		failures += 1
