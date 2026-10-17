class_name DeathScreen
extends MenuBase
## Shown when health hits zero: wake up at the respawn point.

signal respawn_requested


func _ready() -> void:
	super._ready()
	var col := _build_frame(Vector2(760, 0), 0.75)
	col.add_child(MenuBase.header("You blacked out", "Hunger, thirst or the deep got the better of you."))
	col.add_child(UITheme.label("You wake up back at your shelter, a little worse for wear. Your pack is still with you.", 20, UITheme.INK_DIM))
	var b := MenuBase.button("Wake up", func() -> void:
		close()
		respawn_requested.emit())
	col.add_child(b)
	Game.player_died.connect(open)


func _on_open() -> void:
	panel.get_child(0).get_child(-1).grab_focus.call_deferred()
