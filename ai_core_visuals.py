import arcade
import math
import time
from arcade.gl import geometry

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
WINDOW_TITLE = "AI Core Visual System"

# Fragment shader source handling all 3 states
FRAGMENT_SHADER = """
#version 330 core

uniform float u_time;
uniform vec2 u_resolution;
uniform int u_state; // 0=Listening, 1=Thinking, 2=Talking
uniform float u_volume; // 0.0 to 1.0

out vec4 fragColor;

// Simplex noise implementation (Ashima Arts)
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187,  // (3.0-sqrt(3.0))/6.0
                      0.366025403784439,  // 0.5*(sqrt(3.0)-1.0)
                     -0.577350269189626,  // -1.0 + 2.0 * C.x
                      0.024390243902439); // 1.0 / 41.0
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);

  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;

  i = mod289(i); // Avoid truncation effects in permutation
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
        + i.x + vec3(0.0, i1.x, 1.0 ));

  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;

  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;

  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );

  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / u_resolution.y;
    float dist = length(uv);
    
    vec3 color = vec3(0.0);
    float alpha = 1.0;

    if (u_state == 0) {
        // LISTENING: Perfect neon light orb in deep cosmic purple (#6A0DAD).
        // Rhythmic, slow 4-second sinusoidal 'breathing' scale pulse (+/- 15px) with heavy blur.
        
        // base radius ~0.2. Pulse over 4s (2pi / 4 = 1.57)
        float pulse = sin(u_time * 1.57079) * 0.02; // ~15px equivalent depending on res
        float r = 0.2 + pulse;
        
        vec3 purple = vec3(0.415, 0.05, 0.678); // #6A0DAD
        
        // create soft blur orb
        float glow = 0.05 / max(dist - r, 0.01);
        float core = smoothstep(r + 0.01, r - 0.01, dist);
        
        color = purple * glow * 0.5 + purple * core;
        color = max(color, vec3(0.0));
    } 
    else if (u_state == 1) {
        // THINKING: Gaseous, multi-layered liquid light orb.
        // GPU-accelerated Simplex noise to create smoothly swirling, rotating interior currents.
        // Blend cyan (#00FFFF), electric blue (#0000FF), soft purple. Intense white highlights.
        
        float r = 0.25;
        float n1 = snoise(uv * 3.0 + vec2(u_time * 0.2, -u_time * 0.1));
        float n2 = snoise(uv * 5.0 - vec2(u_time * 0.3, u_time * 0.2));
        float n3 = snoise(uv * 2.0 + vec2(sin(u_time*0.5), cos(u_time*0.5)));
        
        float noiseVal = (n1 + n2 + n3) / 3.0;
        
        vec3 cyan = vec3(0.0, 1.0, 1.0);
        vec3 eblue = vec3(0.0, 0.0, 1.0);
        vec3 spurple = vec3(0.5, 0.2, 0.8);
        
        vec3 baseColor = mix(eblue, cyan, n1 * 0.5 + 0.5);
        baseColor = mix(baseColor, spurple, n2 * 0.5 + 0.5);
        
        // Add white highlights
        float highlight = smoothstep(0.3, 0.5, noiseVal);
        baseColor += vec3(highlight);
        
        // Mask to orb and glow
        float mask = smoothstep(r + 0.1, r - 0.05, dist + n3*0.05);
        float glow = 0.08 / max(dist - r, 0.01);
        
        color = baseColor * mask + baseColor * glow * 0.3;
    }
    else if (u_state == 2) {
        // TALKING: Dynamic, morphing energy visualization driven by 'current_volume'.
        // Layered electric cyan and vibrant pink (#FF007F).
        
        float vol = u_volume; // smoothed volume
        float r = 0.15 + vol * 0.15; // expand/contract scale
        
        // geometric deformation
        float angle = atan(uv.y, uv.x);
        float deform = sin(angle * 8.0 + u_time * 5.0) * sin(angle * 3.0 - u_time * 3.0) * 0.05 * vol;
        r += deform;
        
        vec3 cyan = vec3(0.0, 1.0, 1.0);
        vec3 pink = vec3(1.0, 0.0, 0.498); // #FF007F
        
        // Create layers
        float layer1 = smoothstep(r + 0.05, r - 0.01, dist);
        float layer2 = 0.05 / max(dist - r, 0.005); // sharp intense edge glow
        
        vec3 mixedColor = mix(pink, cyan, abs(sin(dist * 10.0 - u_time * 2.0)));
        
        color = mixedColor * layer1 + mixedColor * layer2;
    }
    
    fragColor = vec4(color, alpha);
}
"""

class AICore(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, gl_version=(3, 3))
        
        self.state = 'LISTENING'
        self.state_map = {'LISTENING': 0, 'THINKING': 1, 'TALKING': 2}
        
        # Audio simulation variables
        self.target_volume = 0.0
        self.current_volume = 0.0
        self.shader_time = 0.0
        
        # Setup shaders
        self.quad = geometry.quad_2d_fs()
        self.program = self.ctx.program(
            vertex_shader='''
            #version 330 core
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
            ''',
            fragment_shader=FRAGMENT_SHADER
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.L:
            self.state = 'LISTENING'
        elif key == arcade.key.T:
            self.state = 'THINKING'
        elif key == arcade.key.K:
            self.state = 'TALKING'

    def on_update(self, delta_time):
        self.shader_time += delta_time
        
        # Simulate talking volume changes if in talking state
        if self.state == 'TALKING':
            # Randomly change target volume occasionally to simulate speech patterns
            if math.sin(self.shader_time * 10.0) * math.cos(self.shader_time * 15.0) > 0.5:
                self.target_volume = 0.8 + 0.2 * math.sin(self.shader_time * 20.0)
            else:
                self.target_volume = 0.2 + 0.1 * math.sin(self.shader_time * 5.0)
        else:
            self.target_volume = 0.0
            
        # Linear Interpolation (Lerp) with physics momentum for volume expansion/contraction
        lerp_speed = 10.0 * delta_time
        self.current_volume += (self.target_volume - self.current_volume) * lerp_speed

    def on_draw(self):
        self.clear(color=(0, 0, 0, 255))
        
        # Set uniforms
        self.program['u_time'] = self.shader_time
        self.program['u_resolution'] = (self.width, self.height)
        self.program['u_state'] = self.state_map[self.state]
        self.program['u_volume'] = self.current_volume
        
        # Enable additive blending
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.BLEND_ADDITIVE # Equivalent to (GL_SRC_ALPHA, GL_ONE)
        
        self.quad.render(self.program)

if __name__ == "__main__":
    app = AICore()
    arcade.run()
