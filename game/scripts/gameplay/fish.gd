class_name Fish
extends Node3D
## One swimming fish, steered by its FishSchool. Speared fish stop
## swimming, ride the spear tip back, then fade away.

var species := "snapper"
var alive := true
var radius := 0.15
var velocity := Vector3.ZERO
var school: Node
var _mesh: GeometryInstance3D
var _mats: Array[ShaderMaterial] = []


func setup(sp: String, owner_school: Node, model: PackedScene, rng: RandomNumberGenerator) -> void:
	species = sp
	school = owner_school
	var inst := model.instantiate()
	add_child(inst)
	MaterialLibrary.apply(inst)
	var phase := rng.randf() * TAU
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		_mesh = m
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in m.mesh.get_surface_count():
			var shared := m.get_surface_override_material(i) as ShaderMaterial
			if shared == null:
				continue
			var own := shared.duplicate() as ShaderMaterial
			own.set_shader_parameter("swim_phase", phase)
			m.set_surface_override_material(i, own)
			_mats.append(own)
	var s := rng.randf_range(0.85, 1.15)
	inst.scale = Vector3.ONE * s  # keep this node's basis orthonormal for steering
	var length: float = {"snapper": 0.4, "tang": 0.3, "mackerel": 0.55, "grouper": 0.78}.get(sp, 0.4)
	radius = length * 0.32 * s
	add_to_group("fish")


func set_swim_rate(rate: float) -> void:
	for m in _mats:
		m.set_shader_parameter("swim_rate", rate)


func speared() -> void:
	alive = false
	remove_from_group("fish")
	set_swim_rate(3.0)
	if school and school.has_method("on_fish_lost"):
		school.on_fish_lost(self)
	var tw := create_tween()
	tw.tween_interval(0.5)
	tw.tween_property(get_child(0), "scale", Vector3.ONE * 0.01, 0.35)
	tw.tween_callback(queue_free)
