extends Node3D
## Asset look-development scene: lays out GLB assets in a row on a sand slab
## under the standard daylight rig.
## godot --path game res://scenes/debug/lookdev.tscn -- --assets=res://a.glb,res://b.glb [--spacing=8]

@onready var _root: Node3D = $Assets


func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1]
	var paths: PackedStringArray = args.get("assets", "").split(",", false)
	var spacing := float(args.get("spacing", "8"))
	var x := -spacing * (paths.size() - 1) * 0.5
	for p in paths:
		var scene := load(p) as PackedScene
		if scene == null:
			push_error("lookdev: cannot load %s" % p)
			continue
		var inst := scene.instantiate() as Node3D
		inst.position = Vector3(x, 0.0, 0.0)
		_root.add_child(inst)
		MaterialLibrary.apply(inst)
		x += spacing
