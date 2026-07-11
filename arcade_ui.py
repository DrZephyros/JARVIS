import arcade
import arcade.gl as gl
from array import array
import time
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Jarvis Core UI - Standalone Test"

# The master fragment shader handling all 3 states
FRAGMENT_SHADER = """
#version 330

uniform vec2 u_resolution;
uniform float u_time;
uniform int u_state; // 0=Listening, 1=Thinking, 2=Talking
uniform float u_volume; // 0.0 to 1.0
uniform float u_scale;  // Driven by breathing lerp in python

out vec4 fragColor;

// --- Simplex/Perlin Noise Helpers ---
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
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
    // Normalize coordinates to center (-1.0 to 1.0)
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    vec2 p = (uv - 0.5) * 2.0;
    // Fix aspect ratio if needed (assuming square for now)
    
    float dist = length(p);
    vec3 color = vec3(0.0);
    
    // LISTENING (0): Deep cosmic purple (#6A0DAD), rhythmic breathing blur
    if (u_state == 0) {
        // Base purple: 106, 13, 173 -> 0.41, 0.05, 0.68
        vec3 base_col = vec3(0.41, 0.05, 0.68);
        // Base radius modified by python scale uniform
        float r = 0.4 * u_scale;
        
        // Soft blur glow (exponential falloff)
        float glow = exp(-pow(dist / r, 2.0) * 4.0);
        float core = smoothstep(r, r - 0.1, dist);
        
        color = base_col * glow * 1.5 + vec3(1.0) * core * 0.2;
    }
    
    // THINKING (1): Gaseous, liquid light orb with simplex noise currents
    else if (u_state == 1) {
        // Cyan (#00FFFF), Electric Blue (#0000FF), Soft Purple
        vec3 col1 = vec3(0.0, 1.0, 1.0);
        vec3 col2 = vec3(0.0, 0.0, 1.0);
        vec3 col3 = vec3(0.5, 0.0, 0.8);
        
        // Rotating coordinates
        float s = sin(u_time * 0.2);
        float c = cos(u_time * 0.2);
        mat2 rot = mat2(c, -s, s, c);
        vec2 rp = rot * p;
        
        // Multi-layered noise
        float n1 = snoise(rp * 3.0 + u_time * 0.5);
        float n2 = snoise(rp * 6.0 - u_time * 0.3);
        float n = (n1 + n2) * 0.5;
        
        // Fluid masking
        float mask = smoothstep(0.6, 0.3, dist);
        float internal_current = smoothstep(0.0, 0.5, abs(n));
        
        vec3 mix_col = mix(col1, col2, n1 * 0.5 + 0.5);
        mix_col = mix(mix_col, col3, n2 * 0.5 + 0.5);
        
        // Intense white highlights where layers intersect
        vec3 highlight = vec3(1.0) * pow(internal_current, 4.0) * 2.0;
        
        color = (mix_col + highlight) * mask;
    }
    
    // TALKING (2): Dynamic, morphing energy driven by u_volume
    else if (u_state == 2) {
        // Electric Cyan (#00FFFF) and Vibrant Pink (#FF007F)
        vec3 cyan = vec3(0.0, 1.0, 1.0);
        vec3 pink = vec3(1.0, 0.0, 0.5);
        
        // Deform coordinates based on volume and angle
        float angle = atan(p.y, p.x);
        float deformation = snoise(vec2(angle * 3.0, u_time * 2.0)) * u_volume * 0.3;
        
        float r = 0.3 + u_volume * 0.2 + deformation;
        float mask = smoothstep(r + 0.1, r - 0.05, dist);
        
        // Energy rings
        float ring = abs(sin(dist * 20.0 - u_time * 5.0));
        vec3 ring_col = mix(cyan, pink, ring) * u_volume;
        
        color = mix(pink, cyan, (p.x + p.y)*0.5 + 0.5) * mask;
        color += ring_col * smoothstep(r + 0.2, r - 0.2, dist) * 1.5;
        // Central bright core
        color += vec3(1.0) * smoothstep(0.2, 0.0, dist) * (0.5 + u_volume);
    }
    
    fragColor = vec4(color, 1.0);
}
"""

VERTEX_SHADER = """
#version 330
in vec2 in_vert;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

class JarvisCore(arcade.Window):
    def __init__(self):
        # Request a highly optimized window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, gl_version=(3, 3))
        
        self.time_elapsed = 0.0
        self.state_enum = 0 # 0=Listening, 1=Thinking, 2=Talking
        
        # Physics/Lerp variables
        self.target_volume = 0.0
        self.current_volume = 0.0
        self.current_scale = 1.0
        self.base_breathing_time = 0.0
        
        # Build screen quad
        self.quad_fs = arcade.gl.geometry.quad_2d_fs()
        
        # Compile shaders
        try:
            self.program = self.ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=FRAGMENT_SHADER
            )
        except Exception as e:
            print("Shader compilation failed:", e)
            raise e

    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        self.base_breathing_time += delta_time
        
        # Physics Lerp for smooth talking volume transitions
        # Momentum based lerping
        lerp_speed = 10.0 * delta_time
        self.current_volume += (self.target_volume - self.current_volume) * lerp_speed
        
        # If talking, randomly generate target volume to simulate speech 
        # (in the real app, this would be fed by the mic/TTS RMS)
        if self.state_enum == 2:
            import random
            if random.random() < 0.1:
                self.target_volume = random.uniform(0.1, 1.0)
            else:
                self.target_volume *= 0.9 # decay
        else:
            self.target_volume = 0.0
            
        # LISTENING: Rhythmic 4-second breathing scale pulse (+/- 15px)
        if self.state_enum == 0:
            # 4 second period = 2*pi / 4
            self.current_scale = 1.0 + math.sin(self.base_breathing_time * (math.pi / 2.0)) * 0.15
        else:
            self.current_scale += (1.0 - self.current_scale) * lerp_speed

    def on_draw(self):
        self.clear(arcade.color.BLACK)
        
        # Enable Additive Blending as requested
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.BLEND_ADDITIVE # Equivalent to GL_SRC_ALPHA, GL_ONE
        
        # Update Uniforms
        self.program["u_time"] = self.time_elapsed
        self.program["u_resolution"] = (self.width, self.height)
        self.program["u_state"] = self.state_enum
        self.program["u_volume"] = self.current_volume
        self.program["u_scale"] = self.current_scale
        
        # Draw full screen quad
        self.quad_fs.render(self.program)

    def on_key_press(self, key, modifiers):
        """Keyboard handler mapping L, T, and K to switch states"""
        if key == arcade.key.L:
            self.state_enum = 0
            print("Switched to LISTENING")
        elif key == arcade.key.T:
            self.state_enum = 1
            print("Switched to THINKING")
        elif key == arcade.key.K:
            self.state_enum = 2
            print("Switched to TALKING")
            
if __name__ == "__main__":
    app = JarvisCore()
    print("Arcade UI Started. Press L for Listening, T for Thinking, K for Talking.")
    arcade.run()
