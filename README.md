# nirisnow

Round white dots falling down your desktop, slowly piling up at the bottom of the screen.

A transparent, vibecoded (as always :3) click-through overlay for Wayland, drawn with GTK3 and wlr-layer-shell. It sits above everything, covers every monitor, and doesn't eat your clicks.

## Requirements

- A Wayland compositor with `wlr-layer-shell` support (niri, Sway, Hyprland, ...). GNOME's Mutter doesn't support it.
- Python 3, PyGObject, pycairo, gtk-layer-shell (GTK3 build)

Arch:

```
sudo pacman -S gtk-layer-shell python-gobject python-cairo
```

Debian/Ubuntu:

```
sudo apt install gir1.2-gtklayershell-0.1 python3-gi python3-gi-cairo
```

## Run

```
/usr/bin/python3 main.py
```

Stop it with Ctrl+C in the terminal.

Use the system Python, not a venv. The script has no pip dependencies, and a venv usually can't see the system `gi`.

## Config

Constants at the top of `main.py`:

| Name | Default | What it does |
|---|---|---|
| `FLAKES` | 150 | Number of falling flakes |
| `FPS` | 30 | Animation framerate |
| `MAX_PILE` | 80 | Max height of the snow pile in px |
| `PILE_RATE` | 0.5 | How fast the pile grows (lower = slower) |

The pile resets whenever you restart the script.

## How it works

- Each monitor gets a fullscreen layer-shell surface on the `OVERLAY` layer, anchored to all four edges. Use `Layer.TOP` instead if you want snow only above normal windows, not above fullscreen ones.
- Click-through comes from shrinking the input region to a 1x1 px corner of the surface.
- Flakes that reach the pile add a soft bump to the height map, which is smoothed every frame. Growth tapers off as the pile nears `MAX_PILE`.

## Troubleshooting

**Shows up as a normal window instead of an overlay.** gtk-layer-shell has to be loaded before libwayland. The script re-execs itself with `LD_PRELOAD` set; if that fails, check that `python -c "import ctypes.util; print(ctypes.util.find_library('gtk-layer-shell'))"` prints something, or set `LD_PRELOAD` to the library path yourself.

**`ModuleNotFoundError: No module named 'gi'`.** You're running a venv Python. Use `/usr/bin/python3`.

**`Requiring namespace 'Gdk' version '3.0', but '4.0' is already loaded`.** Make sure the script has `gi.require_version("Gdk", "3.0")` next to the Gtk one.

**Missing `GtkLayerShell` typelib.** Install `gtk-layer-shell`, not `gtk4-layer-shell`. The script uses GTK3.

**Clicks don't pass through.** The input region is set on `map` and again on `size-allocate`; both are needed on Wayland.

## Known limitations

- Developed and tested on niri only.
- The cursor can't interact with the pile. Wayland gives clients no global pointer position, and making the overlay catch pointer events would break click-through.
