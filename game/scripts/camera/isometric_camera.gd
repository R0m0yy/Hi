class_name IsometricCamera
extends Node3D
## Elevated orthographic three-quarter camera (art bible §5).
## The rig sits on the focus point; the Camera3D child is pushed back along
## the rig's local +Z so the orthographic view frames the focus.

@export var target_path: NodePath
@export_range(-85.0, -20.0) var pitch_degrees := -50.0
@export var yaw_degrees := 40.0
@export var zoom_size := 17.0
@export var min_size := 9.0
@export var max_size := 70.0
@export var zoom_step := 1.15
## Seconds for the camera to close half the distance to its goal.
@export var follow_half_life := 0.16
@export var zoom_half_life := 0.12
## Metres of look-ahead per m/s of target velocity.
@export var look_ahead := 0.25
@export var camera_distance := 60.0

@onready var camera: Camera3D = $Camera3D

var _focus := Vector3.ZERO
var _size := 30.0
var _target: Node3D


func _ready() -> void:
	add_to_group("camera_rig")
	_target = get_node_or_null(target_path) as Node3D
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = 0.5
	camera.far = camera_distance * 2.5
	_size = zoom_size
	if _target:
		_focus = _target.global_position
	else:
		_focus = global_position
	_apply()


func _process(delta: float) -> void:
	if _target:
		var goal := _target.global_position
		var vel = _target.get("velocity")
		if vel is Vector3:
			goal += Vector3(vel.x, 0.0, vel.z) * look_ahead
		_focus = _focus.lerp(goal, _damp(follow_half_life, delta))
	_size = lerpf(_size, zoom_size, _damp(zoom_half_life, delta))
	_apply()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("zoom_in"):
		zoom_size = clampf(zoom_size / zoom_step, min_size, max_size)
	elif event.is_action_pressed("zoom_out"):
		zoom_size = clampf(zoom_size * zoom_step, min_size, max_size)


## Instantly frames `focus` (used by cutscenes and the screenshot tool).
func set_view(focus: Vector3, size: float, yaw: float, pitch: float) -> void:
	_target = null
	_focus = focus
	zoom_size = size
	_size = size
	yaw_degrees = yaw
	pitch_degrees = pitch
	_apply()


func set_target(node: Node3D) -> void:
	_target = node


func _apply() -> void:
	global_position = _focus
	rotation_degrees = Vector3(pitch_degrees, yaw_degrees, 0.0)
	camera.position = Vector3(0.0, 0.0, camera_distance)
	camera.size = _size


static func _damp(half_life: float, delta: float) -> float:
	if half_life <= 0.0:
		return 1.0
	return 1.0 - pow(0.5, delta / half_life)
