import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMenu, QSystemTrayIcon, QVBoxLayout, QLabel,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QPushButton,
    QComboBox, QListWidget, QTextEdit, QInputDialog, QLineEdit, QScrollArea, QFileDialog, QMessageBox,
    QStackedLayout, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QSize
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QSurfaceFormat
from PyQt6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram
from OpenGL.GL import *
import array

FRAGMENT_SHADER = """
#version 330 core

uniform float u_time;
uniform vec2 u_resolution;
uniform int u_state; // 0=Thinking, 1=Listening, 2=Talking
uniform float u_volume;

out vec4 fragColor;

// 3D Noise for organic movement
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i); 
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0)) 
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    // Normalize UV by the smaller dimension so the orb is always a perfect circle
    float minDim = min(u_resolution.x, u_resolution.y);
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / minDim;
    
    // Aspect ratio for document editing morph
    float ratio = u_resolution.x / u_resolution.y;
    
    // Stretch UV only during document editing (state 3) to fill the wider window
    vec2 orbUv = uv;
    if (u_state == 3 && ratio > 1.05) {
        // Scale X so the orb stretches to fill the rectangular window
        orbUv.x /= ratio * 0.85;
    }
    
    // Polar coordinates
    float angle = atan(orbUv.y, orbUv.x);
    float radius = length(orbUv);
    
    // Base colors per state
    vec3 coreColor;
    vec3 outerColor;
    float hueShift = u_time * 0.1;
    float vol = smoothstep(0.0, 1.0, u_volume);
    
    float amplitudeScale = 0.05 + vol * 0.2; // A in the harmonic equation
    float timeScale = u_time * 2.0;
    
    if (u_state == 0) {
        // Idle
        coreColor = hsv2rgb(vec3(fract(0.55 + hueShift), 0.8, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.65 + hueShift), 0.9, 1.0));
        timeScale = u_time * 1.5;
        amplitudeScale = 0.03;
    } else if (u_state == 1) {
        // Listening
        coreColor = hsv2rgb(vec3(fract(0.55 + hueShift*2.0), 0.9, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.85 + hueShift), 1.0, 1.0));
        timeScale = u_time * 3.0;
        amplitudeScale = 0.06 + snoise(vec3(u_time))*0.02;
    } else if (u_state == 2) {
        // Talking
        coreColor = hsv2rgb(vec3(fract(0.08 + hueShift*3.0), 0.9, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.95 + hueShift*2.0), 0.9, 1.0));
        timeScale = u_time * 4.0;
        amplitudeScale = 0.08 + vol * 0.3;
    } else if (u_state == 3) {
        // Document Editing
        coreColor = hsv2rgb(vec3(fract(0.80 + hueShift), 0.8, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.90 + hueShift), 0.9, 1.0));
        timeScale = u_time * 2.0;
        amplitudeScale = 0.04;
    } else if (u_state == 4) {
        // Generating
        coreColor = hsv2rgb(vec3(fract(0.12 + hueShift*4.0), 0.9, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.18 + hueShift*3.0), 1.0, 1.0));
        timeScale = u_time * 15.0;
        amplitudeScale = 0.15 + snoise(vec3(u_time * 5.0))*0.08;
    } else if (u_state == 5) {
        // Thinking
        coreColor = hsv2rgb(vec3(fract(0.70 + hueShift), 0.8, 1.0));
        outerColor = hsv2rgb(vec3(fract(0.75 + hueShift), 0.9, 1.0));
        timeScale = u_time * 5.0;
        amplitudeScale = 0.04 + snoise(vec3(u_time * 2.0))*0.02;
    } else {
        coreColor = vec3(1.0);
        outerColor = vec3(1.0);
    }
    
    vec3 col = vec3(0.0);
    
    // Draw multiple overlapping harmonic ribbons/waves
    // Formula: y = A_1 * sin(B_1 * x - C_1 * t) + A_2 * cos(B_2 * x - C_2 * t) + D
    for(int i = 1; i <= 4; i++) {
        float fi = float(i);
        
        // Ensure B_1 and B_2 are strictly integers to prevent radial seams!
        float B_1 = fi * 2.0;
        float B_2 = fi * 3.0;
        
        float C_1 = timeScale * (1.0 + fi * 0.2);
        float C_2 = timeScale * (0.8 + fi * 0.15);
        
        float A_1 = amplitudeScale * (1.0 / fi);
        float A_2 = A_1 * 0.5;
        
        // Compute wave radius offset
        // We use angle as 'x'
        float wave = A_1 * sin(B_1 * angle - C_1) + A_2 * cos(B_2 * angle - C_2);
        
        // Add organic noise to wave
        // Offset UV to avoid axis-aligned simplex grid artifacts (the 'crack' in the center)
        wave += snoise(vec3((uv + vec2(17.31, 29.77)) * 5.0, u_time + fi)) * A_1 * 0.5;
        
        // D is base radius
        float D = 0.25 + (fi * 0.03); 
        float targetRadius = max(D + wave, 0.01); // Prevent targetRadius from going negative and causing a cusp
        
        // Distance to the ribbon
        float d = abs(radius - targetRadius);
        
        // Glow calculation
        float glow = 0.003 / (0.001 + d * d);
        
        // Mix colors
        vec3 layerColor = mix(coreColor, outerColor, fract(fi * 0.25 + hueShift));
        col += layerColor * glow * 0.5;
    }
    
    // Central core glowing orb
    float coreNoise = snoise(vec3((uv + vec2(17.31, 29.77)) * 8.0, u_time * 2.0)) * 0.02;
    float coreRadius = 0.15 + vol * 0.1 + coreNoise;
    float coreDist = abs(radius - coreRadius);
    float coreGlow = 0.01 / (0.001 + coreDist * coreDist);
    col += coreColor * coreGlow * 0.5;
    
    // Fill the inside slightly
    if(radius < coreRadius) {
        col += coreColor * 0.3;
    }
    
    // Tonemapping and gamma
    col = 1.0 - exp(-col * 1.5);
    col = pow(col, vec3(1.0/2.2));
    
    // Soft mask
    float mask = smoothstep(0.48, 0.35, radius);
    
    if (u_state == 3) {
        // Dynamic mask based on window ratio to clip extreme corners
        vec2 qBox = abs(uv) - vec2(ratio * 0.5 - 0.05, 0.5 - 0.05);
        float dBoxMask = length(max(qBox,0.0)) + min(max(qBox.x,qBox.y),0.0);
        mask *= smoothstep(0.02, -0.02, dBoxMask);
    }
    
    col *= mask;
    
    float alpha = dot(col, vec3(0.299, 0.587, 0.114)) * 2.0;
    alpha = clamp(alpha, 0.0, 1.0) * mask;
    
    fragColor = vec4(col, alpha);
}
"""

