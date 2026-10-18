extends SceneTree
## Real key events (not input actions) through the whole input pipeline, so
## the GUI gets its say first, as with a physical keyboard. The other tests
## send actions, which skip focus navigation.
##   godot --headless --path game --script res://tools/keyboard_test.gd


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	var script := load("res://tools/keyboard_test_runner.gd") as GDScript
	if script == null or not script.can_instantiate():
		push_error("keyboard_test: keyboard_test_runner.gd failed to compile")
		print("keyboard_test: FAIL (runner did not compile)")
		quit(1)
		return
	root.add_child(script.new())
