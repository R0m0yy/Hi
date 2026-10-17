class_name Structures
extends RefCounted
## Player-built structures: definitions, ghost models for placement, and
## spawning (from the builder or from a save). Each spawned structure is
## named "Structure_<n>" and saves its own state under "structure_<n>".

const DEFS := {
	"campfire": {"model": "res://scenes/props/campfire.tscn", "radius": 0.9, "water": false, "item": "campfire_kit"},
	"storage": {"model": "res://assets/models/props/chest.glb", "radius": 0.7, "water": false, "item": "storage_kit"},
	"shelter": {"model": "res://assets/models/props/leanto_shelter.glb", "radius": 1.9, "water": false, "item": "shelter_kit"},
	"raft": {"model": "res://assets/models/props/raft.glb", "radius": 1.7, "water": true, "item": "raft_kit"},
}


static func spawn(type: String, index: int, pos: Vector3, yaw: float) -> Node3D:
	var def: Dictionary = DEFS.get(type, {})
	if def.is_empty():
		return null
	var parent := _container()
	var visual: Node3D = (load(def["model"]) as PackedScene).instantiate()
	MaterialLibrary.apply(visual)
	var root: Node3D
	var save_id := "structure_%d" % index
	match type:
		"raft":
			var boat := Boat.new()
			boat.title = "raft"
			boat.max_speed = 4.4
			boat.seat = Vector3(0.0, 0.3, 0.0)
			boat.driver_animation = "sit"
			boat.reach = 2.8
			boat.save_id = save_id
			root = boat
			root.add_child(visual)
		_:
			root = Node3D.new()
			root.add_child(visual)
			var gameplay: Interactable
			match type:
				"campfire":
					gameplay = CookingStation.new()
					gameplay.reach = 2.2
				"storage":
					var box := StorageBox.new()
					box.title = "storage chest"
					gameplay = box
					_box_collider(root, Vector3(1.0, 0.8, 0.7), 0.4)
				"shelter":
					gameplay = ShelterBed.new()
					gameplay.reach = 2.4
					gameplay.position = Vector3(0.0, 0.0, 1.3)
					_box_collider(root, Vector3(3.2, 1.8, 2.0), 0.9)
			gameplay.save_id = save_id
			gameplay.name = "Gameplay"
			root.add_child(gameplay)
	root.name = "Structure_%d" % index
	parent.add_child(root)
	root.global_position = pos
	root.global_rotation = Vector3(0.0, yaw, 0.0)
	return root


static func ghost(type: String) -> Node3D:
	var def: Dictionary = DEFS.get(type, {})
	var path: String = def.get("model", "")
	if path.ends_with(".tscn"):
		path = "res://assets/models/props/campfire.glb"
	var node: Node3D = (load(path) as PackedScene).instantiate()
	return node


static func _container() -> Node3D:
	var tree := Engine.get_main_loop() as SceneTree
	var holder := tree.get_first_node_in_group("structures_root") as Node3D
	if holder == null:
		holder = Node3D.new()
		holder.name = "Structures"
		holder.add_to_group("structures_root")
		tree.current_scene.add_child(holder)
	return holder


static func _box_collider(root: Node3D, size: Vector3, y: float) -> void:
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	cs.position.y = y
	body.add_child(cs)
	root.add_child(body)


## Rebuilds every structure recorded in Game.structures (after loading).
static func respawn_all() -> void:
	for i in Game.structures.size():
		var s: Dictionary = Game.structures[i]
		var p: Array = s["pos"]
		spawn(s["type"], i, Vector3(p[0], p[1], p[2]), float(s.get("yaw", 0.0)))
