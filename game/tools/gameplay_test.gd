extends SceneTree
## End-to-end gameplay test on the real main scene with simulated input.
## The test logic lives in gameplay_test_runner.gd, loaded after the
## autoloads exist so it can use them by name.
##   godot --headless --path game --script res://tools/gameplay_test.gd


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	var script := load("res://tools/gameplay_test_runner.gd") as GDScript
	if script == null or not script.can_instantiate():
		push_error("gameplay_test: gameplay_test_runner.gd failed to compile")
		print("gameplay_test: FAIL (runner did not compile)")
		quit(1)
		return
	root.add_child(script.new())
