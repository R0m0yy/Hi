// Shared helpers for every world shader: global uniforms, hash noise,
// stylised caustics and the wind sway function.

global uniform float water_level;
global uniform vec2 wind_direction;
global uniform float wind_strength;
global uniform float caustics_strength;
// 1 at full day, ~0.25 at night (DayNight).
global uniform float daylight;

// Colour space. Forward+ computes in linear space and converts `source_color`
// uniforms itself. The Compatibility renderer (the browser build) instead hands
// uniforms and the screen texture to shaders as sRGB and expects ALBEDO and
// EMISSION back as sRGB. pu_lin() and pu_out() make both renderers compute in
// linear space, so one set of shaders gives the same picture on either.
vec3 pu_lin(vec3 c) {
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	vec3 hi = pow((max(c, vec3(0.0)) + 0.055) / 1.055, vec3(2.4));
	return mix(hi, c / 12.92, step(c, vec3(0.04045)));
#else
	return c;
#endif
}

vec3 pu_out(vec3 c) {
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
	c = max(c, vec3(0.0));
	vec3 hi = 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055;
	return mix(hi, c * 12.92, step(c, vec3(0.0031308)));
#else
	return c;
#endif
}

float pu_hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float pu_value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = pu_hash(i);
	float b = pu_hash(i + vec2(1.0, 0.0));
	float c = pu_hash(i + vec2(0.0, 1.0));
	float d = pu_hash(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float pu_hash3(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.x + p.y) * p.z);
}

float pu_value_noise3(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float n000 = pu_hash3(i);
	float n100 = pu_hash3(i + vec3(1.0, 0.0, 0.0));
	float n010 = pu_hash3(i + vec3(0.0, 1.0, 0.0));
	float n110 = pu_hash3(i + vec3(1.0, 1.0, 0.0));
	float n001 = pu_hash3(i + vec3(0.0, 0.0, 1.0));
	float n101 = pu_hash3(i + vec3(1.0, 0.0, 1.0));
	float n011 = pu_hash3(i + vec3(0.0, 1.0, 1.0));
	float n111 = pu_hash3(i + vec3(1.0, 1.0, 1.0));
	return mix(mix(mix(n000, n100, u.x), mix(n010, n110, u.x), u.y),
			mix(mix(n001, n101, u.x), mix(n011, n111, u.x), u.y), u.z);
}

float pu_fbm(vec2 p) {
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 4; i++) {
		v += a * pu_value_noise(p);
		p = p * 2.03 + vec2(17.1, 9.7);
		a *= 0.5;
	}
	return v;
}

// Tileable caustic network (iterated domain warp). uv tiles every 1.0.
float pu_caustic_layer(vec2 uv, float t) {
	vec2 p = mod(uv * 6.28318, 6.28318) - 250.0;
	vec2 i = p;
	float c = 1.0;
	float inten = 0.005;
	for (int n = 0; n < 4; n++) {
		float tt = t * (1.0 - (3.5 / float(n + 1)));
		i = p + vec2(cos(tt - i.x) + sin(tt + i.y), sin(tt - i.y) + cos(tt + i.x));
		c += 1.0 / length(vec2(p.x / (sin(i.x + tt) / inten), p.y / (cos(i.y + tt) / inten)));
	}
	c /= 4.0;
	c = 1.17 - pow(c, 1.4);
	return clamp(pow(abs(c), 8.0), 0.0, 1.0);
}

// Caustic light for a world-space point. Returns 0 above the water.
float pu_caustics(vec3 world_pos, float time) {
	float depth = water_level - world_pos.y;
	if (depth <= -0.05) {
		return 0.0;
	}
	vec2 uv = world_pos.xz / 7.0;
	float c = pu_caustic_layer(uv, time * 0.55);
	c = max(c, pu_caustic_layer(uv * 1.37 + vec2(0.31, 0.17), time * 0.43) * 0.8);
	float fade_in = smoothstep(-0.05, 0.2, depth);
	float fade_out = exp(-max(depth, 0.0) * 0.18);
	return c * fade_in * fade_out * caustics_strength;
}

// Wind sway in model space. height_norm: how far up the plant this vertex is (0..1+).
vec3 pu_wind_offset(vec3 vertex, float flex, mat4 model, float time, float sway, float flutter) {
	vec3 origin = (model * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float phase = dot(origin.xz, vec2(0.131, 0.173));
	vec3 wdir = normalize((vec4(wind_direction.x, 0.0, wind_direction.y, 0.0) * model).xyz + vec3(1e-4));
	float h = max(vertex.y, 0.0) / 8.0;
	float gust = sin(time * 1.05 + phase) * 0.65 + sin(time * 2.31 + phase * 1.7) * 0.25 + 0.35;
	vec3 offset = wdir * (h * h) * gust * sway * wind_strength;
	float f = flex * flex;
	offset.y += sin(time * 3.7 + phase * 3.0 + vertex.x * 1.3 + vertex.z * 1.1) * f * flutter * 0.12 * wind_strength;
	offset += wdir * sin(time * 2.9 + phase * 2.0 + vertex.y * 0.7) * f * flutter * 0.06 * wind_strength;
	return offset;
}
