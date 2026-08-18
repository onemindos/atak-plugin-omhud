#!/usr/bin/env python3
"""
OneMind HUD — Tactical AR Overlay
Three modes replicated from reference tactical HUD images:
  1. GROUND — IVAS-style soldier HUD (yellow oval reticle, range rings)
  2. ORBITAL — Space tracking HUD (trajectory lines, orbital data)
  3. ISR — Airborne targeting pod (thermal inset, bearing/range, MGRS)

Deps: kivy[full] nats-py
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ListProperty
from math import sin, cos, radians
from datetime import datetime
import json, threading, asyncio, os

Window.clearcolor = (0, 0, 0, 0)  # transparent

CYAN   = (0, 0.85, 0.85, 0.9)
YELLOW = (1, 0.85, 0, 0.85)
ORANGE = (1, 0.55, 0, 0.85)
RED    = (1, 0.15, 0.15, 0.85)
WHITE  = (0.95, 0.95, 0.95, 0.85)
GREEN  = (0.2, 0.9, 0.2, 0.85)
DIM    = (0.4, 0.4, 0.4, 0.5)

class TacticalHUD(Widget):
    detections = ListProperty([])
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.mode = "GROUND"
        self._time_tick = 0
        # simulate GPS drift for demo — replace with android.gps
        self.lat, self.lon = 37.7749, -122.4194
        self.alt = 363
        self.heading = 310
        self.target_bearing = 104
        self.target_range = 489.2
        Clock.schedule_interval(self._draw, 1/30)
        # Start NATS subscriber
        threading.Thread(target=self._nats_loop, daemon=True).start()
    
    def _nats_loop(self):
        """Subscribe to fabric.vision.*.detect"""
        try:
            import nats
            async def sub():
                url = os.getenv("NATS_URL", "nats://localhost:4222")
                nc = await nats.connect(url)
                async def handler(msg):
                    det = json.loads(msg.data)
                    self.detections = self.detections[-19:] + [det]  # keep last 20
                await nc.subscribe("fabric.vision.*.detect", cb=handler)
                await asyncio.Future()  # keep alive
            asyncio.run(sub())
        except Exception:
            pass  # NATS unavailable → demo mode
    
    def _draw(self, dt):
        self._time_tick += 1
        self.canvas.clear()
        w, h = self.width, self.height
        if w < 100: return  # not laid out yet
        
        cx, cy = w/2, h/2  # center
        
        if self.mode == "GROUND":
            self._draw_ground_mode(w, h, cx, cy)
        elif self.mode == "ISR":
            self._draw_isr_mode(w, h, cx, cy)
        elif self.mode == "ORBITAL":
            self._draw_orbital_mode(w, h, cx, cy)
        
        # Always draw detection boxes from NATS
        self._draw_detections(w, h)
    
    def _draw_ground_mode(self, w, h, cx, cy):
        """Image 1: Ground Soldier IVAS-style HUD on forest"""
        # Top bar
        self._rect(0, h-48, w, 48, DIM)
        self._text(cx, h-16, "Tactical", CYAN, size=18)
        self._text(cx+60, h-16, "2 ⊕", WHITE, size=16)
        self._text(w-80, h-16, "15:06:34 (L)", CYAN, size=14)
        
        # Right data panel
        self._text(w-90, h-40, "Quietpro 19-350631", WHITE, size=11)
        self._text(w-90, h-56, "363 FT", GREEN, size=13)
        self._text(w-90, h-70, "1.75 OV 11328 88864", CYAN, size=11)
        self._text(w-90, h-84, "GROUND TRACK", WHITE, size=11)
        
        # Left range ring
        self._circle(cx-160, cy+40, 80, YELLOW, width=1.2)
        self._text(cx-160, cy-30, "185 M", YELLOW, size=12)
        
        # Right range ring
        self._circle(cx+140, cy+30, 85, YELLOW, width=1.2)
        self._text(cx+140, cy-40, "147 M", YELLOW, size=12)
        
        # Center target oval reticle
        self._oval(cx-45, cy-20, 90, 40, YELLOW, width=2.0)
        self._text(cx, cy+8, "104", ORANGE, size=28)
        self._text(cx, cy-35, "1.75 OV 11328 88864", CYAN, size=10)
        self._text(cx, cy-48, "FUTURE", RED, size=12)
        
        # Bottom range
        self._text(cx, h-40, "489.2 M", YELLOW, size=16)
    
    def _draw_isr_mode(self, w, h, cx, cy):
        """Image 3: ISR Airborne Targeting HUD"""
        # Top bar
        self._rect(0, h-44, w, 44, DIM)
        self._text(cx, h-14, "8008 G", CYAN, size=18)
        self._text(cx+70, h-14, "H+7 01:27", WHITE, size=14)
        
        # Compass indicator
        self._text(w-80, h-14, "W", RED, size=16)
        
        # Right data block
        self._text(w-90, h-42, "COMMS: JUMP30", WHITE, size=11)
        self._text(w-90, h-56, "GC 56H LH 38161 88090", CYAN, size=11)
        self._text(w-90, h-70, "BEARING: 3010 W", GREEN, size=11)
        self._text(w-90, h-84, "RANGE: 1.7 KM", ORANGE, size=13)
        
        # Yellow targeting circle reticle with ranging ticks
        self._circle(cx, cy+10, 55, YELLOW, width=2.0)
        # Ranging scale ticks (4 ticks around circle)
        for i in range(4):
            ang = radians(i * 90)
            rx, ry = cx + 55*cos(ang), (cy+10) + 55*sin(ang)
            rx2, ry2 = cx + 65*cos(ang), (cy+10) + 65*sin(ang)
            self._line(rx, ry, rx2, ry2, YELLOW, width=1.5)
        
        # Bottom MGRS display
        self._rect(0, 0, w, 32, DIM)
        self._text(cx, 10, "56H LH 38161 88090", CYAN, size=13)
        self._text(cx, 22, "119 M HAE", WHITE, size=11)
        
        # Thermal inset window (top-left)
        ix, iy, iw, ih = 16, h-172, 160, 120
        self._rect(ix, iy-ih, iw, ih, (0,0,0,0), border=1.5, border_color=GREEN)
        # Simulated thermal content (gray rectangle)
        self._rect(ix+2, iy-ih+2, iw-4, ih-4, (0.1,0.1,0.1,0.6))
        self._text(ix+iw/2, iy-ih+6, "IR", GREEN, size=10)
    
    def _draw_orbital_mode(self, w, h, cx, cy):
        """Image 2: Orbital/Space Tracking HUD"""
        # Timeline bar at top
        self._rect(0, h-44, w, 44, DIM)
        # Waypoint ticks along timeline
        for i in range(6):
            tx = 40 + i * (w/6)
            self._text(tx, h-16, "▪", CYAN, size=14)
        self._text(w-60, h-16, "▶", ORANGE, size=16)
        
        # Trajectory dotted lines
        for i in range(8):
            self._line(i*w/7, cy-20 + 30*sin(i*0.8+self._time_tick*0.01), 
                       (i+1)*w/7, cy-20 + 30*sin((i+1)*0.8+self._time_tick*0.01), 
                       CYAN, width=1.0)
        
        # Golden waypoint marker
        self._oval(cx-15, cy-15, 30, 30, ORANGE, width=2.0)
        self._text(cx, cy+20, "WAYPOINT", ORANGE, size=12)
        
        # Right orbital data
        self._text(w-100, h-42, "ΔV: 1,547 m/s", WHITE, size=12)
        self._text(w-100, h-58, "INC: 28.5°", CYAN, size=12)
        self._text(w-100, h-74, "ALT: 408 km", GREEN, size=12)
        self._text(w-100, h-90, "PER: 92.7 min", WHITE, size=12)
    
    def _draw_detections(self, w, h):
        """Draw YOLOv5s detection bounding boxes from NATS"""
        cx, cy = w/2, h/2
        for i, det in enumerate(self.detections[-20:]):
            cls = det.get("object_class", "?")
            conf = det.get("confidence", 0)
            bbox = det.get("bbox", [0, 0, 0, 0])
            # Scale bbox (0-1) to screen
            x1 = bbox[0] * w
            y1 = bbox[1] * h
            x2 = bbox[2] * w
            y2 = bbox[3] * h
            
            alpha = 0.7 - (i * 0.03)  # fade older
            color = YELLOW
            if cls in ("person", "people"): color = RED
            elif cls in ("car", "truck", "bus", "van"): color = CYAN
            elif cls == "bicycle": color = GREEN
            
            self._rect(x1, y2, x2-x1, y2-y1, (0,0,0,0), border=1.5, border_color=color)
            self._text(x1, y1-8, f"{cls} {conf:.0%}", color, size=10)
    
    # Drawing primitives
    def _rect(self, x, y, w, h, color, border=0, border_color=None):
        with self.canvas:
            Color(*color)
            Rectangle(pos=(x, y), size=(w, h))
            if border:
                Color(*border_color)
                Line(rectangle=(x, y, w, h), width=border)
    
    def _circle(self, cx, cy, r, color, width=1):
        with self.canvas:
            Color(*color)
            Line(circle=(cx, cy, r), width=width)
    
    def _oval(self, cx, cy, w, h, color, width=1):
        with self.canvas:
            Color(*color)
            Line(ellipse=(cx-w/2, cy-h/2, w, h), width=width)
    
    def _line(self, x1, y1, x2, y2, color, width=1):
        with self.canvas:
            Color(*color)
            Line(points=[x1, y1, x2, y2], width=width)
    
    def _text(self, x, y, text, color, size=12):
        from kivy.uix.label import Label
        lbl = Label(text=text, font_size=size, color=color,
                    pos=(x-100, y-8), size=(200, 20),
                    font_name='DroidSansMono' if 'DroidSansMono' in dir() else None)
        self.add_widget(lbl)
    
    def toggle_mode(self):
        modes = ["GROUND", "ISR", "ORBITAL"]
        idx = modes.index(self.mode)
        self.mode = modes[(idx + 1) % 3]

class HUDApp(App):
    def build(self):
        return TacticalHUD()

if __name__ == "__main__":
    HUDApp().run()
