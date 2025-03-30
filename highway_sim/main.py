import logging
import time
import tkinter

from mySalabim import d2_interface_enhanced as sim

from highway_sim.components.car_generator import CarGenerator
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.stats import default as stats_default
from highway_sim.config import common
from dataclasses import dataclass

ENABLE_3D = True
ENABLE_2D = True
ENABLE_LOG = True

if ENABLE_LOG:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename="../statistics.log",
        filemode="w",
    )
    logger = logging.getLogger(__name__)
    start_time = time.time()

road = Road()
traffic = Traffic()
road.parse()
traffic.parse()

real_root = tkinter.Tk()
real_root.withdraw()

# 注意这里的random_seed,不设置或者设置为None都是固定值
env = sim.Environment(random_seed="*", time_unit="milliseconds")

env.animation_parameters(use_toplevel=True)
CarGenerator(road=road, traffic=traffic)

env.position((500, 0))
g_simulation_resolution = 10000
g_simulation_width_px = 1000
g_simulation_height_px = 1000
env.width(g_simulation_width_px)
env.height(g_simulation_height_px)
if ENABLE_3D:
    env.width3d(g_simulation_width_px)
    env.height3d(g_simulation_height_px)
    env.position3d((500 + 1000, 0))

env.x0(0)
env.y0(0)
env.x1(g_simulation_resolution)

env.view(
    # x_center=5000,
    # y_center=5000,
    # z_center=0,
    # x_eye=500,
    # y_eye=-100,
    # z_eye=100,
    x_center=5000,
    y_center=5000,
    z_center=0,
    x_eye=5000,
    y_eye=-1000,
    z_eye=10000,
    # field_of_view_y=30,
    # x_eye=-6.9024,
    # y_eye=-95.8334,
    # z_eye=30.0000,
    # x_center=93.4761,
    # y_center=623.7552,
    # z_center=0.0000,
    # field_of_view_y=55.5556,
    # x_eye=176.9024,
    # y_eye=295.8334,
    # z_eye=30.0000,
    # x_center=993.4761,
    # y_center=123.7552,
    # z_center=0.0000,
    # field_of_view_y=55.5556,
)

if ENABLE_2D:
    env.video_close()
    env.show_fps(True)
    env.show_time(True)
    env.show_menu_buttons(True)
    env.camera_auto_print(True)
    env.animate(True)
else:
    env.animate(False)
if ENABLE_3D:
    env.animate3d(True)
else:
    env.animate(False)
env.speed(3000)

###
SCALE_INCREASE_FACTOR = 1.1
SCALE_DECREASE_FACTOR = 0.9


###
@dataclass
class Pos:
    x: float
    y: float


###
if ENABLE_2D:
    g_map_width = 500
    g_map_height = 500
    g_map_resolution = g_map_width
    g_map_scale_factor = 1.0
    g_map_drag_start_pos = Pos(0, 0)
    g_inspect_start_pos = Pos(0, 0)
    g_map_origin_pos = Pos(0, 0)
    g_map_cv: tkinter.Canvas = None
    g_map_origin: int = 0
    g_simulation_window = env.root
    g_simulation_cv: tkinter.Canvas = sim.g.canvas
    g_b3_prompt_rec: int = -1
    g_prompt_start_pos: Pos = Pos(0, 0)
    g_sim_origin = sim.g.origin_point
    # 不能直接修改,因为不是引用
    g_sim_global = sim.g


# handler
def deal_cv_scroll_up(event):
    global g_map_scale_factor, g_map_cv
    g_map_scale_factor *= SCALE_INCREASE_FACTOR
    g_map_cv.scale(
        "all", event.x, event.y, SCALE_INCREASE_FACTOR, SCALE_INCREASE_FACTOR
    )


def deal_cv_scroll_down(event):
    global g_map_scale_factor, g_map_cv
    g_map_scale_factor *= SCALE_DECREASE_FACTOR
    g_map_cv.scale(
        "all", event.x, event.y, SCALE_DECREASE_FACTOR, SCALE_DECREASE_FACTOR
    )


def deal_cv_left_press(event):
    global g_map_drag_start_pos
    g_map_drag_start_pos.x = event.x
    g_map_drag_start_pos.y = event.y


def deal_cv_left_motion(event):
    global g_map_drag_start_pos, g_map_cv
    dx = event.x - g_map_drag_start_pos.x
    dy = event.y - g_map_drag_start_pos.y
    g_map_cv.move("all", dx, dy)
    g_map_drag_start_pos.x = event.x
    g_map_drag_start_pos.y = event.y


def deal_cv_right_press(event):
    global g_inspect_start_pos, g_map_cv, g_map_origin, g_map_origin_pos, g_map_scale_factor, g_prompt_start_pos
    tmp = g_map_cv.coords(g_map_origin)
    g_map_origin_pos.x = tmp[0]
    g_map_origin_pos.y = tmp[1]

    screen_pos = Pos(g_map_cv.canvasx(event.x), g_map_cv.canvasy(event.y))

    g_inspect_start_pos = Pos(
        (screen_pos.x - g_map_origin_pos.x) / g_map_scale_factor,
        (screen_pos.y - g_map_origin_pos.y) / g_map_scale_factor,
    )
    g_prompt_start_pos = Pos(screen_pos.x, screen_pos.y)
    print(g_inspect_start_pos)


