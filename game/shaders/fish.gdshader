// Swimming fish: vertex colour albedo, body wave toward the tail.
// Vertex alpha = wave weight (0 at the head, 1 at the tail tip).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/include/world_common.gdshaderinc"

uniform float wave_amplitude = 0.045;
uniform float wave_frequency = 11.0;
uniform float sheen : hint_range(0.0, 1.0) = 0.35;
// Set per fish through a private copy of the material. (Instance uniforms
// would be tidier, but the Compatibility renderer caps how many instances
// may use them, and the browser build runs on it.)
uniform float swim_phase = 0.0;
uniform float swim_rate = 1.0;

varying vec3 world_pos;

void vertex() {
	float w = COLOR.a;
	float t = TIME * 10.0 * swim_rate + swim_phase;
	float amp = wave_amplitude * (0.55 + 0.45 * clamp(swim_rate, 0.0, 2.0));
	VERTEX.x += sin(t - VERTEX.z * wave_frequency) * amp * w;
	// The whole body yaws gently against the tail.
	VERTEX.x += sin(t - 1.2) * amp * 0.25 * (1.0 - w) * sign(VERTEX.z);
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 albedo = COLOR.rgb;
	float caus = pu_caustics(world_pos, TIME);
	albedo += albedo * caus * 2.0;
	if (!FRONT_FACING) {
		albedo *= 0.8;
	}
	ALBEDO = pu_out(albedo);
	ROUGHNESS = 0.38;
	SPECULAR = 0.5 * sheen + 0.2;
	RIM = 0.25;
	RIM_TINT = 0.6;
}
