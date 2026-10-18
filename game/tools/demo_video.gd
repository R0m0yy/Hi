extends SceneTree
## Plays a scripted run through the real game for a gameplay video. Record it
## with Godot's Movie Maker mode (every frame is rendered, so a slow machine
## still gives a smooth 30 fps video):
##   godot --path game --write-movie /abs/demo.avi --fixed-fps 30 \
##       --resolution 1280x720 --script res://tools/demo_video.gd
## The steps live in demo_video_runner.gd, loaded once the autoloads exist.


func _initialize() -> void:
	_start.call_deferred()


func _start() -> void:
	var script := load("res://tools/demo_video_runner.gd") as GDScript
	if script == null or not script.can_instantiate():
		push_error("demo_video: demo_video_runner.gd failed to compile")
		quit(1)
		return
	root.add_child(script.new())
