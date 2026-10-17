extends Node
## World-wide terrain and water queries across every loaded island
## (autoload "World"). Outside all heightmaps the open ocean floor is
## DEEP metres down.

const DEEP := -26.0

var _water: Node


func height_at(x: float, z: float) -> float:
	var best := DEEP
	for island in get_tree().get_nodes_in_group("island"):
		var h: float = island.height_or_nan(x, z)
		if not is_nan(h):
			best = maxf(best, h)
	return best


func surface_at(pos: Vector3) -> float:
	if _water == null or not is_instance_valid(_water):
		_water = get_tree().get_first_node_in_group("water")
	return _water.surface_height_at(pos) if _water else 0.0


func water_level() -> float:
	if _water == null or not is_instance_valid(_water):
		_water = get_tree().get_first_node_in_group("water")
	return _water.water_level() if _water else 0.0


## Metres of water above the ground at (x, z); negative on dry land.
func depth_at(x: float, z: float) -> float:
	return water_level() - height_at(x, z)


func is_land(x: float, z: float, margin: float = 0.15) -> bool:
	return height_at(x, z) > water_level() + margin


## Nearest dry spot within `radius` of `pos` (searching rings), or `pos`
## itself with y = NAN when there is none.
func find_land_near(pos: Vector3, radius: float = 6.0) -> Vector3:
	var best := Vector3(pos.x, NAN, pos.z)
	var best_d := INF
	var r := 1.0
	while r <= radius:
		for i in 16:
			var a := TAU * i / 16.0
			var x := pos.x + cos(a) * r
			var z := pos.z + sin(a) * r
			var h := height_at(x, z)
			if h > water_level() + 0.25:
				var d := Vector2(x - pos.x, z - pos.z).length()
				if d < best_d:
					best_d = d
					best = Vector3(x, h, z)
		if best_d < INF:
			return best
		r += 0.75
	return best
