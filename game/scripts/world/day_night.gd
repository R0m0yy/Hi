class_name DayNight
extends Node
## Drives the daylight rig from Game.time_hours: the sun climbs and swings
## through the day, warms at dawn and dusk, and hands over to a cool
## moonlight at night. Between 07:00 and 17:00 the rig keeps its art-directed
## look (the sun's authored elevation, colour and energy). The `daylight`
## shader global (1 = full day, ~0.25 = night) dims caustics, foam and glints.

const NIGHT_LEVEL := 0.25
## Sunrise and sunset: the sun is the key light between these hours.
const SUNRISE := 5.6
const SUNSET := 19.2

## hour -> look. Interpolated linearly, wrapping at midnight.
const KEYS := [
	{"h": 0.0, "look": "night"},
	{"h": 4.8, "look": "night"},
	{"h": 6.0, "look": "dawn"},
	{"h": 7.2, "look": "day"},
	{"h": 17.0, "look": "day"},
	{"h": 18.4, "look": "dusk"},
	{"h": 19.6, "look": "night"},
	{"h": 24.0, "look": "night"},
]

const LOOKS := {
	"dawn": {
		"energy": 1.1, "color": Color(1.0, 0.82, 0.7),
		"ambient": Color(0.74, 0.66, 0.86), "ambient_energy": 0.8,
		"sky_top": Color(0.38, 0.5, 0.8), "sky_horizon": Color(0.98, 0.78, 0.66),
		"daylight": 0.7, "saturation": 1.08, "exposure": 0.95, "shadow": 0.6,
	},
	"dusk": {
		"energy": 1.2, "color": Color(1.0, 0.78, 0.6),
		"ambient": Color(0.76, 0.64, 0.8), "ambient_energy": 0.8,
		"sky_top": Color(0.34, 0.4, 0.72), "sky_horizon": Color(1.0, 0.7, 0.54),
		"daylight": 0.7, "saturation": 1.05, "exposure": 0.95, "shadow": 0.6,
	},
	"night": {
		"energy": 0.34, "color": Color(0.64, 0.76, 1.0),
		"ambient": Color(0.25, 0.33, 0.62), "ambient_energy": 0.42,
		"sky_top": Color(0.03, 0.06, 0.16), "sky_horizon": Color(0.08, 0.13, 0.26),
		"daylight": NIGHT_LEVEL, "saturation": 0.82, "exposure": 0.9, "shadow": 0.4,
	},
}

@export var rig_path: NodePath

var _sun: DirectionalLight3D
var _env: Environment
var _sky: ProceduralSkyMaterial
var _day := {}
var _sun_az := 0.0
var _sun_el := 0.0
var _caustics := 1.0
## The Compatibility renderer (browser build) has no SSAO and lights a little
## brighter, so its exposure is trimmed to match the desktop look.
var _exposure_scale := 1.0


func _ready() -> void:
	var rig := get_node_or_null(rig_path)
	if rig == null:
		push_warning("DayNight: no daylight rig")
		return
	_sun = rig.get_node("Sun") as DirectionalLight3D
	var we := rig.get_node("WorldEnvironment") as WorldEnvironment
	# A private copy so the shared resource on disk (and in lookdev scenes) is untouched.
	_env = we.environment.duplicate(true)
	we.environment = _env
	_sky = _env.sky.sky_material as ProceduralSkyMaterial
	if RenderingServer.get_current_rendering_method() == "gl_compatibility":
		_exposure_scale = 0.9
	var to_sun := _sun.global_basis.z.normalized()
	_sun_el = asin(to_sun.y)
	_sun_az = atan2(to_sun.x, to_sun.z)
	var caus = ProjectSettings.get_setting("shader_globals/caustics_strength", {})
	_caustics = float(caus.get("value", 1.0)) if caus is Dictionary else 1.0
	_day = {
		"energy": _sun.light_energy, "color": _sun.light_color,
		"ambient": _env.ambient_light_color, "ambient_energy": _env.ambient_light_energy,
		"sky_top": _sky.sky_top_color, "sky_horizon": _sky.sky_horizon_color,
		"daylight": 1.0, "saturation": _env.adjustment_saturation,
		"exposure": _env.tonemap_exposure, "shadow": _sun.shadow_opacity,
	}
	apply(Game.time_hours)


func _process(_delta: float) -> void:
	if _sun:
		apply(Game.time_hours)


## Sets every light, sky and shader global for `hour` (0..24).
func apply(hour: float) -> void:
	var look := sample(hour)
	_sun.light_color = look["color"]
	_sun.light_energy = look["energy"] * _handover(hour)
	_env.ambient_light_color = look["ambient"]
	_env.ambient_light_energy = look["ambient_energy"]
	_env.adjustment_saturation = look["saturation"]
	_env.tonemap_exposure = look["exposure"] * _exposure_scale
	_sun.shadow_opacity = look["shadow"]
	_sky.sky_top_color = look["sky_top"]
	_sky.sky_horizon_color = look["sky_horizon"]
	_sky.ground_horizon_color = (look["sky_horizon"] as Color).lerp(Color(0.58, 0.8, 0.9), 0.5)
	var daylight: float = look["daylight"]
	RenderingServer.global_shader_parameter_set("daylight", daylight)
	RenderingServer.global_shader_parameter_set("caustics_strength", _caustics * smoothstep(NIGHT_LEVEL, 1.0, daylight))
	_sun.global_basis = _light_basis(hour)
	if Game.is_playing():
		AudioManager.set_night(1.0 - smoothstep(NIGHT_LEVEL, 1.0, daylight))


## The blended look at `hour` as a Dictionary of the LOOKS fields.
func sample(hour: float) -> Dictionary:
	hour = fposmod(hour, 24.0)
	for i in KEYS.size() - 1:
		var a: Dictionary = KEYS[i]
		var b: Dictionary = KEYS[i + 1]
		if hour <= b["h"]:
			var t := inverse_lerp(a["h"], b["h"], hour)
			return _mix(_look(a["look"]), _look(b["look"]), t)
	return _look("night")


func _look(name: String) -> Dictionary:
	return _day if name == "day" else LOOKS[name]


func _mix(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var out := {}
	for k in a:
		if a[k] is Color:
			out[k] = (a[k] as Color).lerp(b[k], t)
		else:
			out[k] = lerpf(a[k], b[k], t)
	return out


## Dims the key light briefly around sunrise and sunset, when it swaps
## between the sun and the moon, so the shadow jump is not visible.
func _handover(hour: float) -> float:
	var d := minf(absf(hour - SUNRISE), absf(hour - SUNSET))
	return smoothstep(0.0, 0.4, d)


func _light_basis(hour: float) -> Basis:
	var el: float
	var az: float
	if hour >= SUNRISE and hour <= SUNSET:
		var s := inverse_lerp(SUNRISE, SUNSET, hour)
		var rise := smoothstep(0.0, 0.12, s) * (1.0 - smoothstep(0.86, 1.0, s))
		el = lerpf(deg_to_rad(7.0), _sun_el, rise)
		# Authored azimuth at the start of a new game (07:30), drifting west.
		az = _sun_az + (s - 0.14) * deg_to_rad(60.0)
	else:
		el = deg_to_rad(55.0)
		az = _sun_az + PI * 0.8
	var to_light := Vector3(sin(az) * cos(el), sin(el), cos(az) * cos(el))
	return Basis.looking_at(-to_light, Vector3.UP)
