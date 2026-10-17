extends Node3D
## Lines up character instances, each frozen at a point in one animation.
## godot --path game res://scenes/debug/character_lookdev.tscn -- --anims=idle@0.5,walk@0.25 [--spacing=1.3]

const CHARACTER := preload("res://assets/models/characters/castaway.glb")


func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1]
	var specs: PackedStringArray = args.get("anims", "idle@0").split(",", false)
	var spacing := float(args.get("spacing", "1.3"))
	var x := -spacing * (specs.size() - 1) * 0.5
	for spec in specs:
		var parts := spec.split("@")
		var inst := CHARACTER.instantiate() as Node3D
		inst.position = Vector3(x, 0.0, 0.0)
		add_child(inst)
		MaterialLibrary.apply(inst)
		var ap := inst.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
		var anim := parts[0]
		var t := float(parts[1]) if parts.size() > 1 else 0.0
		ap.play(anim)
		ap.seek(t * ap.get_animation(anim).length, true)
		ap.pause()
		x += spacing
