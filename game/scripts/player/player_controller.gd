class_name PlayerController
extends CharacterBody3D
## The castaway. Camera-relative movement on land, automatic swimming in
## deep water, and diving while the dive action is held. Drives the
## skeletal animations imported with castaway.glb.

enum Mode { GROUND, SWIM, DIVE }

const LOOPING := ["idle", "walk", "run", "swim", "dive", "fish_reel", "cook"]

@export var walk_speed := 3.2
@export var run_speed := 6.0
@export var swim_speed := 2.3
@export var dive_speed := 2.0
@export var acceleration := 14.0
@export var turn_speed := 12.0
@export var gravity := 22.0
## Water deeper than this (metres) at the player's position means swimming.
@export var swim_depth := 1.0
## How far below the surface the body origin floats while swimming.
@export var float_depth := 1.05
@export var seabed_clearance := 0.6

@onready var model: Node3D = $Model

var mode := Mode.GROUND
var _anim: AnimationPlayer
var _island: IslandManager
var _water: WaterSystem
var _rig: IsometricCamera
var _action_lock := 0.0


func _ready() -> void:
	add_to_group("player")
	MaterialLibrary.apply(model)
	_anim = model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	for name in LOOPING:
		if _anim.has_animation(name):
			_anim.get_animation(name).loop_mode = Animation.LOOP_LINEAR
	_anim.play("idle")
	_island = get_tree().get_first_node_in_group("island") as IslandManager
	_water = get_tree().get_first_node_in_group("water") as WaterSystem
	_rig = get_tree().get_first_node_in_group("camera_rig") as IsometricCamera


func _physics_process(delta: float) -> void:
	var wish := _wish_direction()
	_update_mode()
	match mode:
		Mode.GROUND:
			var speed := run_speed if Input.is_action_pressed("sprint") else walk_speed
			_move_horizontal(wish * speed, delta)
			if not is_on_floor():
				velocity.y -= gravity * delta
			else:
				velocity.y = -0.5
		Mode.SWIM:
			_move_horizontal(wish * swim_speed, delta)
			velocity.y = (_surface_y() - float_depth - global_position.y) * 6.0
		Mode.DIVE:
			_move_horizontal(wish * swim_speed * 0.85, delta)
			var floor_y := _ground_y() + seabed_clearance
			var target := maxf(floor_y, global_position.y - 4.0)
			velocity.y = clampf((target - global_position.y) * 4.0, -dive_speed, dive_speed)
	move_and_slide()
	_face(wish, delta)
	_animate(delta)


## Plays a one-shot action (gather, fish_cast, spear_throw, chop...) and
## holds locomotion animations until it finishes. Used by gameplay systems.
func play_action(anim_name: String) -> void:
	if not _anim.has_animation(anim_name):
		return
	_anim.play(anim_name, 0.15)
	_action_lock = _anim.get_animation(anim_name).length


func _wish_direction() -> Vector3:
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	if input == Vector2.ZERO:
		return Vector3.ZERO
	var yaw := deg_to_rad(_rig.yaw_degrees) if _rig else 0.0
	var right := Vector3(cos(yaw), 0.0, -sin(yaw))
	var back := Vector3(sin(yaw), 0.0, cos(yaw))
	return (right * input.x + back * input.y).limit_length(1.0)


func _move_horizontal(target: Vector3, delta: float) -> void:
	var t := 1.0 - exp(-acceleration * delta)
	velocity.x = lerpf(velocity.x, target.x, t)
	velocity.z = lerpf(velocity.z, target.z, t)


func _update_mode() -> void:
	var depth := water_depth()
	match mode:
		Mode.GROUND:
			if depth > swim_depth and global_position.y < _surface_y() - float_depth + 0.25:
				mode = Mode.SWIM
		Mode.SWIM:
			if depth < swim_depth - 0.15:
				mode = Mode.GROUND
			elif Input.is_action_pressed("dive") and depth > swim_depth + 0.8:
				mode = Mode.DIVE
		Mode.DIVE:
			if not Input.is_action_pressed("dive"):
				if global_position.y >= _surface_y() - float_depth - 0.1:
					mode = Mode.SWIM
				else:
					velocity.y = dive_speed  # surface again
					mode = Mode.SWIM


func _face(wish: Vector3, delta: float) -> void:
	var flat := Vector3(velocity.x, 0.0, velocity.z)
	if flat.length() < 0.2 and wish == Vector3.ZERO:
		return
	var dir := wish if wish != Vector3.ZERO else flat.normalized()
	var target := atan2(dir.x, dir.z)  # the model faces +Z
	model.rotation.y = lerp_angle(model.rotation.y, target, 1.0 - exp(-turn_speed * delta))


func _animate(delta: float) -> void:
	if _action_lock > 0.0:
		_action_lock -= delta
		return
	var speed := Vector2(velocity.x, velocity.z).length()
	var want := "idle"
	var rate := 1.0
	match mode:
		Mode.GROUND:
			if speed > walk_speed * 1.15:
				want = "run"
				rate = speed / run_speed * 1.1
			elif speed > 0.3:
				want = "walk"
				rate = speed / walk_speed * 1.05
		Mode.SWIM:
			want = "swim"
			rate = 0.7 + speed / swim_speed * 0.5
		Mode.DIVE:
			want = "dive"
	if _anim.current_animation != want:
		_anim.play(want, 0.2)
	_anim.speed_scale = maxf(rate, 0.4)


## Depth of water (metres) between the surface and the ground under the player.
func water_depth() -> float:
	return _surface_y() - _ground_y()


func _surface_y() -> float:
	return _water.surface_height_at(global_position) if _water else 0.0


func _ground_y() -> float:
	return _island.height_at(global_position.x, global_position.z) if _island else -100.0
