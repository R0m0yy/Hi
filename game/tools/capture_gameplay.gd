extends SceneTree
## Drives the real game into a series of gameplay situations and saves a
## screenshot of each (needs a renderer):
##   godot --path game --script res://tools/capture_gameplay.gd -- --out=/abs/dir [--only=name,name]


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	root.add_child(load("res://tools/capture_gameplay_runner.gd").new())
