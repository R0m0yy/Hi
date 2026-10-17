// Two-sided stylised vertex-colour surface (palm fronds, leaves, cloth).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_burley, specular_schlick_ggx;

#define TWO_SIDED
#include "res://shaders/include/stylized_vc_body.gdshaderinc"
