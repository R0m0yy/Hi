@tool
class_name ScatterField
extends Node3D
## Instanced set dressing (pebbles, grass tufts, ferns, seaweed) drawn with
## one MultiMesh per mesh variant. Instances come from the layout JSON
## written by tools/blender/haven_layout.py:
##   [x, y, z, rotation_y_degrees, uniform_scale, variant_index]
## The source scene's MeshInstance3D children (sorted by name) are the
## variants. MultiMeshes are internal children, rebuilt on load and never
## saved into the scene file.

@export var source_scene: PackedScene
@export_file("*.json") var layout_json := "res://assets/terrain/haven_layout.json"
@export var layout_key := ""
@export var cast_shadows := true

## Per layout instance: [variant, index in that variant's MultiMesh].
var _slots: Array = []
var _positions: Array[Vector3] = []
var _buckets := {}
var _mmis := {}


func _ready() -> void:
	rebuild()


func rebuild() -> void:
	for child in get_children(true):
		if child is MultiMeshInstance3D:
			child.queue_free()
	if source_scene == null or layout_key.is_empty():
		return
	var layout = JSON.parse_string(FileAccess.get_file_as_string(layout_json))
	if not (layout is Dictionary) or not layout.get("scatter", {}).has(layout_key):
		push_warning("ScatterField: no scatter set '%s' in %s" % [layout_key, layout_json])
		return
	var meshes := _variant_meshes()
	if meshes.is_empty():
		return
	var buckets := {}
	_slots.clear()
	_positions.clear()
	for inst in layout["scatter"][layout_key]["instances"]:
		var variant: int = (int(inst[5]) if inst.size() > 5 else 0) % meshes.size()
		var basis := Basis(Vector3.UP, deg_to_rad(inst[3])).scaled(Vector3.ONE * float(inst[4]))
		if not buckets.has(variant):
			buckets[variant] = []
		_slots.append([variant, buckets[variant].size()])
		_positions.append(Vector3(inst[0], inst[1], inst[2]))
		buckets[variant].append(Transform3D(basis, Vector3(inst[0], inst[1], inst[2])))
	_buckets = buckets
	_mmis.clear()
	for variant in buckets:
		var xforms: Array = buckets[variant]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = meshes[variant]
		mm.instance_count = xforms.size()
		for i in xforms.size():
			mm.set_instance_transform(i, xforms[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast_shadows \
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi, false, Node.INTERNAL_MODE_BACK)
		_mmis[variant] = mmi


func _variant_meshes() -> Array[Mesh]:
	var out: Array[Mesh] = []
	var inst := source_scene.instantiate()
	var found := inst.find_children("*", "MeshInstance3D", true, false)
	found.sort_custom(func(a, b): return String(a.name) < String(b.name))
	for mi in found:
		var mesh: Mesh = mi.mesh.duplicate()
		MaterialLibrary.apply_to_mesh(mesh)
		out.append(mesh)
	inst.free()
	return out


func instance_count() -> int:
	return _slots.size()


## Local position of layout instance `i` (the field sits at the island origin).
func instance_position(i: int) -> Vector3:
	return _positions[i]


## Hides or shows one instance (harvested plants and picked-up pebbles).
func set_instance_visible(i: int, visible_now: bool) -> void:
	if i < 0 or i >= _slots.size():
		return
	var variant: int = _slots[i][0]
	var j: int = _slots[i][1]
	var mmi: MultiMeshInstance3D = _mmis.get(variant)
	if mmi == null:
		return
	var xf: Transform3D = _buckets[variant][j]
	if not visible_now:
		xf = Transform3D(Basis().scaled(Vector3.ONE * 0.0001), xf.origin + Vector3.DOWN * 50.0)
	mmi.multimesh.set_instance_transform(j, xf)
