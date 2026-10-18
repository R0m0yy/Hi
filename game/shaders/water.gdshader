// Stylised tropical ocean (art bible §3 "Water colour ramp").
//
// * Water depth comes from the depth buffer: the vertical distance between
//   the surface and the seabed behind each pixel. It drives the
//   clear -> turquoise -> teal -> ocean -> deep colour ramp.
// * The real seabed (with its caustics and shadows) is refracted from the
//   screen texture and fades out with depth (clarity).
// * Foam: a crisp shoreline band that washes in and out (Ref B), broken
//   wave lines travelling toward the shore, and white sun glints on open
//   water (Ref A).
shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/include/world_common.gdshaderinc"

// Gameplay: a clear "window" around a diving player so they stay readable.
global uniform vec3 diver_pos;
global uniform float diver_reveal;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform sampler2D normal_a : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_b : hint_normal, filter_linear_mipmap, repeat_enable;

uniform vec4 color_shallow : source_color = vec4(0.55, 0.88, 0.78, 1.0);
uniform vec4 color_turquoise : source_color = vec4(0.31, 0.84, 0.82, 1.0);
uniform vec4 color_teal : source_color = vec4(0.12, 0.65, 0.75, 1.0);
uniform vec4 color_ocean : source_color = vec4(0.08, 0.41, 0.71, 1.0);
uniform vec4 color_deep : source_color = vec4(0.04, 0.24, 0.49, 1.0);
uniform vec4 foam_color : source_color = vec4(1.0, 0.973, 0.89, 1.0);
uniform float body_brightness = 0.5;
uniform float clarity_falloff = 0.62;
uniform float transmission_tint = 0.75;
uniform float refraction_strength = 0.02;
uniform float normal_scale_a = 0.035;
uniform float normal_scale_b = 0.071;
uniform vec2 normal_speed_a = vec2(0.010, 0.006);
uniform vec2 normal_speed_b = vec2(-0.007, 0.009);
uniform float normal_strength = 0.6;
uniform float wave_height = 0.05;
uniform float shore_foam_width = 0.16;
uniform float wave_foam_strength = 1.0;
uniform float glint_strength = 1.0;
uniform float roughness_value = 0.22;

varying vec3 world_vertex;

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	float h = sin(w.x * 0.21 + t * 0.9) * 0.5 + sin(w.z * 0.17 - t * 0.7) * 0.35
			+ sin((w.x + w.z) * 0.33 + t * 1.3) * 0.15;
	VERTEX.y += h * wave_height;
	world_vertex = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

vec3 scene_world_pos(vec2 uv, mat4 inv_proj, mat4 inv_view) {
	float d = texture(depth_tex, uv).r;
	vec4 v = inv_proj * vec4(uv * 2.0 - 1.0, d, 1.0);
	v.xyz /= v.w;
	return (inv_view * vec4(v.xyz, 1.0)).xyz;
}

