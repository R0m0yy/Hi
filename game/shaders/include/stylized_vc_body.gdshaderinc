// Body of the stylised vertex-colour shader. Included by
// stylized_vc.gdshader (single-sided) and stylized_vc_foliage.gdshader
// (two-sided; defines TWO_SIDED before including).
//
// Vertex colour: RGB = albedo (linear), A = flex weight for wind flutter.

#include "res://shaders/include/world_common.gdshaderinc"

uniform vec4 albedo_tint : source_color = vec4(1.0);
uniform float facet_strength : hint_range(0.0, 1.0) = 0.0;
uniform float roughness_value : hint_range(0.0, 1.0) = 0.85;
uniform float specular_value : hint_range(0.0, 1.0) = 0.25;
uniform float sway_strength = 0.0;
uniform float flutter_strength = 0.0;
uniform float backface_darken : hint_range(0.0, 1.0) = 0.72;
uniform float translucency : hint_range(0.0, 1.0) = 0.0;
uniform float emission_from_albedo = 0.0;

varying vec3 world_pos;

void vertex() {
	if (sway_strength > 0.0 || flutter_strength > 0.0) {
		VERTEX += pu_wind_offset(VERTEX, COLOR.a, MODEL_MATRIX, TIME, sway_strength, flutter_strength);
	}
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 albedo = COLOR.rgb * albedo_tint.rgb;
#ifdef TWO_SIDED
	if (!FRONT_FACING) {
		albedo *= backface_darken;
	}
#endif
	if (facet_strength > 0.0) {
		vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
		if (dot(fn, VIEW) < 0.0) {
			fn = -fn;
		}
		NORMAL = normalize(mix(NORMAL, fn, facet_strength));
	}
	float caus = pu_caustics(world_pos, TIME);
	albedo += albedo * caus * 2.4 + vec3(0.55, 0.8, 0.75) * caus * 0.35;
	ALBEDO = albedo;
	ROUGHNESS = roughness_value;
	SPECULAR = specular_value;
	BACKLIGHT = albedo * translucency;
	EMISSION = albedo * emission_from_albedo;
}
