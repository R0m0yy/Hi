class_name CompassArrow
extends Control
## A small arrow pointing in screen space (0 = up), used by the HUD compass.

var angle := 0.0


func _draw() -> void:
	var c := size * 0.5
	var r := minf(size.x, size.y) * 0.5
	draw_circle(c, r, Color(0, 0, 0, 0.3))
	var dir := Vector2(sin(angle), -cos(angle))
	var side := Vector2(-dir.y, dir.x)
	var pts := PackedVector2Array([c + dir * r * 0.8, c - dir * r * 0.45 + side * r * 0.45, c - dir * r * 0.2, c - dir * r * 0.45 - side * r * 0.45])
	draw_colored_polygon(pts, UITheme.ACCENT)
