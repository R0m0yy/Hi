class_name WorldPopulator
extends Node
## Turns an island's generated set dressing into gameplay at load time:
## palms and rocks become renewable resource nodes, driftwood, pebbles,
## shells and fibre plants become pickups, the camp gets a working
## campfire, chest, shelter and supplies, and the rowboat becomes a boat.
## Everything is attached by name, so rebuilding the island art keeps the
## gameplay in place.

const ROCK_SCENES := ["rock_cluster_a", "rock_cluster_b", "boulder_a", "boulder_b", "boulder_c", "boulder_d"]


static func populate(island: Node3D, profile: Dictionary = {}) -> void:
	var count := 0
	for group in island.get_children():
		if not (group is Node3D):
			continue
		for item in group.get_children():
			if item is Node3D:
				count += _attach(island, item as Node3D, profile)
	for field in island.find_children("*", "ScatterField", true, false):
		count += _scatter_pickups(island, field as ScatterField)
	for extra in profile.get("extras", []):
		count += _extra(island, extra)
	print("WorldPopulator: %s -> %d gameplay objects" % [island.name, count])


static func _scene_name(node: Node) -> String:
	return node.scene_file_path.get_file().get_basename()


static func _attach(island: Node3D, item: Node3D, profile: Dictionary) -> int:
	var n := String(item.name)
	var scene := _scene_name(item)
	if scene.begins_with("palm_"):
		var r := ResourceNode.new()
		r.name = "Resource"
		r.kind = "palm"
		r.reach = 2.0
		item.add_child(r)
		return 1
	if scene in ROCK_SCENES and item.global_position.y > -0.9 and not n.begins_with("Offshore"):
		var aabb := _aabb(item)
		if aabb.size.y > 0.3:
			_rock_collider(item, aabb)
		var r := ResourceNode.new()
		r.name = "Resource"
		r.kind = "rock"
		r.reach = maxf(aabb.size.x, aabb.size.z) * 0.5 + 1.0
		item.add_child(r)
		return 1
	if scene.begins_with("driftwood"):
		return _pickup(item, "wood", 3, 360.0, "Collect")
	if n == "Planks":
		return _pickup(item, "wood", 4, 0.0, "Collect")
	if n == "Coconuts":
		return _pickup(item, "coconut", 2, 420.0, "Pick up")
	if n == "Campfire":
		var c := CookingStation.new()
		c.name = "Cooking"
		c.reach = 2.2
		item.add_child(c)
		return 1
	if n == "Chest":
		var box := StorageBox.new()
		box.name = "Storage"
		box.title = "camp chest"
		box.starting_items = profile.get("chest", {})
		item.add_child(box)
		return 1
	if n == "LeanTo":
		var bed := ShelterBed.new()
		bed.name = "Bed"
		bed.reach = 2.4
		item.add_child(bed)
		bed.position = Vector3(0, 0, 1.3)
		return 1
	if n == "Barrel" or n == "Barrel2" or n == "Crate":
		var s := Searchable.new()
		s.name = "Search"
		s.title = "crate" if n == "Crate" else "barrel"
		s.loot = profile.get("loot", {}).get(n, {"rope": 1})
		item.add_child(s)
		return 1
	if n == "WreckRibs":
		var s := Searchable.new()
		s.name = "Search"
		s.title = "shipwreck"
		s.reach = 3.5
		s.loot = profile.get("loot", {}).get(n, {"wood": 4, "rope": 1})
		item.add_child(s)
		return 1
	if n == "Rowboat" or n == "Raft":
		_make_boat(item, n == "Rowboat")
		return 1
	return 0


static func _pickup(item: Node3D, id: String, amount: int, respawn: float, verb: String) -> int:
	var p := Pickup.new()
	p.name = "Pickup"
	p.item_id = id
	p.amount = amount
	p.respawn_seconds = respawn
	p.verb = verb
	p.priority = 0.3
	item.add_child(p)
	return _wrap_visual(item, p)


