extends SceneTree
## Drives the real game into a series of gameplay situations and saves a
## screenshot of each (needs a renderer):
##   godot --path game --script res://tools/capture_gameplay.gd -- --out=/abs/dir [--only=name,name]


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	var script := load("res://tools/capture_gameplay_runner.gd") as GDScript
	if script == null or not script.can_instantiate():
		push_error("capture_gameplay: capture_gameplay_runner.gd failed to compile")
		print("capture_gameplay: FAIL (runner did not compile)")
		quit(1)
		return
	root.add_child(script.new())
