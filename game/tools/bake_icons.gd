extends SceneTree
## Renders every item's 3D model into a 256 px transparent PNG icon in
## res://assets/icons/ (needs a renderer, not --headless):
##   godot --path game --script res://tools/bake_icons.gd

const SIZE := 256
const OUT := "res://assets/icons/"
const STRUCTURE_MODELS := {
	"campfire_kit": "res://assets/models/props/campfire.glb",
	"storage_kit": "res://assets/models/props/chest.glb",
	"shelter_kit": "res://assets/models/props/leanto_shelter.glb",
	"raft_kit": "res://assets/models/props/raft.glb",
}
## Per-item view tweaks: [yaw deg, pitch deg, zoom]
const VIEWS := {
	"spear": [35.0, -35.0, 0.95],
	"fishing_rod": [35.0, -35.0, 0.95],
	"hatchet": [55.0, -25.0, 1.0],
	"rope": [20.0, -55.0, 1.0],
	"shell": [10.0, -55.0, 1.0],
}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var items: Dictionary = root.get_node("ItemDB").ITEMS
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var vp := SubViewport.new()
	vp.size = Vector2i(SIZE, SIZE)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c9c0f0")
	env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	vp.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color("ffe7c2")
	sun.light_energy = 1.6
	sun.rotation_degrees = Vector3(-50, 35, 0)
	vp.add_child(sun)
	var rim := DirectionalLight3D.new()
	rim.light_color = Color("bfe9ff")
	rim.light_energy = 0.6
	rim.rotation_degrees = Vector3(-20, 200, 0)
	vp.add_child(rim)
	var cam := Camera3D.new()
	cam.fov = 26.0
	vp.add_child(cam)
	var made := 0
	for id in items:
		var path: String = STRUCTURE_MODELS.get(id, "res://assets/models/items/%s.glb" % id)
		if not ResourceLoader.exists(path):
			print("  no model for ", id)
			continue
		var node: Node3D = (load(path) as PackedScene).instantiate()
		vp.add_child(node)
		node.position = Vector3(0, 60, 0)
		MaterialLibrary.apply(node)
		var aabb := _aabb(node)
		var view: Array = VIEWS.get(id, [30.0, -32.0, 1.0])
		var radius := aabb.size.length() * 0.5
		var dist := radius / sin(deg_to_rad(cam.fov * 0.5)) * 1.02 / float(view[2])
		var basis := Basis.from_euler(Vector3(deg_to_rad(view[1]), deg_to_rad(view[0]), 0.0))
		cam.global_position = aabb.get_center() + basis.z * dist
		cam.look_at(aabb.get_center(), Vector3.UP)
		cam.near = dist * 0.05
		cam.far = dist * 4.0
		for i in 4:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		img.save_png(ProjectSettings.globalize_path(OUT + id + ".png"))
		made += 1
		node.queue_free()
		await process_frame
	print("bake_icons: %d icons -> %s" % [made, OUT])
	quit()


static func _aabb(node: Node3D) -> AABB:
	var out := AABB()
	var first := true
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var box: AABB = mi.global_transform * mi.get_aabb()
		out = box if first else out.merge(box)
		first = false
	return out
