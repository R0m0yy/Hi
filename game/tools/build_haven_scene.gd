extends SceneTree
## Generates the island scenes (res://scenes/world/<scene>.tscn) from the
## layout JSONs exported by the Blender pipeline. Run headless after
## building assets:
##   godot --headless --path game --script res://tools/build_haven_scene.gd

const ISLANDS := [
	{"id": "haven", "name": "Haven Island", "node": "HavenIsland", "scene": "haven_island", "radius": 60.0},
	{"id": "palm_key", "name": "Palm Key", "node": "PalmKey", "scene": "palm_key", "radius": 45.0},
	{"id": "lookout", "name": "Lookout Isle", "node": "LookoutIsle", "scene": "lookout_isle", "radius": 50.0},
]


func _init() -> void:
	var failures := 0
	for spec in ISLANDS:
		if not _build(spec):
			failures += 1
	quit(1 if failures else 0)


func _build(spec: Dictionary) -> bool:
	var layout_path := "res://assets/terrain/%s_layout.json" % spec["id"]
	var terrain_path := "res://assets/models/terrain/%s_terrain.glb" % spec["id"]
	var out := "res://scenes/world/%s.tscn" % spec["scene"]
	var layout = JSON.parse_string(FileAccess.get_file_as_string(layout_path))
	if not (layout is Dictionary):
		push_error("cannot parse %s" % layout_path)
		return false
	var root := Node3D.new()
	root.name = spec["node"]
	root.set_script(load("res://scripts/world/island_manager.gd"))
	root.set("island_name", spec["name"])
	root.set("island_id", spec["id"])
	root.set("discover_radius", spec["radius"])
	root.set("heightmap_json", "res://assets/terrain/%s_heightmap.json" % spec["id"])

	var terrain: Node3D = load(terrain_path).instantiate()
	terrain.name = "Terrain"
	_attach(root, root, terrain)

	var groups := {}
	var missing := {}
	var placed := 0
	for item in layout["items"]:
		var path: String = item["scene"]
		if not ResourceLoader.exists(path):
			missing[path] = true
			continue
		var inst: Node3D = load(path).instantiate()
		inst.name = item["name"]
		inst.position = Vector3(item["pos"][0], item["pos"][1], item["pos"][2])
		inst.rotation_degrees = Vector3(item["rot"][0], item["rot"][1], item["rot"][2])
		inst.scale = Vector3.ONE * float(item["scale"])
		_attach(_group(root, groups, item["group"]), root, inst)
		if item.has("collider"):
			_add_collider(inst, item["collider"], root)
		placed += 1

	var scatter_count := 0
	for key in layout["scatter"]:
		var s: Dictionary = layout["scatter"][key]
		if not ResourceLoader.exists(s["scene"]):
			missing[s["scene"]] = true
			continue
		var field := ScatterField.new()
		field.name = String(key).to_pascal_case()
		field.source_scene = load(s["scene"])
		field.layout_json = layout_path
		field.layout_key = key
		field.cast_shadows = s.get("shadows", true)
		_attach(_group(root, groups, s["group"]), root, field)
		scatter_count += 1

	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err == OK:
		err = ResourceSaver.save(packed, out)
	print("build_island_scene: %s placed %d items, %d scatter fields -> %s (err=%d)" % [spec["id"], placed, scatter_count, out, err])
	for m in missing:
		print("  missing asset (skipped): ", m)
	root.free()
	return err == OK


func _attach(parent: Node, root: Node, node: Node) -> void:
	parent.add_child(node)
	node.owner = root


func _group(root: Node, groups: Dictionary, group_name: String) -> Node3D:
	if not groups.has(group_name):
		var g := Node3D.new()
		g.name = group_name
		_attach(root, root, g)
		groups[group_name] = g
	return groups[group_name]


func _add_collider(inst: Node3D, spec: Dictionary, root: Node) -> void:
	var body := StaticBody3D.new()
	body.name = "Collider"
	var cs := CollisionShape3D.new()
	cs.name = "Shape"
	match spec.get("type", "box"):
		"cylinder":
			var cyl := CylinderShape3D.new()
			cyl.radius = spec.get("radius", 0.5)
			cyl.height = spec.get("height", 1.0)
			cs.shape = cyl
		_:
			var box := BoxShape3D.new()
			var sz: Array = spec.get("size", [1, 1, 1])
			box.size = Vector3(sz[0], sz[1], sz[2])
			cs.shape = box
	cs.position.y = spec.get("y", 0.0)
	_attach(inst, root, body)
	_attach(body, root, cs)
