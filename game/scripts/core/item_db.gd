extends Node
## Item, recipe and fish definitions (autoload "ItemDB").
## kind: resource | food | tool | placeable
## Food values restore stats; negative values hurt (raw fish).

const ICON_DIR := "res://assets/icons/"
const MODEL_DIR := "res://assets/models/items/"

const ITEMS := {
	"wood": {"name": "Wood", "kind": "resource", "stack": 40, "color": Color("a8693f"),
		"desc": "Driftwood and palm branches. The base of almost everything."},
	"stone": {"name": "Stone", "kind": "resource", "stack": 40, "color": Color("8d8290"),
		"desc": "Lavender-grey stone, good for tool heads and fire rings."},
	"fiber": {"name": "Plant Fiber", "kind": "resource", "stack": 40, "color": Color("8fbf5a"),
		"desc": "Tough leaf fibre from bushes and beach grass. Twist it into rope."},
	"palm_frond": {"name": "Palm Frond", "kind": "resource", "stack": 20, "color": Color("5f9e4a"),
		"desc": "Big leaves for roofs and sails."},
	"shell": {"name": "Shell", "kind": "resource", "stack": 20, "color": Color("f1d9c4"),
		"desc": "A sturdy shell. Makes a fine fish hook."},
	"rope": {"name": "Rope", "kind": "resource", "stack": 20, "color": Color("d8be8a"),
		"desc": "Twisted fibre rope for lashings."},
	"coconut": {"name": "Coconut", "kind": "food", "stack": 10, "color": Color("7a4a2a"),
		"food": 12.0, "water": 28.0, "desc": "Sweet water and flesh. Restores thirst."},
	"fish_snapper_raw": {"name": "Raw Sunny Snapper", "kind": "food", "stack": 10, "color": Color("f2a33a"),
		"food": 8.0, "health": -4.0, "cooks_to": "fish_snapper_cooked", "desc": "Cook it before eating."},
	"fish_tang_raw": {"name": "Raw Blue Tang", "kind": "food", "stack": 10, "color": Color("3f7fe0"),
		"food": 8.0, "health": -4.0, "cooks_to": "fish_tang_cooked", "desc": "Cook it before eating."},
	"fish_mackerel_raw": {"name": "Raw Silver Mackerel", "kind": "food", "stack": 10, "color": Color("9fb6c8"),
		"food": 10.0, "health": -4.0, "cooks_to": "fish_mackerel_cooked", "desc": "Cook it before eating."},
	"fish_grouper_raw": {"name": "Raw Coral Grouper", "kind": "food", "stack": 10, "color": Color("d9475a"),
		"food": 14.0, "health": -4.0, "cooks_to": "fish_grouper_cooked", "desc": "A rare catch from deep water."},
	"fish_snapper_cooked": {"name": "Grilled Snapper", "kind": "food", "stack": 10, "color": Color("c9773a"),
		"food": 34.0, "health": 6.0, "desc": "Smoky and filling."},
	"fish_tang_cooked": {"name": "Grilled Tang", "kind": "food", "stack": 10, "color": Color("b9783f"),
		"food": 30.0, "health": 6.0, "desc": "Smoky and filling."},
	"fish_mackerel_cooked": {"name": "Grilled Mackerel", "kind": "food", "stack": 10, "color": Color("a8794a"),
		"food": 40.0, "health": 8.0, "desc": "Rich and filling."},
	"fish_grouper_cooked": {"name": "Grilled Grouper", "kind": "food", "stack": 10, "color": Color("b8573f"),
		"food": 55.0, "health": 15.0, "desc": "A feast."},
	"hatchet": {"name": "Stone Hatchet", "kind": "tool", "stack": 1, "color": Color("9b6a43"),
		"durability": 90.0, "desc": "Chops palm wood and splits stone."},
	"spear": {"name": "Fishing Spear", "kind": "tool", "stack": 1, "color": Color("c98b5e"),
		"durability": 50.0, "desc": "Thrust at fish while swimming or diving."},
	"fishing_rod": {"name": "Fishing Rod", "kind": "tool", "stack": 1, "color": Color("b07a4a"),
		"durability": 70.0, "desc": "Hold to charge a cast, wait for the bite, then reel."},
	"campfire_kit": {"name": "Campfire", "kind": "placeable", "stack": 5, "color": Color("e07a3a"),
		"structure": "campfire", "desc": "Cook fish and warm up. Place on sand or grass."},
	"storage_kit": {"name": "Storage Chest", "kind": "placeable", "stack": 5, "color": Color("8a5a35"),
		"structure": "storage", "desc": "Stores 16 stacks."},
	"shelter_kit": {"name": "Lean-to Shelter", "kind": "placeable", "stack": 3, "color": Color("6f9a4c"),
		"structure": "shelter", "desc": "Sleep through the night and set your respawn point."},
	"raft_kit": {"name": "Raft", "kind": "placeable", "stack": 2, "color": Color("b5824f"),
		"structure": "raft", "desc": "A sailing raft. Place it in shallow water to explore."},
}

