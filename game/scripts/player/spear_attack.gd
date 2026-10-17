class_name SpearAttack
extends Node
## Pole-spear thrust: the spear shoots out ~4 m along the aim and snaps back.
## Any fish the tip passes within HIT_RADIUS of is caught. In the water the
## aim locks onto the nearest fish in a forward cone.

const RANGE := 4.2
const OUT_TIME := 0.16
const BACK_TIME := 0.24
const HIT_RADIUS := 0.55
const COOLDOWN := 0.3
const ASSIST_ANGLE := 0.72  # cos(~44 deg)

var _phase := 0
var _t := 0.0
var _cooldown := 0.0
var _origin := Vector3.ZERO
var _dir := Vector3.FORWARD
var _prev_tip := Vector3.ZERO
var _caught: Node3D
var _visual: MeshInstance3D

@onready var player: PlayerController = get_parent()


func _ready() -> void:
	_visual = MeshInstance3D.new()
	_visual.top_level = true
	_visual.visible = false
	var path := ItemDB.model_path("spear")
	if not path.is_empty():
		var inst: Node3D = (load(path) as PackedScene).instantiate()
		MaterialLibrary.apply(inst)
		_visual.add_child(inst)
	else:
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.02
		cyl.bottom_radius = 0.02
		cyl.height = 1.6
		_visual.mesh = cyl
	add_child(_visual)


func thrust() -> void:
	if _phase != 0 or _cooldown > 0.0:
		return
	var fwd := player.model.global_basis.z.normalized()
	var in_water := player.mode != PlayerController.Mode.GROUND
	_origin = player.global_position + Vector3.UP * (0.55 if in_water else 1.15) + Vector3(fwd.x, 0.0, fwd.z) * 0.3
	_dir = Vector3(fwd.x, 0.0, fwd.z).normalized()
	var target := _assist_target(_dir)
	if target:
		_dir = (target.global_position - _origin).normalized()
		player.face_direction(Vector3(_dir.x, 0.0, _dir.z))
	_phase = 1
	_t = 0.0
	_prev_tip = _origin
	_caught = null
	player.play_action("spear_thrust", 0.45)
	if player.held:
		player.held.set_visible_in_hand(false)
	_visual.visible = true
	AudioManager.play("spear_whoosh", _origin, -4.0)


func _assist_target(fwd: Vector3) -> Node3D:
	var best: Node3D = null
	var best_d := RANGE + 1.0
	for f in get_tree().get_nodes_in_group("fish"):
		var fish := f as Fish
		if fish == null or not fish.alive:
			continue
		var d := fish.global_position - _origin
		var dist := d.length()
		if dist > RANGE + 0.6 or dist < 0.05:
			continue
		var flat := Vector3(d.x, 0.0, d.z).normalized()
		if flat.dot(fwd) < ASSIST_ANGLE:
			continue
		if dist < best_d:
			best_d = dist
			best = fish
	return best


func _physics_process(delta: float) -> void:
	_cooldown -= delta
	if _phase == 0:
		return
	_t += delta / (OUT_TIME if _phase == 1 else BACK_TIME)
	var k := clampf(_t, 0.0, 1.0)
	var reach := RANGE * (ease(k, 0.4) if _phase == 1 else 1.0 - ease(k, 2.0))
	var tip := _origin + _dir * reach
	_place_visual(tip)
	if _phase == 1:
		_check_hits(_prev_tip, tip)
		_prev_tip = tip
		if _t >= 1.0:
			_phase = 2
			_t = 0.0
	elif _t >= 1.0:
		_phase = 0
		_cooldown = COOLDOWN
		_visual.visible = false
		if player.held:
			player.held.set_visible_in_hand(true)
		if _caught:
			_caught = null
	if _caught:
		_caught.global_position = tip


func _place_visual(tip: Vector3) -> void:
	var tail := tip - _dir * 1.55  # the model's grip sits 1.55 m behind its tip
	_visual.global_position = tail
	if _dir.cross(Vector3.UP).length() > 0.01:
		_visual.look_at(tip, Vector3.UP)
	# The spear model points along +Y: rotate so +Y follows -Z (look direction).
	_visual.rotate_object_local(Vector3.RIGHT, -PI * 0.5)


func _check_hits(a: Vector3, b: Vector3) -> void:
	if _caught:
		return
	for f in get_tree().get_nodes_in_group("fish"):
		var fish := f as Fish
		if fish == null or not fish.alive:
			continue
		var p := fish.global_position
		var closest := Geometry3D.get_closest_point_to_segment(p, a, b)
		if closest.distance_to(p) <= HIT_RADIUS + fish.radius:
			fish.speared()
			_caught = fish
			var def: Dictionary = ItemDB.FISH[fish.species]
			Game.give(def["item"], 1, true)
			Game.notify("Speared a %s!" % def["name"], def["item"])
			Game.record("catch")
			Game.record("spear_catch")
			player.wear_selected(2.0)
			AudioManager.play("spear_hit", p)
			return
