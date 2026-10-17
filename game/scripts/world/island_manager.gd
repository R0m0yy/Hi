@tool
class_name IslandManager
extends Node3D
## Root of an island scene. Applies the stylised materials to the generated
## assets underneath it, builds terrain collision from the exported
## heightmap, and answers terrain queries for gameplay systems.

@export var island_name := "Haven Island"
@export_file("*.json") var heightmap_json := "res://assets/terrain/haven_heightmap.json"
## Gentle terrain needs no self-shadowing, and casting from it causes
## acne-like blotches on the near-flat facets; props still shadow it.
@export var terrain_node := NodePath("Terrain")

var heightmap: TerrainHeightmap


func _ready() -> void:
	add_to_group("island")
	MaterialLibrary.apply(self)
	var terrain := get_node_or_null(terrain_node)
	if terrain:
		for mi in terrain.find_children("*", "MeshInstance3D", true, false):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	heightmap = TerrainHeightmap.load_from(heightmap_json)
	if heightmap and not Engine.is_editor_hint():
		_build_collision()


func _build_collision() -> void:
	var body := StaticBody3D.new()
	body.name = "TerrainCollision"
	body.collision_layer = 1
	var cs := CollisionShape3D.new()
	cs.shape = heightmap.make_shape()
	cs.position = heightmap.shape_center()
	cs.scale = Vector3(heightmap.spacing, 1.0, heightmap.spacing)
	body.add_child(cs)
	add_child(body)


func height_at(world_x: float, world_z: float) -> float:
	if heightmap == null:
		return 0.0
	var local := to_local(Vector3(world_x, 0.0, world_z))
	return heightmap.height_at(local.x, local.z) + global_position.y
