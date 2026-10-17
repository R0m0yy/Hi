class_name IsometricCamera
extends Node3D
## Elevated three-quarter gameplay camera (art bible §5).
## The rig sits on the focus point; the Camera3D child is pushed back along
## the rig's local +Z. `zoom_size` is the view height in metres at the focus,
## so zoom behaves the same with either projection:
##   fov_degrees <= 0 -> orthographic
##   fov_degrees  > 0 -> narrow-angle perspective (Ref B's gentle depth)

@export var target_path: NodePath
@export_range(-85.0, -20.0) var pitch_degrees := -40.0
@export var yaw_degrees := 18.0
@export var fov_degrees := 38.0
@export var zoom_size := 17.0
@export var min_size := 9.0
@export var max_size := 110.0
@export var zoom_step := 1.15
## Seconds for the camera to close half the distance to its goal.
@export var follow_half_life := 0.16
@export var zoom_half_life := 0.12
## Metres of look-ahead per m/s of target velocity.
@export var look_ahead := 0.25
## Orthographic only: how far back the camera sits (clipping, not framing).
@export var ortho_distance := 60.0

@onready var camera: Camera3D = $Camera3D

var _focus := Vector3.ZERO
var _size := 17.0
var _target: Node3D


func _ready() -> void:
	add_to_group("camera_rig")
	_target = get_node_or_null(target_path) as Node3D
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
## A negative `fov` keeps the current projection; 0 switches to orthographic.
func set_view(focus: Vector3, size: float, yaw: float, pitch: float, fov: float = -1.0) -> void:
	_target = null
	_focus = focus
	zoom_size = size
	_size = size
	yaw_degrees = yaw
	pitch_degrees = pitch
	if fov >= 0.0:
		fov_degrees = fov
	_apply()


func set_target(node: Node3D) -> void:
	_target = node


func _apply() -> void:
	global_position = _focus
	rotation_degrees = Vector3(pitch_degrees, yaw_degrees, 0.0)
	if fov_degrees > 0.0:
		var dist := _size * 0.5 / tan(deg_to_rad(fov_degrees) * 0.5)
		camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		camera.fov = fov_degrees
		camera.position = Vector3(0.0, 0.0, dist)
		camera.near = maxf(0.3, dist * 0.05)
		camera.far = dist * 6.0 + 200.0
	else:
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = _size
		camera.position = Vector3(0.0, 0.0, ortho_distance)
		camera.near = 0.5
		camera.far = ortho_distance * 2.5


static func _damp(half_life: float, delta: float) -> float:
	if half_life <= 0.0:
		return 1.0
	return 1.0 - pow(0.5, delta / half_life)