void fragment() {
	vec2 wp = world_vertex.xz;
	vec3 na = texture(normal_a, wp * normal_scale_a + TIME * normal_speed_a).rgb;
	vec3 nb = texture(normal_b, wp * normal_scale_b + TIME * normal_speed_b).rgb;
	vec3 nmix = mix(na, nb, 0.5);
	NORMAL_MAP = nmix;
	NORMAL_MAP_DEPTH = normal_strength;
	vec2 ripple = (nmix.xy * 2.0 - 1.0);

	vec3 floor_pos = scene_world_pos(SCREEN_UV, INV_PROJECTION_MATRIX, INV_VIEW_MATRIX);
	float depth = max(world_vertex.y - floor_pos.y, 0.0);

	// Refract only toward pixels that are themselves underwater.
	vec2 ruv = SCREEN_UV + ripple * refraction_strength * clamp(depth * 0.7, 0.0, 1.0);
	vec3 rfloor = scene_world_pos(ruv, INV_PROJECTION_MATRIX, INV_VIEW_MATRIX);
	if (rfloor.y > world_vertex.y) {
		ruv = SCREEN_UV;
		rfloor = floor_pos;
	}
	float rdepth = max(world_vertex.y - rfloor.y, 0.0);
	vec3 refr = textureLod(screen_tex, ruv, 0.0).rgb;

	vec3 body = mix(color_shallow.rgb, color_turquoise.rgb, smoothstep(0.0, 1.4, rdepth));
	body = mix(body, color_teal.rgb, smoothstep(1.2, 4.5, rdepth));
	body = mix(body, color_ocean.rgb, smoothstep(4.0, 10.0, rdepth));
	body = mix(body, color_deep.rgb, smoothstep(10.0, 18.0, rdepth));

	float clarity = exp(-rdepth * clarity_falloff);
	float reveal = diver_reveal * (1.0 - smoothstep(2.5, 7.5, distance(world_vertex.xz, diver_pos.xz)));
	clarity = mix(clarity, max(clarity, exp(-rdepth * clarity_falloff * 0.22)), reveal);
	vec3 tint = mix(vec3(1.0), color_turquoise.rgb * 1.25, transmission_tint * smoothstep(0.0, 1.1, rdepth));
	vec3 transmitted = refr * tint;

	// Shoreline foam: thin crisp band that washes in and out.
	float n1 = pu_fbm(wp * 0.35 + vec2(TIME * 0.05, 0.0));
	// Crisp cream line hugging the shore (Ref B), anti-aliased with fwidth.
	float wash = shore_foam_width * (0.75 + 0.35 * sin(TIME * 1.1 + n1 * 6.0));
	float shore_d = depth + (n1 - 0.5) * 0.05;
	float aa = max(fwidth(shore_d), 0.004);
	float shore_foam = 1.0 - smoothstep(wash - aa, wash + aa, shore_d);
	// Broken wave lines travelling toward the beach.
	float phase = depth * 1.4 - TIME * 0.22 + n1 * 0.8;
	float f = fract(phase);
	float faa = max(fwidth(phase), 0.002);
	float band = smoothstep(0.93 - faa, 0.93 + faa, f) * (1.0 - smoothstep(0.965 - faa, 0.965 + faa, f));
	float band_mask = smoothstep(wash, wash + 0.3, depth) * (1.0 - smoothstep(0.7, 1.4, depth));
	band_mask *= smoothstep(0.52, 0.66, pu_fbm(wp * 0.13 + vec2(7.0, TIME * 0.03)));
	float foam = clamp(max(shore_foam, band * band_mask * wave_foam_strength), 0.0, 1.0) * (1.0 - reveal * 0.6);

	// Sun glints on open water (Ref A's white flecks).
	// Clustered in slowly drifting patches so open water reads calm, not noisy.
	float patch = smoothstep(0.58, 0.75, pu_fbm(wp * 0.015 + vec2(TIME * 0.006, -TIME * 0.004)));
	float g1 = pu_value_noise(wp * vec2(2.2, 3.4) + TIME * vec2(0.31, 0.17));
	float g2 = pu_value_noise(wp * vec2(2.9, 2.1) - TIME * vec2(0.23, 0.29) + 3.1);
	float glint = smoothstep(0.74, 0.8, g1 * g2 * 1.55) * patch * smoothstep(1.5, 4.0, depth) * glint_strength;
	glint *= 1.0 - smoothstep(60.0, 140.0, length(VERTEX));  // sparkles are a close-up detail
	glint *= 1.0 - reveal;

	ALBEDO = mix(body * body_brightness * (1.0 - clarity), foam_color.rgb, foam);
	EMISSION = transmitted * clarity * (1.0 - foam) + foam_color.rgb * (foam * 0.3 + glint * 0.6);
	ROUGHNESS = mix(roughness_value, 0.9, foam);
	SPECULAR = 0.18;
	ALPHA = 1.0;
}
