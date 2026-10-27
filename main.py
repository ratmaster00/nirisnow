#!/usr/bin/env python3
# Wayland layer-shell snow overlay (Niri, Sway, Hyprland...).
# Arch: sudo pacman -S gtk-layer-shell python-gobject python-cairo
import ctypes.util, math, os, random, signal, sys

# gtk-layer-shell must be loaded before libwayland-client -> re-exec with preload
if "snow_preload" not in os.environ:
    lib = ctypes.util.find_library("gtk-layer-shell")
    if lib:
        os.environ["LD_PRELOAD"] = lib
    os.environ["snow_preload"] = "1"
    os.environ.setdefault("GDK_BACKEND", "wayland")
    os.execvp(sys.executable, [sys.executable] + sys.argv)

import cairo, gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell

FLAKES = 150
FPS = 30
MAX_PILE = 80    # max pile height in px
PILE_RATE = 0.5    # how fast the pile builds up


class Snow(Gtk.Window):
    def __init__(self, monitor):
        super().__init__()
        self.set_app_paintable(True)
        self.set_visual(self.get_screen().get_rgba_visual())

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_monitor(self, monitor)
        GtkLayerShell.set_exclusive_zone(self, -1)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                     GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, edge, True)

        g = monitor.get_geometry()
        self.w, self.h = g.width, g.height
        self.flakes = [self.flake(True) for _ in range(FLAKES)]
        self.pile = [0.0] * self.w

        self.connect("draw", self.on_draw)
        self.connect("map", self.passthrough)
        self.connect("size-allocate", self.passthrough)
        GLib.timeout_add(1000 // FPS, self.step)

    def flake(self, anywhere=False):
        r = random.uniform(1.5, 4)
        return [random.uniform(0, self.w),
                random.uniform(0, self.h) if anywhere else -r,
                r, r * 0.4 + 0.3, random.uniform(0, 6.28)]  # x, y, radius, speed, phase

    def step(self):
        for i, f in enumerate(self.flakes):
            f[1] += f[3]
            f[0] += math.sin(f[1] / 50 + f[4]) * 0.4
            x = min(max(int(f[0]), 0), self.w - 1)
            if f[1] + f[2] >= self.h - self.pile[x]:
                self.land(x, f[2])
                self.flakes[i] = self.flake()
        p = self.pile
        self.pile = [p[0]] + [(p[i-1] + 2*p[i] + p[i+1]) / 4
                              for i in range(1, self.w - 1)] + [p[-1]]
        self.queue_draw()
        return True

    def land(self, x, r):
        R = int(r * 12)
        for i in range(max(0, x - R), min(self.w, x + R + 1)):
            bump = r * PILE_RATE * 0.5 * (1 + math.cos(math.pi * (i - x) / R))
            self.pile[i] += bump * (1 - self.pile[i] / MAX_PILE)

    def on_draw(self, _, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(1, 1, 1, 0.85)

        cr.move_to(0, self.h)
        for i in range(0, self.w, 3):
            cr.line_to(i, self.h - self.pile[i])
        cr.line_to(self.w, self.h - self.pile[-1])
        cr.line_to(self.w, self.h)
        cr.fill()

        for x, y, r, *_ in self.flakes:
            cr.arc(x, y, r, 0, 6.2832)
            cr.fill()

    def passthrough(self, *_):
        w = self.get_window()
        if w:
            w.input_shape_combine_region(
                cairo.Region(cairo.RectangleInt(0, 0, 1, 1)), 0, 0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    d = Gdk.Display.get_default()
    wins = [Snow(d.get_monitor(i)) for i in range(d.get_n_monitors())]
    for w in wins:
        w.show_all()
    Gtk.main()