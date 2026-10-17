// Island terrain: golden faceted sand, wet waterline band, seabed, grass
// patches with a light rim, and caustics underwater (art bible §3).
// Vertex colour carries masks: R = grass, G = darkening near rocks.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/include/world_common.gdshaderinc"

uniform vec4 sand_color : source_color = vec4(0.93, 0.75, 0.48, 1.0);
uniform vec4 sand_shade_color : source_color = vec4(0.89, 0.69, 0.44, 1.0);
uniform vec4 wet_sand_color : source_color = vec4(0.788, 0.616, 0.408, 1.0);
uniform vec4 seabed_color : source_color = vec4(0.9, 0.77, 0.53, 1.0);
uniform vec4 grass_color : source_color = vec4(0.53, 0.77, 0.42, 1.0);
uniform vec4 grass_dark_color : source_color = vec4(0.33, 0.6, 0.31, 1.0);
uniform vec4 grass_rim_color : source_color = vec4(0.81, 0.9, 0.66, 1.0);
uniform vec4 dirt_tint : source_color = vec4(0.82, 0.74, 0.72, 1.0);
uniform float facet_strength : hint_range(0.0, 1.0) = 0.9;
uniform float wet_band_height = 0.4;
uniform float grass_edge_noise = 0.45;

varying vec3 world_pos;
varying vec4 masks;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	masks = COLOR;
}

void fragment() {
	vec2 p = world_pos.xz;
	float large = pu_fbm(p * 0.035);
	float fine = pu_value_noise(p * 1.7);
	vec3 col = mix(sand_shade_color.rgb, sand_color.rgb, smoothstep(0.3, 0.7, large));
	col *= 0.97 + fine * 0.06;

	float above = world_pos.y - water_level;
	float wet = 1.0 - smoothstep(0.0, wet_band_height, above + (fine - 0.5) * 0.08);
	col = mix(col, wet_sand_color.rgb, wet * 0.85);
	float under = smoothstep(0.0, -0.3, above);
	col = mix(col, seabed_color.rgb * (0.95 + fine * 0.1), under);

	float g = masks.r + (pu_fbm(p * 0.21 + 5.0) - 0.5) * grass_edge_noise + (pu_value_noise(p * 1.6) - 0.5) * 0.12;
	float grass = smoothstep(0.48, 0.51, g);
	float rim = grass * (1.0 - smoothstep(0.51, 0.57, g));
	vec3 gcol = mix(grass_dark_color.rgb, grass_color.rgb, smoothstep(0.25, 0.75, pu_fbm(p * 0.11 + 3.0)));
	gcol *= 0.96 + fine * 0.08;
	gcol = mix(gcol, grass_rim_color.rgb, rim * 0.75);
	col = mix(col, gcol, grass * (1.0 - under));

	col = mix(col, col * dirt_tint.rgb, masks.g * (1.0 - grass) * 0.6);

	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	if (dot(fn, VIEW) < 0.0) {
		fn = -fn;
	}
	NORMAL = normalize(mix(NORMAL, fn, facet_strength));

	float caus = pu_caustics(world_pos, TIME);
	col += col * caus * 2.4 + vec3(0.55, 0.8, 0.75) * caus * 0.35;

	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.5, wet * (1.0 - under));
	SPECULAR = 0.3;
}
