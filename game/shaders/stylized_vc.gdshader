// Single-sided stylised vertex-colour surface (rocks, wood, props, trunks).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/include/stylized_vc_body.gdshaderinc"
