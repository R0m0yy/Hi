extends SceneTree
## Renders the player character for review: a turnaround at rest, a face
## close-up, and one frame of each listed animation.
##   godot --path game --script res://tools/character_sheet.gd -- --model=res://assets/models/characters/explorer.glb --out=/abs/prefix

const CLIPS := ["idle", "walk", "run", "sprint", "jump", "swim", "dive", "gather", "chop", "spear_thrust",
		"fish_cast", "fish_reel", "cook", "row", "eat", "hurt"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var model_path := "res://assets/models/characters/explorer.glb"
	var out := "/tmp/character"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--model="):
			model_path = a.substr(8)
		elif a.begins_with("--out="):
			out = a.substr(6)
	var scene: PackedScene = load(model_path)
	var env := WorldEnvironment.new()
	env.environment = load("res://materials/daylight_environment.tres").duplicate()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("f3e6c4")
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color("ffe7c2")
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	sun.rotation_degrees = Vector3(-42, 35, 0)
	root.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.light_color = Color("b8b0eb")
	fill.light_energy = 0.45
	fill.rotation_degrees = Vector3(-20, -140, 0)
	root.add_child(fill)
	var floor_mesh := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(60, 60)
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color("ead6a8")
	pm.material = fm
	floor_mesh.mesh = pm
	root.add_child(floor_mesh)
	var cam := Camera3D.new()
	cam.fov = 24.0
	root.add_child(cam)
	# Turnaround at rest.
	var yaws := [0.0, 35.0, 90.0, 180.0]
	var models := []
	for i in yaws.size():
		var m: Node3D = scene.instantiate()
		MaterialLibrary.apply(m)
		root.add_child(m)
		m.position = Vector3(i * 1.05 - 1.575, 0, 0)
		m.rotation_degrees.y = yaws[i]
		models.append(m)
	cam.position = Vector3(0, 0.95, 6.6)
	cam.look_at(Vector3(0, 0.72, 0))
	await _save(out + "_turnaround.png")
	# Face close-up.
	for m in models:
		m.visible = false
	var face: Node3D = models[1]
	face.visible = true
	face.position = Vector3.ZERO
	face.rotation_degrees.y = 18.0
	cam.fov = 18.0
	cam.position = Vector3(0.0, 1.32, 1.35)
	cam.look_at(Vector3(0, 1.22, 0))
	await _save(out + "_face.png")
	face.visible = false
	# Animation lineup.
	cam.fov = 24.0
	var cols := 8
	var poses := []
	for i in CLIPS.size():
		var m: Node3D = scene.instantiate()
		MaterialLibrary.apply(m)
		root.add_child(m)
		m.position = Vector3((i % cols) * 1.15 - 4.0, 0, -(i / cols) * 2.2)
		m.rotation_degrees.y = 25.0
		var ap: AnimationPlayer = m.find_children("*", "AnimationPlayer", true, false)[0]
		if ap.has_animation(CLIPS[i]):
			ap.play(CLIPS[i])
			ap.seek(ap.get_animation(CLIPS[i]).length * 0.4, true)
			ap.pause()
		var l := Label3D.new()
		l.text = CLIPS[i]
		l.font_size = 48
		l.pixel_size = 0.003
		l.modulate = Color("3a2a20")
		l.position = m.position + Vector3(0, 0.02, 0.45)
		l.rotation_degrees.x = -30
		root.add_child(l)
	cam.position = Vector3(0, 4.6, 7.2)
	cam.look_at(Vector3(0, 0.3, -1.1))
	cam.fov = 38.0
	await _save(out + "_anims.png")
	quit()


func _save(path: String) -> void:
	for i in 6:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