def deal_cv_right_motion(event):
    global g_b3_prompt_rec, g_map_cv, g_prompt_start_pos
    screen_pos = Pos(g_map_cv.canvasx(event.x), g_map_cv.canvasy(event.y))
    if g_b3_prompt_rec != -1:
        g_map_cv.delete(g_b3_prompt_rec)
    g_b3_prompt_rec = g_map_cv.create_rectangle(
        g_prompt_start_pos.x,
        g_prompt_start_pos.y,
        screen_pos.x,
        screen_pos.y,
        outline="red",
    )


def deal_cv_mid_press(event):
    global g_simulation_cv, g_sim_origin, g_sim_global
    tmp = g_simulation_cv.coords(g_sim_origin)
    origin_x = tmp[0]
    origin_y = tmp[1]
    g_simulation_cv.move("all", -origin_x, -origin_y)
    g_simulation_cv.scale(
        "all", 0, 0, 1 / g_sim_global.scale_factor, 1 / g_sim_global.scale_factor
    )
    g_sim_global.scale_factor = 1


def deal_cv_right_release(event):
    global g_inspect_start_pos, g_map_cv, g_map_origin_pos, g_map_scale_factor, g_inspect_start_pos, road
    global g_simulation_cv, g_simulation_height_px, g_simulation_width_px, g_map_height, g_sim_global
    screen_pos = Pos(g_map_cv.canvasx(event.x), g_map_cv.canvasy(event.y))
    inspect_end_pos = Pos(
        (screen_pos.x - g_map_origin_pos.x) / g_map_scale_factor,
        (screen_pos.y - g_map_origin_pos.y) / g_map_scale_factor,
    )
    print(inspect_end_pos)

    map_max_height = (
            g_map_width
            / (road.max_longitude - road.min_longitude)
            * (road.max_latitude - road.min_latitude)
    )
    if g_inspect_start_pos.x < 0:
        g_inspect_start_pos.x = 0
    if g_inspect_start_pos.y < g_map_height - map_max_height:
        g_inspect_start_pos.y = g_map_height - map_max_height
    if inspect_end_pos.x > g_map_width:
        inspect_end_pos.x = g_map_width
    if inspect_end_pos.y > g_map_height:
        inspect_end_pos.y = g_map_height

    if (
            inspect_end_pos.x <= g_inspect_start_pos.x
            or inspect_end_pos.y <= g_inspect_start_pos.y
    ):
        return
    rec_height = abs(inspect_end_pos.y - g_inspect_start_pos.y)
    rec_width = abs(inspect_end_pos.x - g_inspect_start_pos.x)

    sim_height_px, sim_width_px = 0, 0
    sim_heigth_res, sim_width_res = 0, 0
    sim_scale = 1.0
    if rec_height > rec_width:
        sim_height_px = g_simulation_height_px
        sim_width_px = int(g_simulation_width_px * rec_width / rec_height)
        # attention to scale parameter
        sim_scale = g_map_height / rec_height

    else:
        sim_width_px = g_simulation_width_px
        sim_height_px = int(g_simulation_height_px * rec_height / rec_width)
        sim_scale = g_map_width / rec_width

    # 从左上角(0, 0)放大,然后拖动
    # g_simulation_window.geometry(f"{sim_width_px}x{sim_height_px}")
    # 如果在获取新的框前有移动sim界面,如何复位?用origin_point和scale
    deal_cv_mid_press(event)
    # 调整y轴:原因: map和simulation的x轴成比例,图像生成时都是x轴固定,y轴可以取任意值,这里只是设定为一样,实际不同,这里的调整原点应该是
    # height- map_max_height
    map2sim = g_simulation_width_px / g_map_width
    move_x_px = -(g_inspect_start_pos.x * map2sim)
    move_y_px = -(g_simulation_height_px - (map_max_height * map2sim))
    move_y_px += -((g_inspect_start_pos.y - (g_map_height - map_max_height)) * map2sim)
    g_simulation_cv.move("all", move_x_px, move_y_px)
    g_simulation_cv.scale("all", 0, 0, sim_scale, sim_scale)
    g_sim_global.scale_factor = sim_scale


# visualization
if ENABLE_2D:
    map_window = tkinter.Toplevel()
    map_window.geometry(f"{g_map_width}x{g_map_height}+0+0")
    g_map_cv = tkinter.Canvas(map_window, bg="white")
    g_map_origin = g_map_cv.create_oval(0, 0, 0, 0, fill="white", outline="white")

    g_map_cv.bind("<Button-4>", deal_cv_scroll_up)
    g_map_cv.bind("<Button-5>", deal_cv_scroll_down)
    g_map_cv.bind("<Button-1>", deal_cv_left_press)
    g_map_cv.bind("<B1-Motion>", deal_cv_left_motion)
    g_map_cv.bind("<Button-3>", deal_cv_right_press)
    g_map_cv.bind("<ButtonRelease-3>", deal_cv_right_release)
    g_map_cv.bind("<B3-Motion>", deal_cv_right_motion)
    g_map_cv.bind("<Button-2>", deal_cv_mid_press)

    g_map_cv.pack(fill="both", expand=True)

    road.draw_map(g_map_cv, g_map_width, g_map_height)
    # 注意,这里不能传入resolution,因为直接调用tkinter
    road.draw_map(
        g_simulation_cv, g_simulation_width_px, g_simulation_height_px, "red", False
    )

# map_window.mainloop()

###


env.run(common.DAY_MILLISECOND * 1)

if ENABLE_LOG:
    end_time = time.time()
    logger.info("spend %fs", end_time - start_time)
    stats_default.record(logger)