## Ordered for the crafting panel.
const RECIPES := [
	{"out": "rope", "count": 1, "in": {"fiber": 3}},
	{"out": "hatchet", "count": 1, "in": {"wood": 2, "stone": 2, "rope": 1}},
	{"out": "spear", "count": 1, "in": {"wood": 2, "stone": 1, "rope": 1}},
	{"out": "fishing_rod", "count": 1, "in": {"wood": 2, "rope": 2, "shell": 1}},
	{"out": "campfire_kit", "count": 1, "in": {"wood": 4, "stone": 4}},
	{"out": "storage_kit", "count": 1, "in": {"wood": 8, "rope": 2}},
	{"out": "shelter_kit", "count": 1, "in": {"wood": 8, "palm_frond": 6, "rope": 2}},
	{"out": "raft_kit", "count": 1, "in": {"wood": 12, "rope": 4, "palm_frond": 4}},
]

## Fish species: depth band (metres of water) where they live, weights for
## rod catches, reel difficulty, and the GLB used for the swimming fish.
const FISH := {
	"snapper": {"name": "Sunny Snapper", "item": "fish_snapper_raw", "depth": Vector2(0.8, 4.0),
		"weight": 1.0, "strength": 0.35, "speed": 1.6, "model": "res://assets/models/fish/fish_snapper.glb"},
	"tang": {"name": "Blue Tang", "item": "fish_tang_raw", "depth": Vector2(2.0, 8.0),
		"weight": 0.8, "strength": 0.45, "speed": 1.9, "model": "res://assets/models/fish/fish_tang.glb"},
	"mackerel": {"name": "Silver Mackerel", "item": "fish_mackerel_raw", "depth": Vector2(5.0, 30.0),
		"weight": 0.7, "strength": 0.6, "speed": 2.6, "model": "res://assets/models/fish/fish_mackerel.glb"},
	"grouper": {"name": "Coral Grouper", "item": "fish_grouper_raw", "depth": Vector2(8.0, 30.0),
		"weight": 0.18, "strength": 0.85, "speed": 1.3, "model": "res://assets/models/fish/fish_grouper.glb"},
}

var _icons := {}


func has(id: String) -> bool:
	return ITEMS.has(id)


func item(id: String) -> Dictionary:
	return ITEMS.get(id, {})


func display_name(id: String) -> String:
	return ITEMS.get(id, {}).get("name", id.capitalize())


func kind(id: String) -> String:
	return ITEMS.get(id, {}).get("kind", "resource")


func max_stack(id: String) -> int:
	return int(ITEMS.get(id, {}).get("stack", 1))


func max_durability(id: String) -> float:
	return float(ITEMS.get(id, {}).get("durability", 0.0))


func recipe_for(id: String) -> Dictionary:
	for r in RECIPES:
		if r["out"] == id:
			return r
	return {}


## Picks a species that lives at `depth` metres of water, weighted.
func roll_fish(depth: float, rng: RandomNumberGenerator) -> String:
	var total := 0.0
	var pool := []
	for key in FISH:
		var band: Vector2 = FISH[key]["depth"]
		if depth >= band.x and depth <= band.y:
			pool.append(key)
			total += FISH[key]["weight"]
	if pool.is_empty():
		return "snapper"
	var r := rng.randf() * total
	for key in pool:
		r -= FISH[key]["weight"]
		if r <= 0.0:
			return key
	return pool[-1]


## Baked icon (tools/bake_icons.gd) or a generated swatch if none exists yet.
func icon(id: String) -> Texture2D:
	if _icons.has(id):
		return _icons[id]
	var tex: Texture2D
	var path := ICON_DIR + id + ".png"
	if ResourceLoader.exists(path):
		tex = load(path)
	else:
		tex = _swatch(ITEMS.get(id, {}).get("color", Color.GRAY))
	_icons[id] = tex
	return tex


func model_path(id: String) -> String:
	var path := MODEL_DIR + id + ".glb"
	return path if ResourceLoader.exists(path) else ""


static func _swatch(c: Color) -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 64:
			var d := Vector2(x - 31.5, y - 31.5).length()
			var a := clampf(26.0 - d, 0.0, 1.0)
			var shade := 1.0 - (y / 64.0) * 0.25
			img.set_pixel(x, y, Color(c.r * shade, c.g * shade, c.b * shade, a))
	return ImageTexture.create_from_image(img)
