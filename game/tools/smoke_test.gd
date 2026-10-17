extends SceneTree
## Headless smoke test: loads the main scene, lets physics settle, then
## checks terrain collision, heightmap queries and the water system.
##   godot --headless --path game --script res://tools/smoke_test.gd

var _frames := 0
var _failures := 0


func _initialize() -> void:
	change_scene_to_file("res://scenes/main.tscn")


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames < 30:
		return false
	var island: IslandManager = get_first_node_in_group("island")
	var water: WaterSystem = get_first_node_in_group("water")
	_check(island != null, "island present")
	_check(water != null, "water present")
	if island:
		_check(island.heightmap != null, "heightmap loaded")
		var camp := island.height_at(12.0, 12.0)
		_check(camp > 0.2 and camp < 2.0, "camp ground above water (%.2f)" % camp)
		var deep := island.height_at(100.0, 100.0)
		_check(deep < -10.0, "open ocean is deep (%.2f)" % deep)
		var space := island.get_world_3d().direct_space_state
		var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(12, 30, 12), Vector3(12, -30, 12)))
		_check(not hit.is_empty() and absf(hit.position.y - camp) < 0.3, "terrain collision matches heightmap")
		var rock_hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-8, 30, -10), Vector3(-8, -30, -10)))
		_check(not rock_hit.is_empty() and rock_hit.position.y > 3.0, "rock stack has collision (top %.2f)" % (rock_hit.position.y if rock_hit else 0.0))
		var scatter := island.find_children("*", "ScatterField", true, false)
		_check(scatter.size() == 11, "11 scatter fields")
		var mmi := 0
		for s in scatter:
			mmi += s.get_child_count(true)
		_check(mmi > 0, "scatter built %d multimeshes" % mmi)
	if water:
		_check(absf(water.surface_height_at(Vector3(50, 0, 50))) < 0.2, "water surface near 0")
	var fire := root.find_child("Campfire", true, false)
	_check(fire is Campfire, "campfire wrapper instanced")
	print("smoke_test: %s (%d failure(s))" % ["PASS" if _failures == 0 else "FAIL", _failures])
	quit(1 if _failures else 0)
	return true


func _check(ok: bool, what: String) -> void:
	print("  [%s] %s" % ["ok" if ok else "FAIL", what])
	if not ok:
		_failures += 1
