extends Node
## Automated capture of genuine in-engine screenshots for visual review.
##
## Usage (arguments after "--" are user args):
##   godot --path game [res://scene.tscn] -- --capture=/abs/out.png [--frames=40]
##        [--view=x,y,z,size,yaw,pitch]
##   godot --path game -- --shots=/abs/shots.json
## shots.json: [{"file": "/abs/a.png", "view": [x, y, z, size, yaw, pitch], "frames": 40}, ...]
## The view is applied to the first node in group "camera_rig" (IsometricCamera).

var _shots: Array = []
var _index := 0
var _frame := 0
var _busy := false


func _ready() -> void:
	var args := _parse_args(OS.get_cmdline_user_args())
	if args.has("shots"):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(args["shots"]))
		if parsed is Array:
			_shots = parsed
	elif args.has("capture"):
		var shot := {"file": args["capture"], "frames": int(args.get("frames", "40"))}
		if args.has("view"):
			shot["view"] = Array(args["view"].split_floats(","))
		_shots = [shot]
	if _shots.is_empty():
		set_process(false)
		return
	process_mode = Node.PROCESS_MODE_ALWAYS
	print("[capture] %d shot(s) queued" % _shots.size())


func _process(_delta: float) -> void:
	if _busy or _index >= _shots.size():
		return
	var shot: Dictionary = _shots[_index]
	_frame += 1
	if _frame == 2 and shot.has("view"):
		_apply_view(shot["view"])
	if _frame >= int(shot.get("frames", 40)):
		_busy = true
		_capture(shot)


func _capture(shot: Dictionary) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path: String = shot["file"]
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var err := img.save_png(path)
	print("[capture] saved %s (%dx%d) err=%d" % [path, img.get_width(), img.get_height(), err])
	_index += 1
	_frame = 0
	_busy = false
	if _index >= _shots.size():
		get_tree().quit()


func _apply_view(view: Array) -> void:
	var rig := get_tree().get_first_node_in_group("camera_rig")
	if rig == null or view.size() < 6:
		push_warning("[capture] no camera_rig found or bad view")
		return
	rig.set_view(Vector3(view[0], view[1], view[2]), view[3], view[4], view[5])


static func _parse_args(raw: PackedStringArray) -> Dictionary:
	var out := {}
	for a in raw:
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			out[kv[0]] = kv[1]
	return out
