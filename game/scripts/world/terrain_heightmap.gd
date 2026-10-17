class_name TerrainHeightmap
extends RefCounted
## Height samples exported by tools/blender/assets_terrain.py (float32,
## row-major z * width + x, `spacing` metres apart, starting at `origin`).
## Used for collision (HeightMapShape3D) and gameplay queries such as
## "how deep is the water here?".

var width := 0
var depth := 0
var spacing := 1.0
var origin := Vector2.ZERO
var data := PackedFloat32Array()


static func load_from(json_path: String) -> TerrainHeightmap:
	var meta = JSON.parse_string(FileAccess.get_file_as_string(json_path))
	if not (meta is Dictionary):
		push_error("TerrainHeightmap: cannot read %s" % json_path)
		return null
	var hm := TerrainHeightmap.new()
	hm.width = int(meta["width"])
	hm.depth = int(meta["depth"])
	hm.spacing = float(meta["spacing"])
	hm.origin = Vector2(meta["origin"][0], meta["origin"][1])
	var bytes := FileAccess.get_file_as_bytes(json_path.get_basename() + ".bin")
	hm.data = bytes.to_float32_array()
	if hm.data.size() != hm.width * hm.depth:
		push_error("TerrainHeightmap: %s has %d samples, expected %d" % [json_path, hm.data.size(), hm.width * hm.depth])
		return null
	return hm


## True when (x, z) in the heightmap's own space lies inside the sampled area.
func contains(x: float, z: float) -> bool:
	return x >= origin.x and z >= origin.y \
			and x <= origin.x + (width - 1) * spacing and z <= origin.y + (depth - 1) * spacing


## Bilinear terrain height at world XZ.
func height_at(x: float, z: float) -> float:
	var fx := clampf((x - origin.x) / spacing, 0.0, width - 1.001)
	var fz := clampf((z - origin.y) / spacing, 0.0, depth - 1.001)
	var ix := int(fx)
	var iz := int(fz)
	var tx := fx - ix
	var tz := fz - iz
	var i := iz * width + ix
	var h0 := lerpf(data[i], data[i + 1], tx)
	var h1 := lerpf(data[i + width], data[i + width + 1], tx)
	return lerpf(h0, h1, tz)


## Collision shape; place it at `shape_center()` with scale (spacing, 1, spacing).
func make_shape() -> HeightMapShape3D:
	var shape := HeightMapShape3D.new()
	shape.map_width = width
	shape.map_depth = depth
	shape.map_data = data
	return shape


func shape_center() -> Vector3:
	return Vector3(origin.x + (width - 1) * spacing * 0.5, 0.0, origin.y + (depth - 1) * spacing * 0.5)
