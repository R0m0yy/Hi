extends Node
## Sound effects, ambience and music (autoload "AudioManager").
## Effects live in res://assets/audio/sfx/<name>.wav, optionally with
## variants <name>_1.wav, <name>_2.wav... picked at random. Missing sounds
## are ignored so gameplay never depends on audio.

const SFX_DIR := "res://assets/audio/sfx/"
const LOOP_DIR := "res://assets/audio/loops/"
const BUSES := ["Music", "SFX", "Ambience"]

var _cache := {}
var _pool3d: Array[AudioStreamPlayer3D] = []
var _pool2d: Array[AudioStreamPlayer] = []
var _loops := {}
var _rng := RandomNumberGenerator.new()
var _underwater := false
var _night := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")
	for i in 16:
		var p := AudioStreamPlayer3D.new()
		p.bus = "SFX"
		p.unit_size = 6.0
		p.max_distance = 60.0
		p.attenuation_filter_cutoff_hz = 12000.0
		add_child(p)
		_pool3d.append(p)
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_pool2d.append(p)


func _variants(name: String) -> Array:
	if _cache.has(name):
		return _cache[name]
	var out := []
	for path in [SFX_DIR + name + ".wav"]:
		if ResourceLoader.exists(path):
			out.append(load(path))
	for i in range(1, 6):
		var path := "%s%s_%d.wav" % [SFX_DIR, name, i]
		if ResourceLoader.exists(path):
			out.append(load(path))
	_cache[name] = out
	return out


## Plays a one-shot. With a position it is spatial; otherwise it is UI-level.
func play(name: String, pos = null, volume_db: float = 0.0, pitch_jitter: float = 0.08) -> void:
	var vars := _variants(name)
	if vars.is_empty():
		return
	var stream: AudioStream = vars[_rng.randi() % vars.size()]
	var pitch := 1.0 + _rng.randf_range(-pitch_jitter, pitch_jitter)
	if pos is Vector3:
		var p := _free3d()
		p.stream = stream
		p.global_position = pos
		p.volume_db = volume_db
		p.pitch_scale = pitch
		p.play()
	else:
		var p := _free2d()
		p.stream = stream
		p.volume_db = volume_db
		p.pitch_scale = pitch
		p.play()


func _free3d() -> AudioStreamPlayer3D:
	for p in _pool3d:
		if not p.playing:
			return p
	return _pool3d[_rng.randi() % _pool3d.size()]


func _free2d() -> AudioStreamPlayer:
	for p in _pool2d:
		if not p.playing:
			return p
	return _pool2d[0]


## Starts (or retargets the volume of) a looping track by name.
func set_loop(name: String, volume_db: float, bus: String = "Ambience", fade: float = 1.5) -> void:
	var path := LOOP_DIR + name + ".ogg"
	if not ResourceLoader.exists(path):
		path = LOOP_DIR + name + ".wav"
	if not ResourceLoader.exists(path):
		return
	var p: AudioStreamPlayer = _loops.get(name)
	if p == null:
		p = AudioStreamPlayer.new()
		p.bus = bus
		p.stream = AudioUtil.looped(load(path))
		p.volume_db = -60.0
		add_child(p)
		_loops[name] = p
		p.play()
	var tw := create_tween()
	tw.tween_property(p, "volume_db", volume_db, fade)


## Muffles effects and swaps the ambience while the player's head is underwater.
func set_underwater(on: bool) -> void:
	if on == _underwater:
		return
	_underwater = on
	var i := AudioServer.get_bus_index("SFX")
	if i >= 0:
		if AudioServer.get_bus_effect_count(i) == 0:
			var lp := AudioEffectLowPassFilter.new()
			lp.cutoff_hz = 900.0
			AudioServer.add_bus_effect(i, lp)
		AudioServer.set_bus_effect_enabled(i, 0, on)
	set_loop("ocean", -22.0 if on else -6.0, "Ambience", 0.6)
	set_loop("underwater", -4.0 if on else -60.0, "Ambience", 0.6)
	_apply_ambience(0.6)


## 0 = day (wind), 1 = night (crickets). DayNight calls this every frame.
func set_night(amount: float) -> void:
	amount = clampf(amount, 0.0, 1.0)
	if absf(amount - _night) < 0.02:
		return
	_night = amount
	_apply_ambience(0.5)


## Starts or re-levels the wind and night loops for the current state.
func refresh_ambience() -> void:
	_apply_ambience(1.5)


func _apply_ambience(fade: float) -> void:
	set_loop("wind", -40.0 if _underwater else lerpf(-16.0, -26.0, _night), "Ambience", fade)
	set_loop("night", -60.0 if _underwater else lerpf(-60.0, -13.0, sqrt(_night)), "Ambience", fade)


func _exit_tree() -> void:
	# Release looping streams so nothing is left playing when the game quits.
	for name in _loops:
		var p: AudioStreamPlayer = _loops[name]
		p.stop()
		p.stream = null
	_loops.clear()
	for p in _pool3d:
		p.stop()
		p.stream = null
	for p in _pool2d:
		p.stop()
		p.stream = null


func stop_loop(name: String, fade: float = 1.0) -> void:
	var p: AudioStreamPlayer = _loops.get(name)
	if p:
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -60.0, fade)


func set_bus_volume(bus: String, linear: float) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i >= 0:
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(linear, 0.0001)))
		AudioServer.set_bus_mute(i, linear <= 0.001)