## Moves the item's visual children under a "Visual" node so the pickup can
## hide them without hiding itself.
static func _wrap_visual(item: Node3D, p: Pickup) -> int:
	var visual := Node3D.new()
	visual.name = "Visual"
	item.add_child(visual)
	for child in item.get_children():
		if child != visual and child != p:
			child.reparent(visual, false)
	p.visual_path = p.get_path_to(visual)
	p._visual = visual
	p._apply_visibility()
	return 1


static func _make_boat(item: Node3D, rowboat: bool) -> void:
	var parent := item.get_parent()
	var boat := Boat.new()
	boat.name = String(item.name) + "Boat"
	boat.title = "rowboat" if rowboat else "raft"
	boat.needs_repair = rowboat
	boat.max_speed = 5.5 if rowboat else 4.2
	boat.reach = 2.6
	boat.seat = Vector3(0.0, 0.12, -0.25) if rowboat else Vector3(0.0, 0.3, 0.0)
	boat.driver_animation = "row" if rowboat else "sit"
	boat.transform = item.transform
	parent.add_child(boat)
	item.reparent(boat, false)
	item.transform = Transform3D()
	boat.visual_path = boat.get_path_to(item)


static func _scatter_pickups(island: Node3D, field: ScatterField) -> int:
	var key := field.layout_key
	var spec := {}
	match key:
		"bushes", "ferns":
			spec = {"item": "fiber", "amount": 2, "respawn": 300.0, "verb": "Gather", "reach": 1.8, "every": 1, "sound": "rustle"}
		"beach_grass":
			spec = {"item": "fiber", "amount": 1, "respawn": 240.0, "verb": "Gather", "reach": 1.5, "every": 1, "sound": "rustle"}
		"pebbles":
			spec = {"item": "stone", "amount": 1, "respawn": 420.0, "verb": "Pick up", "reach": 1.4, "every": 1, "sound": "stone_pick"}
		"shells":
			spec = {"item": "shell", "amount": 1, "respawn": 600.0, "verb": "Pick up", "reach": 1.4, "every": 1, "sound": "pickup"}
		_:
			return 0
	var made := 0
	for i in field.instance_count():
		if i % int(spec["every"]) != 0:
			continue
		var p := Pickup.new()
		p.name = "%s_%d" % [key, i]
		p.item_id = spec["item"]
		p.amount = spec["amount"]
		p.respawn_seconds = spec["respawn"]
		p.verb = spec["verb"]
		p.reach = spec["reach"]
		p.sound = spec["sound"]
		p.scatter = field
		p.scatter_index = i
		p.priority = -0.35
		p.position = field.instance_position(i)
		field.add_child(p)
		made += 1
	return made


static func _extra(island: Node3D, extra: Dictionary) -> int:
	var node: Interactable
	match String(extra.get("type", "")):
		"spring":
			node = WaterSource.new()
		_:
			return 0
	node.name = String(extra.get("name", "Extra"))
	var p: Array = extra["pos"]
	island.add_child(node)
	var pos := Vector3(p[0], 0.0, p[1])
	pos.y = p[2] if p.size() > 2 else (island as IslandManager).height_at(pos.x, pos.z)
	node.global_position = pos
	node.reach = extra.get("reach", 2.0)
	if extra.has("visual"):
		var v: Node3D = load(extra["visual"]).instantiate()
		node.add_child(v)
	return 1


static func _aabb(node: Node3D) -> AABB:
	var out := AABB()
	var first := true
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		var box := m.global_transform * m.get_aabb()
		if first:
			out = box
			first = false
		else:
			out = out.merge(box)
	return out


static func _rock_collider(item: Node3D, aabb: AABB) -> void:
	if item.find_child("Collider", false, false):
		return
	var body := StaticBody3D.new()
	body.name = "Collider"
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = maxf(minf(aabb.size.x, aabb.size.z) * 0.42, 0.3)
	cyl.height = aabb.size.y
	cs.shape = cyl
	body.add_child(cs)
	item.add_child(body)
	body.global_position = aabb.get_center()
