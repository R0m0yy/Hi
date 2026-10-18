extends SceneTree
## Prints renderer statistics (draw calls, primitives, objects, video memory)
## at a few representative views. These numbers do not depend on the GPU, so
## they are meaningful even on a software renderer:
##   godot --path game --audio-driver Dummy --resolution 1920x1080 --script res://tools/perf_probe.gd


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	var script := load("res://tools/perf_probe_runner.gd") as GDScript
	if script == null or not script.can_instantiate():
		push_error("perf_probe: perf_probe_runner.gd failed to compile")
		quit(1)
		return
	root.add_child(script.new())
