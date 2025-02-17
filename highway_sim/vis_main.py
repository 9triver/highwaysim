from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set

from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.entity.location import Location

import tkinter as tk

###
SCALE_INCREASE_FACTOR = 1.1
SCALE_DECREASE_FACTOR = 0.9


###
@dataclass
class Pos:
    x: float
    y: float


###
g_width = 800
g_height = 600
g_scale_factor = 1.0
g_drag_start_pos = Pos(0, 0)
g_inspect_start_pos = Pos(0, 0)
g_origin_pos = Pos(0, 0)
g_cv: tk.Canvas = None
g_origin: int = 0


# data parse
road = Road()
traffic = Traffic()
road.parse()
traffic.parse()

gantries = list(road.hex_2_gantry.values())
gantry_num = len(gantries)
min_latitude = 90
max_latitude = -90
min_longitude = 180
max_longitude = -180
for g in gantries:
    min_latitude = min(min_latitude, g.latitude)
    max_latitude = max(max_latitude, g.latitude)
    min_longitude = min(min_longitude, g.longitude)
    max_longitude = max(max_longitude, g.longitude)


# handler
def deal_cv_scroll_up(event):
    global g_scale_factor, g_cv
    g_scale_factor *= SCALE_INCREASE_FACTOR
    g_cv.scale("all", event.x, event.y, SCALE_INCREASE_FACTOR, SCALE_INCREASE_FACTOR)


def deal_cv_scroll_down(event):
    global g_scale_factor, g_cv
    g_scale_factor *= SCALE_DECREASE_FACTOR
    g_cv.scale("all", event.x, event.y, SCALE_DECREASE_FACTOR, SCALE_DECREASE_FACTOR)


def deal_cv_left_press(event):
    global g_drag_start_pos
    g_drag_start_pos.x = event.x
    g_drag_start_pos.y = event.y


def deal_cv_left_motion(event):
    global g_drag_start_pos, g_cv
    dx = event.x - g_drag_start_pos.x
    dy = event.y - g_drag_start_pos.y
    g_cv.move("all", dx, dy)
    g_drag_start_pos.x = event.x
    g_drag_start_pos.y = event.y


def deal_cv_right_press(event):
    global g_inspect_start_pos, g_cv, g_origin, g_origin_pos, g_scale_factor
    tmp = g_cv.coords(g_origin)
    g_origin_pos.x = tmp[0]
    g_origin_pos.y = tmp[1]

    screen_pos = Pos(g_cv.canvasx(event.x), g_cv.canvasy(event.y))

    g_inspect_start_pos = Pos(
        (screen_pos.x - g_origin_pos.x) / g_scale_factor,
        (screen_pos.y - g_origin_pos.y) / g_scale_factor,
    )
    print(g_inspect_start_pos)


def deal_cv_right_release(event):
    global g_inspect_start_pos, g_cv, g_origin_pos, g_scale_factor
    screen_pos = Pos(g_cv.canvasx(event.x), g_cv.canvasy(event.y))
    inspect_end_pos = Pos(
        (screen_pos.x - g_origin_pos.x) / g_scale_factor,
        (screen_pos.y - g_origin_pos.y) / g_scale_factor,
    )
    print(inspect_end_pos)


# common func
def lon2x(lon: float) -> float:
    return (lon - min_longitude) / (max_longitude - min_longitude) * g_width


def lat2y(lat: float) -> float:
    return g_height - ((lat - min_latitude) / (max_longitude - min_longitude) * g_width)


def draw_map():
    global g_cv
    hex_drawn: Set[str] = set()

    def draw_gantry(gantry: Location, prev: Location = None):
        if gantry.hex_code in hex_drawn:
            return
        x = lon2x(gantry.longitude)
        y = lat2y(gantry.latitude)
        hex_drawn.add(gantry.hex_code)
        tag = g_cv.create_oval(x - 2, y - 2, x + 2, y + 2, fill="gray")
        g_cv.tag_bind(tag, "<Button-1>", lambda event: print(gantry.name))
        if prev:
            x_prev = lon2x(prev.longitude)
            y_prev = lat2y(prev.latitude)
            g_cv.create_line(x_prev, y_prev, x, y, width=1, fill="black")
        for e in gantry.downstream:
            draw_gantry(e.l, gantry)

    for entry in road.hex_2_entrance.values():
        if entry.hex_code not in hex_drawn:
            draw_gantry(entry)


# visualization
root = tk.Tk()
root.geometry(f"{g_width}x{g_height}")

g_cv = tk.Canvas(root, bg="white")

g_origin = g_cv.create_oval(0, 0, 0, 0, fill="white", outline="white")
circle = g_cv.create_oval(
    g_width / 2, g_height / 2, g_width / 2 + 100, g_height / 2 + 100, fill="green"
)

g_cv.bind("<Button-4>", deal_cv_scroll_up)
g_cv.bind("<Button-5>", deal_cv_scroll_down)
g_cv.bind("<Button-1>", deal_cv_left_press)
g_cv.bind("<B1-Motion>", deal_cv_left_motion)
g_cv.bind("<Button-3>", deal_cv_right_press)
g_cv.bind("<ButtonRelease-3>", deal_cv_right_release)
g_cv.tag_bind(
    circle,
    "<Button-1>",
    lambda event: g_cv.create_oval(
        g_width / 2, g_height / 2, g_width / 2 + 100, g_height / 2 + 100, fill="green"
    ),
)

g_cv.pack(fill="both", expand=True)

# draw_map()

root.mainloop()
