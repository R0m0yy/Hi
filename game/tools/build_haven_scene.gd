extends SceneTree
## Generates res://scenes/world/haven_island.tscn from the layout JSON
## exported by the Blender pipeline. Run headless after building assets:
##   godot --headless --path game --script res://tools/build_haven_scene.gd

const LAYOUT := "res://assets/terrain/haven_layout.json"
const TERRAIN := "res://assets/models/terrain/haven_terrain.glb"
const OUT := "res://scenes/world/haven_island.tscn"


func _init() -> void:
	var layout = JSON.parse_string(FileAccess.get_file_as_string(LAYOUT))
	if not (layout is Dictionary):
		push_error("cannot parse %s" % LAYOUT)
		quit(1)
		return
	var root := Node3D.new()
	root.name = "HavenIsland"
	root.set_script(load("res://scripts/world/island_manager.gd"))

	var terrain: Node3D = load(TERRAIN).instantiate()
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
		field.layout_json = LAYOUT
		field.layout_key = key
		field.cast_shadows = s.get("shadows", true)
		_attach(_group(root, groups, s["group"]), root, field)
		scatter_count += 1

	var packed := PackedScene.new()
	var err := packed.pack(root)
	if err == OK:
		err = ResourceSaver.save(packed, OUT)
	print("build_haven_scene: placed %d items, %d scatter fields -> %s (err=%d)" % [placed, scatter_count, OUT, err])
	for m in missing:
		print("  missing asset (skipped): ", m)
	root.free()
	quit(0 if err == OK else 1)


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
