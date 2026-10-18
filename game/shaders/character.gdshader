// The player character: smooth vertex-colour shading with a soft
// "clay toy" look (wrap lighting via Burley diffuse, gentle rim light),
// plus caustics when underwater. Vertex colour RGB = linear albedo.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/include/world_common.gdshaderinc"

uniform float roughness_value : hint_range(0.0, 1.0) = 0.62;
uniform float specular_value : hint_range(0.0, 1.0) = 0.32;
uniform float rim_amount : hint_range(0.0, 1.0) = 0.35;
uniform float saturation_boost : hint_range(0.0, 0.5) = 0.06;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 albedo = COLOR.rgb;
	float l = dot(albedo, vec3(0.299, 0.587, 0.114));
	albedo = clamp(mix(vec3(l), albedo, 1.0 + saturation_boost), 0.0, 1.0);
	float caus = pu_caustics(world_pos, TIME);
	albedo += albedo * caus * 2.0;
	ALBEDO = albedo;
	ROUGHNESS = roughness_value;
	SPECULAR = specular_value;
	RIM = rim_amount;
	RIM_TINT = 0.55;
	// Underwater, a soft aqua edge glow keeps the explorer readable from above.
	float under = smoothstep(0.2, 0.9, water_level - world_pos.y);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
	EMISSION = vec3(0.55, 0.95, 1.0) * fres * under * 0.45 + albedo * under * 0.12;
}
