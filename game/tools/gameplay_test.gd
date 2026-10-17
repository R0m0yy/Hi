extends SceneTree
## End-to-end gameplay test on the real main scene with simulated input.
## The test logic lives in gameplay_test_runner.gd, loaded after the
## autoloads exist so it can use them by name.
##   godot --headless --path game --script res://tools/gameplay_test.gd


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	root.add_child(load("res://tools/gameplay_test_runner.gd").new())
