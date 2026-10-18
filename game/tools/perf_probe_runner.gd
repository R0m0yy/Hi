extends Node
## See perf_probe.gd.


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	Game.reset()
	Game.pending_start = "new"
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await _frames(30)
	var world: GameWorld = get_tree().current_scene
	var player := world.player
	print("perf_probe: view, draw calls, primitives, objects, video MiB, process ms, physics ms")
	await _probe("camp (start)")
	player.teleport(Vector3(40.0, 0.0, 22.0), 90.0)
	await _frames(40)
	await _probe("swimming offshore")
	world.camera.zoom_size = world.camera.max_size * 0.5
	await _frames(40)
	await _probe("zoomed out (55 m)")
	world.camera.zoom_size = GameWorld.DEFAULT_ZOOM
	player.teleport(Vector3(175.0, 2.0, -140.0), 0.0)
	await _frames(40)
	await _probe("Palm Key")
	get_tree().quit()


func _probe(label: String) -> void:
	await _frames(5)
	var rs := RenderingServer
	print("perf_probe: %s, %d, %d, %d, %.0f, %.2f, %.2f" % [
		label,
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		rs.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576.0,
		Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
		Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
	])


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
