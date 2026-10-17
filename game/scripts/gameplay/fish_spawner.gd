class_name FishSpawner
extends RefCounted
## Places fish schools around an island by water depth: snapper in the
## shallows, tang over the reef, mackerel and the odd grouper in deep water.
## Deterministic per island so every run looks the same.

## species, schools, fish per school, depth band (m)
const PLAN := [
	["snapper", 4, 8, Vector2(1.2, 3.8)],
	["tang", 4, 7, Vector2(2.5, 7.5)],
	["mackerel", 3, 9, Vector2(7.0, 21.0)],
	["grouper", 3, 1, Vector2(9.0, 23.0)],
]


static func spawn_for(island: Node3D, parent: Node3D, seed_value: int, preferred: Array = []) -> int:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var centres: Array[Vector3] = []
	var made_total := 0
	var origin := island.global_position
	for plan in PLAN:
		var species: String = plan[0]
		var band: Vector2 = plan[3]
		var made := 0
		var tries := 0
		var candidates := preferred.duplicate() if species == "snapper" else []
		while made < int(plan[1]) and tries < 600:
			tries += 1
			var x: float
			var z: float
			if not candidates.is_empty():
				var c: Vector2 = candidates.pop_front()
				x = c.x
				z = c.y
			else:
				var a := rng.randf() * TAU
				var r := rng.randf_range(14.0, 100.0)
				x = origin.x + cos(a) * r
				z = origin.z + sin(a) * r
			var depth := World.depth_at(x, z)
			if depth < band.x or depth > band.y:
				continue
			var pos := Vector3(x, World.water_level() - minf(depth * 0.5, 4.0), z)
			var clash := false
			for c in centres:
				if c.distance_to(pos) < 13.0:
					clash = true
					break
			if clash:
				continue
			var school := FishSchool.new()
			school.name = "%s_%s_%d" % [island.name, species, made]
			school.species = species
			school.count = int(plan[2])
			school.home_radius = 5.0 if species == "snapper" else 8.0
			school.position = pos - parent.global_position  # before _ready, which spawns the fish
			parent.add_child(school)
			centres.append(pos)
			made += 1
			made_total += school.count
	return made_total