VERTEX_SHADER = """
#version 330 core
in vec2 in_vert;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

class ShaderWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        fmt = QSurfaceFormat()
        fmt.setAlphaBufferSize(8)
        self.setFormat(fmt)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.shader_time = 0.0
        self.state_map = {'listening': 1, 'thinking': 5, 'speaking': 2, 'idle': 0, 'confirming_pause': 1, 'document_editing': 3, 'generating': 4, 'awaiting_edit_goal': 1}
        self.state = 'idle'
        self.target_volume = 0.0
        self.current_volume = 0.0
        
        self.program = None
        
    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0) # Transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.program = QOpenGLShaderProgram()
        self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER)
        self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAGMENT_SHADER)
        self.program.link()
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
        if self.state == 'idle':
            return
            
        self.program.bind()
        
        self.program.setUniformValue("u_time", self.shader_time)
        pr = self.devicePixelRatio()
        self.program.setUniformValue("u_resolution", float(self.width() * pr), float(self.height() * pr))
        self.program.setUniformValue("u_state", self.state_map.get(self.state, 0))
        self.program.setUniformValue("u_volume", self.current_volume)
        
        # Simple fullscreen quad
        vertices = [
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0
        ]
        
        loc = self.program.attributeLocation("in_vert")
        if loc != -1:
            self.program.enableAttributeArray(loc)
            
            import ctypes
            vert_array = (ctypes.c_float * len(vertices))(*vertices)
            
            glVertexAttribPointer(loc, 2, GL_FLOAT, GL_FALSE, 0, vert_array)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            self.program.disableAttributeArray(loc)
        self.program.release()

from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient

class DropBox(QFrame):
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._speaking_state = "idle"  # idle | speaking | thinking
        self._anim_time = 0.0
        self._volume = 0.0
        
    def set_speaking_state(self, state: str, volume: float = 0.0):
        self._speaking_state = state
        self._volume = volume
        self.update()
        
    def advance_time(self, dt: float):
        self._anim_time += dt
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        import math, colorsys
        t = self._anim_time
        hue_shift = t * 0.1  # matches shader hueShift = u_time * 0.1
        vol = min(1.0, self._volume)
        
        if self._speaking_state == "speaking":
            # Orb talking state: hue ~ 0.08 + hueShift*3 (warm orange→red cycling)
            hue = math.fmod(0.08 + hue_shift * 3.0, 1.0)
            hue2 = math.fmod(0.95 + hue_shift * 2.0, 1.0)
            # Pulse fast, boosted by volume
            pulse = 0.5 + 0.5 * math.sin(t * 8.0)
            intensity = 0.6 + 0.4 * max(pulse, vol)
            r1, g1, b1 = colorsys.hsv_to_rgb(hue, 0.9, intensity)
            r2, g2, b2 = colorsys.hsv_to_rgb(hue2, 0.9, intensity)
            alpha = int(180 + 75 * intensity)
            border_w = 2 + int(4 * (0.5 + 0.5 * vol))
            
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0.0,  QColor(int(r1*255), int(g1*255), int(b1*255), alpha))
            grad.setColorAt(0.5,  QColor(int(r2*255), int(g2*255), int(b2*255), alpha))
            grad.setColorAt(1.0,  QColor(int(r1*255), int(g1*255), int(b1*255), alpha))
            
            pen = QPen(grad, border_w)
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            m = border_w // 2 + 1
            painter.drawRoundedRect(m, m, self.width() - m * 2, self.height() - m * 2, 10, 10)
            
        elif self._speaking_state in ("thinking", "listening", "generating"):
            # Perimeter streak animation for processing
            hue = math.fmod(0.65 + hue_shift, 1.0)
            r1, g1, b1 = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
            
            border_w = 3
            m = border_w // 2 + 1
            rect_w = self.width() - m * 2
            rect_h = self.height() - m * 2
            perimeter = 2 * (rect_w + rect_h)
            
            dash_length = 150.0 # Length of the streak
            # Streak races around the perimeter
            offset = (t * 400.0) % perimeter
            
            pen = QPen(QColor(int(r1*255), int(g1*255), int(b1*255), 255), border_w)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setDashPattern([dash_length, perimeter - dash_length])
            pen.setDashOffset(-offset)  # Negative to move clockwise
            
            painter.setPen(pen)
            painter.drawRoundedRect(m, m, rect_w, rect_h, 10, 10)
        
        painter.end()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            event.ignore()
            return
        super().mousePressEvent(event)

class JarvisBubble(QWidget):
    state_signal = pyqtSignal(str)
    audio_signal = pyqtSignal(float)
    transcript_signal = pyqtSignal(str)
    abort_signal = pyqtSignal()
    show_memory_signal = pyqtSignal(dict)
    sleep_signal = pyqtSignal()
    show_protocols_signal = pyqtSignal(dict)
    save_protocols_signal = pyqtSignal(dict)
    ui_closed_signal = pyqtSignal()
    save_memory_full_signal = pyqtSignal(dict)
    refresh_memory_signal = pyqtSignal(dict)
    prompt_password_signal = pyqtSignal(str, str, list)
    protocol_authenticated_signal = pyqtSignal(list)
    prompt_user_input_signal = pyqtSignal(str, str)
    prompt_signin_signal = pyqtSignal()
    refresh_sticky_note_signal = pyqtSignal(object)
    prompt_url_dialog_signal = pyqtSignal(str)
    prompt_folder_signal = pyqtSignal()
    files_dropped_signal = pyqtSignal(list)  # Emitted when files are dropped/browsed while morphed

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        
        self.last_dropped_files = []
        
        # Small desktop overlay size
        self.resize(150, 150)
        self._center_on_screen()
        self._is_morphed = False  # Track whether we are in morphed (rectangular) mode
        
        # Use a stacked layout so everything overlaps (no vertical stacking)
        stack_layout = QStackedLayout(self)
        stack_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        
        # Use our custom OpenGL widget (bottom layer — fills entire window)
        self.shader_widget = ShaderWidget(self)
        self.shader_effect = QGraphicsOpacityEffect(self.shader_widget)
        self.shader_widget.setGraphicsEffect(self.shader_effect)
        stack_layout.addWidget(self.shader_widget)
        
        # Overlay container for transcript label + dropdown (on top of shader)
        overlay = QWidget(self)
        overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # IMPORTANT: let mouse & drag events pass through to DropBox below
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(10, 10, 10, 10)
        
        # Push content to the bottom of the overlay
        overlay_layout.addStretch(1)
        
        # Transcript label overlaid on top
        self.transcript_label = QLabel(self)
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; background: transparent;")
        self.transcript_label.setWordWrap(True)
        overlay_layout.addWidget(self.transcript_label)

        # Document Drop Box
        self.drop_box = DropBox(self)
        self.drop_box.clicked.connect(self._on_drop_box_clicked)
        
        
        
        self.drop_effect = QGraphicsOpacityEffect(self.drop_box)
        self.drop_box.setGraphicsEffect(self.drop_effect)
        self.drop_box.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 15, 15, 240);
                border: 2px dashed rgba(255, 255, 255, 100);
                border-radius: 10px;
            }
        """)
        self.drop_box.hide()
        drop_layout = QVBoxLayout(self.drop_box)
        drop_layout.setContentsMargins(20, 20, 20, 20)
        drop_layout.setSpacing(10)
        
        self.drop_label = QLabel("Browse or Drop files")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        drop_layout.addWidget(self.drop_label)
        stack_layout.addWidget(self.drop_box)
        
        stack_layout.addWidget(overlay)
        
        # Animation loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16) # ~60fps
        
        # Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        self._create_tray_icon()
        
        # Context Menu
        tray_menu = QMenu()
        abort_action = QAction("Abort Agent Tasks", self)
        abort_action.triggered.connect(self.abort_signal.emit)
        sleep_action = QAction("Put Jarvis to Sleep", self)
        sleep_action.triggered.connect(self.sleep_signal.emit)
        show_action = QAction("Show/Hide Jarvis", self)
        show_action.triggered.connect(self._toggle_visibility)
        quit_action = QAction("Quit Jarvis completely", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(abort_action)
        tray_menu.addAction(sleep_action)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        self.tray_icon.show()
        
        # pyqtSignals
        self.state_signal.connect(self._on_state_change)
        self.audio_signal.connect(self._on_audio_change)
        self.transcript_signal.connect(self._on_transcript)
        self.show_memory_signal.connect(self._on_show_memory)
        self.show_protocols_signal.connect(self._on_show_protocols)
        self.refresh_memory_signal.connect(self._on_refresh_memory)
        self.prompt_password_signal.connect(self._on_prompt_password)
        self.prompt_user_input_signal.connect(self._on_prompt_user_input)
        self.prompt_signin_signal.connect(self._on_prompt_signin)
        self.refresh_sticky_note_signal.connect(self._on_refresh_sticky_note)
        self.prompt_url_dialog_signal.connect(self._on_prompt_url_dialog)
        self.prompt_folder_signal.connect(self._on_prompt_folder)
        
        self._user_input_response = ""
        self._signin_response = ""
        import threading
        self._user_input_event = threading.Event()
        self._signin_event = threading.Event()
        
        self.memory_window = None
        self.protocol_window = None
        self.sticky_note_widget = None

    def _close_all_ui(self):
        if self.memory_window is not None and self.memory_window.isVisible():
            self.memory_window.close()
        if self.protocol_window is not None and self.protocol_window.isVisible():
            self.protocol_window.close()

    def _on_show_memory(self, memory_data):
        self._close_all_ui()
        if self.memory_window is None:
            self.memory_window = MemoryWindow()
            self.memory_window.save_signal.connect(self.save_memory_full_signal.emit)
            self.memory_window.finished.connect(lambda: self.ui_closed_signal.emit())
        
        self.memory_window.update_memory(memory_data)
        
        if not self.memory_window.isVisible():
            self.memory_window.setWindowFlags(self.memory_window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.memory_window.show()
            self.memory_window.setWindowFlags(self.memory_window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.memory_window.show()
            self.memory_window.raise_()
            self.memory_window.activateWindow()

    def _on_refresh_memory(self, memory_data):
        if self.memory_window is not None and self.memory_window.isVisible():
            self.memory_window.update_memory(memory_data)

    def _on_prompt_folder(self):
        import os
        import json
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Document Output Folder", desktop_path)
        if folder:
            try:
                mem_file = "memory.json"
                if os.path.exists(mem_file):
                    with open(mem_file, "r", encoding="utf-8") as f:
                        mem = json.load(f)
                else:
                    mem = {}
                mem["document_output_folder"] = folder
                with open(mem_file, "w", encoding="utf-8") as f:
                    json.dump(mem, f, indent=4)
            except Exception as e:
                print("Failed to save folder:", e)

    def _on_show_protocols(self, protocols_data):
        self._close_all_ui()
        if self.protocol_window is None:
            self.protocol_window = ProtocolWindow(parent=self)
            self.protocol_window.save_protocols_signal.connect(self.save_protocols_signal.emit)
            self.protocol_window.finished.connect(lambda: self.ui_closed_signal.emit())
        self.protocol_window.update_protocols(protocols_data)
        self.protocol_window.setWindowFlags(self.protocol_window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.protocol_window.show()
        self.protocol_window.setWindowFlags(self.protocol_window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.protocol_window.show()
        self.protocol_window.raise_()
        self.protocol_window.activateWindow()

    def _on_prompt_password(self, protocol_name, expected_password, prompt):
        self._close_all_ui()
        
        # We need a hidden parent or self to show dialog
        pwd, ok = QInputDialog.getText(
            self, 
            "Authentication Required", 
            f"Enter password for {protocol_name}:",
            QLineEdit.EchoMode.Password
        )
        if ok and pwd == expected_password:
            self.protocol_authenticated_signal.emit(prompt)
            QTimer.singleShot(100, lambda: self.state_signal.emit("LISTENING"))
        else:
            self.protocol_authenticated_signal.emit("")
            QTimer.singleShot(100, lambda: self.state_signal.emit("LISTENING"))

    def _on_prompt_user_input(self, title: str, prompt: str):
        win = UserInputDialog(title, prompt, self)
        if win.exec() == QDialog.DialogCode.Accepted:
            self._user_input_response = win.get_text().strip()
        else:
            self._user_input_response = ""
        self._user_input_event.set()

    def ask_user_input_sync(self, title: str, prompt: str) -> str:
        """Called from a background thread to safely block and get input from the UI."""
        self._user_input_event.clear()
        self.prompt_user_input_signal.emit(title, prompt)
        self._user_input_event.wait()
        return self._user_input_response

    def _on_prompt_signin(self):
        self._close_all_ui()
        win = SignInWindow(self)
        if win.exec() == QDialog.DialogCode.Accepted:
            self._signin_response = win.choice
        else:
            self._signin_response = "cancel"
        self._signin_event.set()

    def ask_signin_sync(self) -> str:
        self._signin_event.clear()
        self.prompt_signin_signal.emit()
        self._signin_event.wait()
        return self._signin_response

    def _on_refresh_sticky_note(self, payload):
        if self.sticky_note_widget:
            self.sticky_note_widget.close()
            
        agenda_items = payload
        title = "Morning Briefing"
        subtitle = "TODAY'S SCHEDULE"
        
        if isinstance(payload, dict):
            agenda_items = payload.get("agenda_items", [])
            title = payload.get("title", "Morning Briefing")
            subtitle = payload.get("subtitle", "TODAY'S SCHEDULE")
            
        from sticky_note import StickyNote
        self.sticky_note_widget = StickyNote(agenda_items, title=title, subtitle=subtitle)
        self.sticky_note_widget.sign_in_requested.connect(self._on_prompt_signin)
        self.sticky_note_widget.show()

    def _on_prompt_url_dialog(self, url):
        win = UrlDialog(url, self)
        win.exec()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)


    def _center_on_screen(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + screen.height() - self.height() - 20
        self.move(x, y)
        



    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            
    def _on_drop_box_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", "All Files (*)")
        if file_names:
            self._on_files_dropped(file_names)
            
    def _create_tray_icon(self):

        from PyQt6.QtGui import QIcon, QAction
        
        self.tray_icon = QSystemTrayIcon(self)
        try:
            self.tray_icon.setIcon(QIcon("jarvis_logo.ico"))
        except:
            pass
            
        tray_menu = QMenu()
        
        browse_action = QAction("Browse Document", self)
        browse_action.triggered.connect(self._on_drop_box_clicked)
        tray_menu.addAction(browse_action)
        
        quit_action = QAction("Quit JARVIS", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _on_drop_box_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", "All Files (*)")
        if file_names:
            self._on_files_dropped(file_names)

    def _on_files_dropped(self, files):
        self.last_dropped_files = files
        print(f"Dropped files: {files}")
        self.files_dropped_signal.emit(files)

    def mousePressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            if hasattr(self, 'tray_icon') and self.tray_icon.contextMenu():
                self.tray_icon.contextMenu().popup(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_drag_pos'):
            del self._drag_pos
        event.accept()

    def _animate_close(self, callback=None):
        if callback:
            callback()

    def _on_state_change(self, new_state):
        # If we're morphed (document editing mode), preserve the rectangular shape
        # during transient states like speaking/listening that happen mid-flow
        if self._is_morphed and new_state in ("speaking", "listening", "thinking"):
            self.shader_widget.state = new_state
            # Update border animation on the drop box
            self.drop_box.set_speaking_state(new_state)
            if not self.isVisible():
                self.show()
            return
        
        # awaiting_edit_goal: show orb in listening mode, no resize
        if new_state == "awaiting_edit_goal":
            self.shader_widget.state = new_state
            if not self.isVisible():
                self.show()
            return
        
        if self.shader_widget.state == "document_editing" and new_state == "idle":
            # Don't go idle if we are waiting for a document
            if not getattr(self, 'last_dropped_files', []):
                return
        
        self.shader_widget.state = new_state
        
        if new_state == "document_editing":
            if not self._is_morphed:
                self._is_morphed = True
                self.drop_box.show()
                self.shader_widget.show()
                self.anim_group = QParallelAnimationGroup(self)
                
                self.size_anim = QPropertyAnimation(self, b"size")
                self.size_anim.setDuration(400)
                self.size_anim.setStartValue(self.size())
                self.size_anim.setEndValue(QSize(300, 150))
                self.size_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
                
                shader_anim = QPropertyAnimation(self.shader_effect, b"opacity")
                shader_anim.setDuration(400)
                shader_anim.setStartValue(1.0)
                shader_anim.setEndValue(0.0)
                
                drop_anim = QPropertyAnimation(self.drop_effect, b"opacity")
                drop_anim.setDuration(400)
                drop_anim.setStartValue(0.0)
                drop_anim.setEndValue(1.0)
                
                self.anim_group.addAnimation(self.size_anim)
                self.anim_group.addAnimation(shader_anim)
                self.anim_group.addAnimation(drop_anim)
                
                self.anim_group.finished.connect(self.shader_widget.hide)
                self.anim_group.start()
                QTimer.singleShot(410, self._center_on_screen)
        else:
            if self._is_morphed:
                self._is_morphed = False
                # Use a sequential animation to prevent visual glitches
                self.anim_group = QSequentialAnimationGroup(self)
                
                # Step 1: Fade out the drop box completely first
                drop_anim = QPropertyAnimation(self.drop_effect, b"opacity")
                drop_anim.setDuration(250)
                drop_anim.setStartValue(1.0)
                drop_anim.setEndValue(0.0)
                
                # Step 2: Parallel group to shrink the window while fading the orb back in
                step2_group = QParallelAnimationGroup(self)
                
                size_anim = QPropertyAnimation(self, b"size")
                size_anim.setDuration(350)
                size_anim.setStartValue(self.size())
                size_anim.setEndValue(QSize(150, 150))
                size_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
                
                shader_anim = QPropertyAnimation(self.shader_effect, b"opacity")
                shader_anim.setDuration(350)
                shader_anim.setStartValue(0.0)
                shader_anim.setEndValue(1.0)
                
                step2_group.addAnimation(size_anim)
                step2_group.addAnimation(shader_anim)
                
                self.anim_group.addAnimation(drop_anim)
                self.anim_group.addAnimation(step2_group)
                
                self.shader_widget.show()
                self.anim_group.finished.connect(self.drop_box.hide)
                self.anim_group.start()
                
                # Center after total animation time (250 + 350 = 600ms)
                QTimer.singleShot(610, self._center_on_screen)
            
        if new_state == "idle":
            if self.isVisible():
                self._animate_close(self.hide)
            else:
                self.hide()
        else:
            self.show()
        
        # Reset drop box border if we leave morphed mode
        if not self._is_morphed:
            self.drop_box.set_speaking_state("idle")
        
    def _on_audio_change(self, level):
        self.shader_widget.target_volume = level
            
    def _on_transcript(self, text):
        # The user requested to not display the text as it looks unprofessional.
        # We simply clear the text or keep it empty so the UI remains clean.
        self.transcript_label.setText("")
        
    def _animate(self):
        dt = 0.016
        self.shader_widget.shader_time += dt
        
        # Lerp volume
        lerp_speed = 10.0 * dt
        self.shader_widget.current_volume += (self.shader_widget.target_volume - self.shader_widget.current_volume) * lerp_speed
        
        if self.shader_widget.state != 'idle':
            self.shader_widget.update()
        
        # Drive drop box border animation when morphed
        if self._is_morphed:
            self.drop_box.advance_time(dt)
            self.drop_box.set_speaking_state(
                self.drop_box._speaking_state,
                self.shader_widget.current_volume
            )

class AnimatedGlassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #212121;
                border: 1px solid #424242;
                border-radius: 12px;
            }
            QLabel {
                color: #ececec;
                font-size: 15px;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-weight: 500;
                padding: 5px;
            }
            QPushButton {
                background-color: #2f2f2f;
                color: #ececec;
                border: 1px solid #424242;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-family: "Inter", "Segoe UI", sans-serif;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QPushButton#deleteBtn {
                color: #ff6b6b;
                border: 1px solid #5c2b2b;
                background-color: #3a1c1c;
            }
            QPushButton#deleteBtn:hover {
                background-color: #4a2424;
            }
            QTableWidget, QListWidget, QTextEdit, QLineEdit {
                background-color: #171717;
                color: #ececec;
                border: 1px solid #424242;
                border-radius: 6px;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-size: 14px;
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #212121;
                color: #ececec;
                padding: 6px;
                border: 1px solid #424242;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #424242;
                color: #ffffff;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #212121;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #525252;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        
        # Hide the orb when modal is open to avoid overlapping
        if self.parent() and hasattr(self.parent(), 'hide'):
            self.parent().hide()
            
        self.setWindowOpacity(0.0)
        
        self.anim_group = QParallelAnimationGroup(self)
        
        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(280)
        op_anim.setStartValue(0.0)
        op_anim.setEndValue(1.0)
        op_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(280)
        start_pos = self.pos()
        start_pos.setY(start_pos.y() + 20)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(self.pos())
        pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        self.anim_group.addAnimation(op_anim)
        self.anim_group.addAnimation(pos_anim)
        self.anim_group.start()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # #212121 background, #424242 border
        painter.setBrush(QBrush(QColor(33, 33, 33, 255)))
        painter.setPen(QPen(QColor(66, 66, 66, 255), 1))
        
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 12, 12)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent() and hasattr(self.parent(), "hide"):
            self.parent().hide()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.parent() and hasattr(self.parent(), "show"):
            self.parent().show()

    def reject(self):
        self._animate_close(lambda: QDialog.reject(self))
        
    def accept(self):
        self._animate_close(lambda: QDialog.accept(self))
        
    def _animate_close(self, callback):
        # Show the orb again
        if self.parent() and hasattr(self.parent(), 'show'):
            self.parent().show()
            
        self.anim_group = QParallelAnimationGroup(self)
        
        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(200)
        op_anim.setStartValue(self.windowOpacity())
        op_anim.setEndValue(0.0)
        op_anim.setEasingCurve(QEasingCurve.Type.InExpo)
        
        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(200)
        pos_anim.setStartValue(self.pos())
        end_pos = self.pos()
        end_pos.setY(end_pos.y() + 20)
        pos_anim.setEndValue(end_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.InExpo)
        
        self.anim_group.addAnimation(op_anim)
        self.anim_group.addAnimation(pos_anim)
        self.anim_group.finished.connect(callback)
        self.anim_group.start()

class MemoryWindow(AnimatedGlassDialog):
    save_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("J.A.R.V.I.S. Memory Banks")
        self.resize(600, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        layout = QVBoxLayout(self)

        title = QLabel("Memory Banks")
        layout.addWidget(title)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Fact Key", "Fact Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        top_btn_layout = QHBoxLayout()
        add_btn = QPushButton("New Memory")
        add_btn.clicked.connect(self._add_memory)
        del_btn = QPushButton("Delete Selected")
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self._delete_memory)
        top_btn_layout.addWidget(add_btn)
        top_btn_layout.addWidget(del_btn)
        top_btn_layout.addStretch()
        layout.addLayout(top_btn_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Apply Changes")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def update_memory(self, memory_data: dict):
        self.table.setRowCount(0)
        for row, (key, value) in enumerate(memory_data.items()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _add_memory(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("new_key"))
        self.table.setItem(row, 1, QTableWidgetItem("new_value"))
        self.table.selectRow(row)

    def _delete_memory(self):
        rows = set([index.row() for index in self.table.selectedIndexes()])
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def _save_and_close(self):
        new_memory = {}
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            if key_item and val_item:
                k = key_item.text().strip()
                v = val_item.text().strip()
                if k:
                    new_memory[k] = v
        self.save_signal.emit(new_memory)
        self.accept()

class ProtocolWindow(AnimatedGlassDialog):
    save_protocols_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("J.A.R.V.I.S. Protocol Configuration")
        self.resize(700, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        self.protocols = {}
        self.verifier_callback = parent.verifier_callback if hasattr(parent, "verifier_callback") else None
        self.current_selected = None

        layout = QVBoxLayout(self)
        title = QLabel("Protocol Configuration")
        layout.addWidget(title)

        main_split = QHBoxLayout()
        
        # Left Panel: List of Protocols
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_widget)
        
        list_btn_layout = QHBoxLayout()
        add_btn = QPushButton("New Protocol")
        add_btn.clicked.connect(self._add_protocol)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self._delete_protocol)
        list_btn_layout.addWidget(add_btn)
        list_btn_layout.addWidget(delete_btn)
        left_layout.addLayout(list_btn_layout)
        
        main_split.addLayout(left_layout, 1)

        # Right Panel: Protocol Editor
        right_layout = QVBoxLayout()
        self.editor_label = QLabel("Commands")
        right_layout.addWidget(self.editor_label)
        
        self.commands_text_edit = QTextEdit()
        self.commands_text_edit.setPlaceholderText("Enter natural language instructions for JARVIS here...")
        right_layout.addWidget(self.commands_text_edit)

        spotlight_layout = QHBoxLayout()
        spotlight_label = QLabel("Spotlight:")
        spotlight_layout.addWidget(spotlight_label)
        self.spotlight_edit = QLineEdit()
        self.spotlight_edit.setPlaceholderText("e.g. chrome, spotify (optional)")
        self.spotlight_edit.textChanged.connect(self._on_spotlight_changed)
        spotlight_layout.addWidget(self.spotlight_edit)
        right_layout.addLayout(spotlight_layout)
        
        # Right Panel: Password controls
        pwd_layout = QHBoxLayout()
        self.pwd_btn = QPushButton("Set Password")
        self.pwd_btn.clicked.connect(self._set_password)
        self.pwd_btn.setEnabled(False)
        pwd_layout.addWidget(self.pwd_btn)
        pwd_layout.addStretch()
        right_layout.addLayout(pwd_layout)
        
        main_split.addLayout(right_layout, 2)
        
        layout.addLayout(main_split)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Apply Changes")
        self.save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def update_protocols(self, protocols_data: dict):
        self.protocols = protocols_data.copy()
        self.list_widget.clear()
        for name in sorted(self.protocols.keys()):
            display_name = f"🔒 {name}" if self.protocols[name].get("password") else name
            self.list_widget.addItem(display_name)
        if self.protocols:
            self.list_widget.setCurrentRow(0)

    def _get_actual_name(self, display_name: str) -> str:
        return display_name.replace("🔒 ", "").strip()

    def _on_selection_changed(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.current_selected = None
            self.commands_text_edit.clear()
            self.commands_text_edit.setEnabled(False)
            self.spotlight_edit.clear()
            self.spotlight_edit.setEnabled(False)
            return
            
        display_name = items[0].text()
        name = self._get_actual_name(display_name)
        self.current_selected = name
        
        protocol_info = self.protocols.get(name, {})
        prompt = protocol_info.get("prompt", "")
        spotlight = protocol_info.get("spotlight", "")
        has_pwd = bool(protocol_info.get("password"))
        
        self.commands_text_edit.setText(prompt)
        self.commands_text_edit.setEnabled(True)
                
        self.spotlight_edit.blockpyqtSignals(True)
        self.spotlight_edit.setText(spotlight)
        self.spotlight_edit.setEnabled(True)
        self.spotlight_edit.blockpyqtSignals(False)
        
        self.editor_label.setText(f"Editing: {name} Protocol")
        
        self.pwd_btn.setEnabled(True)
        if has_pwd:
            self.pwd_btn.setText("Change / Remove Password")
        else:
            self.pwd_btn.setText("Set Password")

    def _on_spotlight_changed(self):
        if self.current_selected and self.current_selected in self.protocols:
            self.protocols[self.current_selected]["spotlight"] = self.spotlight_edit.text()

    def _set_password(self):
        if not self.current_selected: return
        pwd, ok = QInputDialog.getText(
            self, 
            "Set Password", 
            f"Enter password for {self.current_selected} (leave blank to remove):", 
            QLineEdit.EchoMode.Password
        )
        if ok:
            pwd = pwd.strip()
            self.protocols[self.current_selected]["password"] = pwd if pwd else None
            items = self.list_widget.selectedItems()
            if items:
                items[0].setText(f"🔒 {self.current_selected}" if pwd else self.current_selected)
            self._on_selection_changed()

    def _add_protocol(self):
        name, ok = QInputDialog.getText(self, "New Protocol", "Enter protocol name:")
        if ok and name:
            name = name.strip().lower()
            if name and name not in self.protocols:
                self.protocols[name] = {"prompt": "", "password": None}
                self.list_widget.addItem(name)
                items = self.list_widget.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    self.list_widget.setCurrentItem(items[0])

    def _delete_protocol(self):
        if self.current_selected and self.current_selected in self.protocols:
            del self.protocols[self.current_selected]
            row = self.list_widget.currentRow()
            self.list_widget.takeItem(row)

    def _save_and_close(self):
        if self.current_selected and self.current_selected in self.protocols:
            self.protocols[self.current_selected]["prompt"] = self.commands_text_edit.toPlainText()
            
        if self.verifier_callback:
            self.save_btn.setText("Verifying...")
            self.save_btn.setEnabled(False)
            QApplication.processEvents()
            
            for name, data in self.protocols.items():
                prompt = data.get("prompt", "").strip()
                if prompt:
                    success, error_msg = self.verifier_callback(name, prompt)
                    if not success:
                        QMessageBox.warning(self, "Protocol Ambiguity Detected", f"Issue in '{name}':\n\n{error_msg}")
                        self.save_btn.setText("Apply Changes")
                        self.save_btn.setEnabled(True)
                        return

        self.save_protocols_signal.emit(self.protocols)
        self.accept()


class UserInputDialog(AnimatedGlassDialog):
    def __init__(self, title: str, prompt: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title Label
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(title_label)

        # Prompt Label
        prompt_label = QLabel(prompt)
        prompt_label.setWordWrap(True)
        prompt_label.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        layout.addWidget(prompt_label)

        # Input Field
        self.input_field = QLineEdit(self)
        self.input_field.setStyleSheet(
            "background-color: rgba(30, 30, 30, 180);"
            "border: 1px solid rgba(255, 255, 255, 30);"
            "border-radius: 6px;"
            "padding: 8px;"
            "color: white;"
            "selection-background-color: #0078D7;"
        )
        self.input_field.returnPressed.connect(self.accept)
        layout.addWidget(self.input_field)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("primary_btn")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)  # Disabled by default
        
        # Enable OK button only when text is not empty
        self.input_field.textChanged.connect(lambda text: self.ok_btn.setEnabled(bool(text.strip())))
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
        self.input_field.setFocus()

    def get_text(self):
        return self.input_field.text()

class SignInWindow(AnimatedGlassDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("JARVIS Integration Authentication")
        self.resize(320, 180)

        layout = QVBoxLayout()
        label = QLabel("Select integration to sign in:", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.google_btn = QPushButton("Sign in with Google", self)
        self.google_btn.setObjectName("google_btn")
        self.google_btn.clicked.connect(self.accept_google)
        layout.addWidget(self.google_btn)

        self.microsoft_btn = QPushButton("Sign in with Microsoft", self)
        self.microsoft_btn.setObjectName("microsoft_btn")
        self.microsoft_btn.clicked.connect(self.accept_microsoft)
        layout.addWidget(self.microsoft_btn)
        
        self.skip_btn = QPushButton("Skip / Cancel", self)
        self.skip_btn.clicked.connect(self.reject)
        layout.addWidget(self.skip_btn)

        self.setLayout(layout)
        self.choice = None

    def accept_google(self):
        self.choice = "google"
        self.accept()

    def accept_microsoft(self):
        self.choice = "microsoft"
        self.accept()


class UrlDialog(AnimatedGlassDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authorization Required")
        self.resize(450, 220)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please visit this URL in your preferred Chrome profile:"))
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(url)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        self.copy_btn = QPushButton("Copy Link to Clipboard")
        self.copy_btn.clicked.connect(self.copy_link)
        layout.addWidget(self.copy_btn)
        
        self.open_btn = QPushButton("Open in Default Browser")
        self.open_btn.clicked.connect(self.open_link)
        layout.addWidget(self.open_btn)
        
        self.close_btn = QPushButton("Done / Continue")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.url = url
        
    def copy_link(self):
        QApplication.clipboard().setText(self.url)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("Copy Link to Clipboard"))
        
    def open_link(self):
        import webbrowser
        webbrowser.open(self.url)
