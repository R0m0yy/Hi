@tool
class_name WaterSystem
extends MeshInstance3D
## The ocean surface. Owns the water plane mesh, publishes the water level
## to every shader (global uniform `water_level`) and answers gameplay
## queries (surface height, submersion) using the same wave function as
## shaders/water.gdshader.

@export var size := 700.0:
	set(v):
		size = v
		_rebuild()
@export var subdivisions := 175:
	set(v):
		subdivisions = v
		_rebuild()
@export var water_material: Material = preload("res://materials/water_ocean.tres"):
	set(v):
		water_material = v
		_rebuild()
## A flat floor far below the surface so the ocean never "sees" past the
## edge of the island terrain (the water shader colours by depth).
@export var deep_floor_depth := 26.0

var _floor: MeshInstance3D


func _ready() -> void:
	add_to_group("water")
	_rebuild()
	RenderingServer.global_shader_parameter_set("water_level", global_position.y)


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSFORM_CHANGED and is_inside_tree():
		RenderingServer.global_shader_parameter_set("water_level", global_position.y)


func _rebuild() -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	plane.subdivide_width = subdivisions
	plane.subdivide_depth = subdivisions
	plane.material = water_material
	mesh = plane
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	set_notify_transform(true)
	if not is_inside_tree():
		return
	if _floor == null:
		_floor = MeshInstance3D.new()
		_floor.name = "DeepFloor"
		add_child(_floor, false, Node.INTERNAL_MODE_BACK)
	var floor_mesh := PlaneMesh.new()
	floor_mesh.size = Vector2(size, size)
	var floor_mat := StandardMaterial3D.new()
	floor_mat.albedo_color = Color(0.03, 0.12, 0.25)
	floor_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	floor_mesh.material = floor_mat
	_floor.mesh = floor_mesh
	_floor.position = Vector3(0.0, -deep_floor_depth, 0.0)
	_floor.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func water_level() -> float:
	return global_position.y


## Approximate surface height including the shader's gentle swell.
func surface_height_at(pos: Vector3) -> float:
	var t := Time.get_ticks_msec() / 1000.0
	var h := sin(pos.x * 0.21 + t * 0.9) * 0.5 + sin(pos.z * 0.17 - t * 0.7) * 0.35 \
			+ sin((pos.x + pos.z) * 0.33 + t * 1.3) * 0.15
	var amp := 0.05  # shader default
	if water_material is ShaderMaterial:
		var v = water_material.get_shader_parameter("wave_height")
		if v != null:
			amp = v
	return global_position.y + h * amp


func depth_below_surface(pos: Vector3) -> float:
	return surface_height_at(pos) - pos.y
