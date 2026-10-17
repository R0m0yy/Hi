class_name Builder
extends Node
## Placement mode for structure kits: a ghost follows the player's aim,
## turns green where it fits (dry flat ground, or water for rafts, and
## clear of other structures and props), and use confirms. R rotates,
## cancel backs out.

signal placement_changed(active: bool, valid: bool, item_id: String)

const DISTANCE := 2.8
const MAX_SLOPE := 0.55

var active := false
var valid := false
var item_id := ""
var type := ""
var _ghost: Node3D
var _yaw := 0.0
var _armed := false
var _ok_mat: StandardMaterial3D
var _bad_mat: StandardMaterial3D

@onready var player: PlayerController = get_parent()


func _ready() -> void:
	_ok_mat = _ghost_material(Color(0.45, 1.0, 0.6, 0.45))
	_bad_mat = _ghost_material(Color(1.0, 0.4, 0.35, 0.45))


static func _ghost_material(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.no_depth_test = false
	return m


func begin(id: String) -> void:
	var structure: String = ItemDB.item(id).get("structure", "")
	if structure.is_empty() or not Structures.DEFS.has(structure):
		return
	end()
	item_id = id
	type = structure
	_ghost = Structures.ghost(type)
	_ghost.top_level = true
	add_child(_ghost)
	_yaw = player.model.global_rotation.y
	active = true
	_armed = false
	Game.notify("Place the %s: %s to build, %s to rotate, %s to cancel" % [ItemDB.display_name(id),
			InputBindings.glyph("use_tool"), InputBindings.glyph("rotate_build"), InputBindings.glyph("cancel")], id)
	placement_changed.emit(true, false, id)


func end() -> void:
	if _ghost and is_instance_valid(_ghost):
		_ghost.queue_free()
	_ghost = null
	active = false
	placement_changed.emit(false, false, item_id)


func _physics_process(_delta: float) -> void:
	if not active:
		return
	if Game.selected_item() != item_id or player.mode != PlayerController.Mode.GROUND or not Game.is_playing():
		end()
		return
	var controls := not Game.ui_open
	if controls and Input.is_action_just_pressed("rotate_build"):
		_yaw += PI / 4.0
	var fwd := player.model.global_basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var def: Dictionary = Structures.DEFS[type]
	var dist := DISTANCE + float(def["radius"]) * 0.6
	var pos := player.global_position + fwd * dist
	var h := World.height_at(pos.x, pos.z)
	var water := World.water_level()
	if def["water"]:
		pos.y = water
	else:
		pos.y = h
	valid = _check(pos, def, h, water)
	_ghost.global_position = pos
	_ghost.global_rotation = Vector3(0.0, _yaw, 0.0)
	_paint(valid)
	placement_changed.emit(true, valid, item_id)
	if not controls:
		return
	if Input.is_action_just_pressed("cancel"):
		end()
		return
	# Ignore the press that opened placement mode.
	if not Input.is_action_pressed("use_tool"):
		_armed = true
	if _armed and Input.is_action_just_pressed("use_tool"):
		if valid:
			_place(pos)
		else:
			Game.notify("It doesn't fit there", "")
			AudioManager.play("error")


func _check(pos: Vector3, def: Dictionary, h: float, water: float) -> bool:
	var r: float = def["radius"]
	if def["water"]:
		var depth := water - h
		if depth < 0.7:
			return false
	else:
		if h < water + 0.2:
			return false
		var lo := h
		var hi := h
		for i in 6:
			var a := TAU * i / 6.0
			var hh := World.height_at(pos.x + cos(a) * r, pos.z + sin(a) * r)
			lo = minf(lo, hh)
			hi = maxf(hi, hh)
		if hi - lo > MAX_SLOPE * r * 1.3 or lo < water + 0.05:
			return false
	for node in get_tree().get_nodes_in_group("interactable"):
		var n := node as Node3D
		if n is Pickup:
			continue
		var d := Vector2(n.global_position.x - pos.x, n.global_position.z - pos.z).length()
		if d < r + 0.7:
			return false
	var space := player.get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	var shape := SphereShape3D.new()
	shape.radius = r * 0.8
	q.shape = shape
	q.transform = Transform3D(Basis(), pos + Vector3.UP * (r * 0.8 + 0.3))
	q.exclude = [player.get_rid()]
	for hit in space.intersect_shape(q, 8):
		var col = hit.get("collider")
		if col is StaticBody3D and col.get_parent() is IslandManager:
			continue  # the terrain itself
		return false
	return true


func _paint(ok: bool) -> void:
	var mat := _ok_mat if ok else _bad_mat
	for mi in _ghost.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = mat
		(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _place(pos: Vector3) -> void:
	if not Game.inventory.remove(item_id, 1):
		end()
		return
	var index := Game.structures.size()
	Game.structures.append({"type": type, "pos": [pos.x, pos.y, pos.z], "yaw": _yaw})
	Structures.spawn(type, index, pos, _yaw)
	Game.record("place:" + type)
	Game.notify("Built a %s" % ItemDB.display_name(item_id), item_id)
	AudioManager.play("build", pos)
	player.play_action("chop")
	end()
