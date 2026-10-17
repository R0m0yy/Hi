class_name MaterialLibrary
extends RefCounted
## Maps the placeholder material names exported by the Blender pipeline
## (tools/blender/pu_common.py) to the project's stylised shader materials.

const BY_NAME := {
	"PU_Solid": preload("res://materials/pu_solid.tres"),
	"PU_Faceted": preload("res://materials/pu_faceted.tres"),
	"PU_Rock": preload("res://materials/pu_rock.tres"),
	"PU_Plant": preload("res://materials/pu_plant.tres"),
	"PU_Foliage": preload("res://materials/pu_foliage.tres"),
	"PU_Cloth": preload("res://materials/pu_cloth.tres"),
	"PU_Emissive": preload("res://materials/pu_emissive.tres"),
	"PU_Terrain": preload("res://materials/terrain_haven.tres"),
}


## Material for a glTF material name (Godot may append ".001"-style suffixes).
static func lookup(material_name: String) -> Material:
	var base := material_name.get_slice(".", 0)
	return BY_NAME.get(base)


## Replaces every surface material under `root` that has a known name.
static func apply(root: Node) -> void:
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		_apply_mesh_instance(mi)
	if root is MeshInstance3D:
		_apply_mesh_instance(root)


static func _apply_mesh_instance(mi: MeshInstance3D) -> void:
	if mi.mesh == null:
		return
	for i in mi.mesh.get_surface_count():
		var src := mi.mesh.surface_get_material(i)
		if src == null:
			continue
		var mat := lookup(src.resource_name)
		if mat:
			mi.set_surface_override_material(i, mat)


## Applies the library to a bare mesh resource (used for MultiMesh scatter).
static func apply_to_mesh(mesh: Mesh) -> void:
	for i in mesh.get_surface_count():
		var src := mesh.surface_get_material(i)
		if src == null:
			continue
		var mat := lookup(src.resource_name)
		if mat:
			mesh.surface_set_material(i, mat)
