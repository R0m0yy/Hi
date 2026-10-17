extends Node
## Automated capture of genuine in-engine screenshots for visual review.
##
## Usage (arguments after "--" are user args):
##   godot --path game [res://scene.tscn] -- --capture=/abs/out.png [--frames=40]
##        [--view=x,y,z,size,yaw,pitch[,fov]]   (fov 0 = orthographic)
##   godot --path game -- --shots=/abs/shots.json
## shots.json: [{"file": "/abs/a.png", "view": [x, y, z, size, yaw, pitch, fov?], "frames": 40}, ...]
## The view is applied to the first node in group "camera_rig" (IsometricCamera).
## Optional "player": [x, z, facing_deg, "anim", anim_time_0_to_1, y?] poses the
## player for the shot (physics paused so the pose holds).

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
	if _frame == 2 and shot.has("player"):
		_pose_player(shot["player"])
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
	var fov: float = view[6] if view.size() > 6 else -1.0
	rig.set_view(Vector3(view[0], view[1], view[2]), view[3], view[4], view[5], fov)


func _pose_player(p: Array) -> void:
	var player := get_tree().get_first_node_in_group("player") as Node3D
	var island := get_tree().get_first_node_in_group("island")
	if player == null:
		return
	player.set_physics_process(false)
	var y: float = p[5] if p.size() > 5 else (island.height_at(p[0], p[1]) if island else 0.0)
	player.global_position = Vector3(p[0], y, p[1])
	var model := player.get_node("Model") as Node3D
	model.rotation.y = deg_to_rad(p[2])
	var ap := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	ap.play(p[3])
	ap.seek(float(p[4]) * ap.get_animation(p[3]).length, true)
	ap.pause()


static func _parse_args(raw: PackedStringArray) -> Dictionary:
	var out := {}
	for a in raw:
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			out[kv[0]] = kv[1]
	return out
