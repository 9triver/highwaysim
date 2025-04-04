"""
启动模块
该模块负责初始化日志记录器、设置动画参数、处理鼠标事件以及创建地图窗口等功能
"""
# run `export PYTHONPATH=/extend/school/projects/highwaysim:$PYTHONPATH` before running this file

import logging
import time
import tkinter

from highway_sim.mySalabim import d2_interface_enhanced as sim
from highway_sim.components.car_generator import CarGenerator
from highway_sim.data_parser.road_network import RoadNetwork, Parser as RoadNetworkParser
from highway_sim.data_parser.traffic import Traffic, Parser as TrafficParser
from highway_sim.stats import default as stats_default
from highway_sim.config import common
from dataclasses import dataclass
from highway_sim.config import args


@dataclass
class Pos:
    """
    Pos类用于表示坐标位置
    """
    x: float
    y: float


SCALE_INCREASE_FACTOR = 1.1
SCALE_DECREASE_FACTOR = 0.9

G_SIMULATION_RESOLUTION = 10000
G_SIMULATION_WIDTH_PX = 1000
G_SIMULATION_HEIGHT_PX = 1000

G_MAP_WIDTH = 500
G_MAP_HEIGHT = 500

logger: logging.Logger
start_time: int


def init_logger(enable_log: bool) -> None:
    """
    初始化日志记录器

    Args:
        enable_log (bool): 是否启用日志记录
    """
    global logger, start_time
    if enable_log:
        logging.basicConfig(
            level=args.LOG_LEVEL,
            format="%(message)s",
            filename=args.LOG_FILE,
            filemode="w",
        )
        logger = logging.getLogger(__name__)
        start_time = time.time()


def record(enable_log: bool) -> None:
    """
    记录日志

    Args:
        enable_log (bool): 是否启用日志记录
    """
    global logger, start_time

    if enable_log:
        end_time = time.time()
        logger.info("spend %fs", end_time - start_time)
        stats_default.record(logger)


g_map_scale_factor: float = 1.0
g_map_drag_start_pos: Pos = Pos(0, 0)
g_inspect_start_pos: Pos
g_map_origin_pos: Pos = Pos(0, 0)
g_map_cv: tkinter.Canvas
g_map_origin: int
g_simulation_cv: tkinter.Canvas
g_b3_prompt_rec: int
g_prompt_start_pos: Pos
g_sim_origin: int
# 不能直接修改,因为不是引用
g_sim_global: sim.g


def set_animate(en: sim.Environment, enable_2d: bool, enable_3d: bool) -> None:
    """
    设置动画参数

    Args:
        en (sim.Environment): 环境对象
        enable_2d (bool): 是否启用2D动画
        enable_3d (bool): 是否启用3D动画
    """

    if enable_2d:
        en.position((500, 0))
        en.width(G_SIMULATION_WIDTH_PX)
        en.height(G_SIMULATION_HEIGHT_PX)
        en.x0(0)
        en.y0(0)
        en.x1(G_SIMULATION_RESOLUTION)
        en.animation_parameters(use_toplevel=True)
    if enable_3d:
        en.width3d(G_SIMULATION_WIDTH_PX)
        en.height3d(G_SIMULATION_HEIGHT_PX)
        en.position3d((500 + 1000, 0))

    if enable_2d:
        en.video_close()
        en.show_fps(True)
        en.show_time(True)
        en.show_menu_buttons(True)
        en.animate(True)
        en.speed(3000)
    if enable_3d:
        en.view(
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
        )
        en.camera_auto_print(True)
        en.animate3d(True)
        # 注意这里，不能调用env.animate3d(False)，不设置就好
    if enable_2d:
        global g_map_scale_factor, g_map_drag_start_pos, g_map_origin_pos, g_map_cv, g_simulation_cv, g_sim_origin, g_sim_global
        g_simulation_cv = sim.g.canvas
        g_sim_origin = sim.g.origin_point
        # 不能直接修改,因为不是引用
        g_sim_global = sim.g


def deal_cv_scroll_up(event: tkinter.Event) -> None:
    """
    将鼠标上滑与2d界面缩小绑定
    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
    global g_map_scale_factor, g_map_cv
    g_map_scale_factor *= SCALE_INCREASE_FACTOR
    g_map_cv.scale(
        "all", event.x, event.y, SCALE_INCREASE_FACTOR, SCALE_INCREASE_FACTOR
    )


def deal_cv_scroll_down(event: tkinter.Event) -> None:
    """
    将鼠标下滑与2d界面放大绑定

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
    global g_map_scale_factor, g_map_cv
    g_map_scale_factor *= SCALE_DECREASE_FACTOR
    g_map_cv.scale(
        "all", event.x, event.y, SCALE_DECREASE_FACTOR, SCALE_DECREASE_FACTOR
    )


def deal_cv_left_press(event: tkinter.Event) -> None:
    """
    处理鼠标左键按下事件

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
    global g_map_drag_start_pos
    g_map_drag_start_pos.x = event.x
    g_map_drag_start_pos.y = event.y


def deal_cv_left_motion(event: tkinter.Event) -> None:
    """
    将鼠标左键拖动与2d界面拖动绑定

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
    global g_map_drag_start_pos, g_map_cv
    dx = event.x - g_map_drag_start_pos.x
    dy = event.y - g_map_drag_start_pos.y
    g_map_cv.move("all", dx, dy)
    g_map_drag_start_pos.x = event.x
    g_map_drag_start_pos.y = event.y


def deal_cv_right_press(event: tkinter.Event) -> None:
    """
    处理鼠标右键按下事件

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
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


def deal_cv_right_motion(event: tkinter.Event) -> None:
    """
    将鼠标右键拖动与现实提示框

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
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


def deal_cv_mid_press(event: tkinter.Event) -> None:
    """
    将鼠标中键按下与返回原始2d界面大小绑定

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """

    global g_simulation_cv, g_sim_origin, g_sim_global
    tmp = g_simulation_cv.coords(g_sim_origin)
    origin_x = tmp[0]
    origin_y = tmp[1]
    g_simulation_cv.move("all", -origin_x, -origin_y)
    g_simulation_cv.scale(
        "all", 0, 0, 1 / g_sim_global.scale_factor, 1 / g_sim_global.scale_factor
    )
    g_sim_global.scale_factor = 1


def deal_cv_right_release(event: tkinter.Event) -> None:
    """
    将鼠标右键释放与改变2d界面显示区域绑定

    Args:
        event (tkinter.Event): 鼠标事件对象

    Returns:

    """
    global g_inspect_start_pos, g_map_cv, g_map_origin_pos, g_map_scale_factor, g_inspect_start_pos, rn
    global g_simulation_cv, G_SIMULATION_HEIGHT_PX, G_SIMULATION_WIDTH_PX, G_MAP_HEIGHT, g_sim_global
    screen_pos = Pos(g_map_cv.canvasx(event.x), g_map_cv.canvasy(event.y))
    inspect_end_pos = Pos(
        (screen_pos.x - g_map_origin_pos.x) / g_map_scale_factor,
        (screen_pos.y - g_map_origin_pos.y) / g_map_scale_factor,
    )
    print(inspect_end_pos)

    map_max_height = (
            G_MAP_WIDTH
            / (rn.max_longitude - rn.min_longitude)
            * (rn.max_latitude - rn.min_latitude)
    )
    if g_inspect_start_pos.x < 0:
        g_inspect_start_pos.x = 0
    if g_inspect_start_pos.y < G_MAP_HEIGHT - map_max_height:
        g_inspect_start_pos.y = G_MAP_HEIGHT - map_max_height
    if inspect_end_pos.x > G_MAP_WIDTH:
        inspect_end_pos.x = G_MAP_WIDTH
    if inspect_end_pos.y > G_MAP_HEIGHT:
        inspect_end_pos.y = G_MAP_HEIGHT

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
        sim_height_px = G_SIMULATION_HEIGHT_PX
        sim_width_px = int(G_SIMULATION_WIDTH_PX * rec_width / rec_height)
        # attention to scale parameter
        sim_scale = G_MAP_HEIGHT / rec_height

    else:
        sim_width_px = G_SIMULATION_WIDTH_PX
        sim_height_px = int(G_SIMULATION_HEIGHT_PX * rec_height / rec_width)
        sim_scale = G_MAP_WIDTH / rec_width

    # 从左上角(0, 0)放大,然后拖动
    # g_simulation_window.geometry(f"{sim_width_px}x{sim_height_px}")
    # 如果在获取新的框前有移动sim界面,如何复位?用origin_point和scale
    deal_cv_mid_press(event)
    # 调整y轴:原因: map和simulation的x轴成比例,图像生成时都是x轴固定,y轴可以取任意值,这里只是设定为一样,实际不同,这里的调整原点应该是
    # height- map_max_height
    map2sim = G_SIMULATION_WIDTH_PX / G_MAP_WIDTH
    move_x_px = -(g_inspect_start_pos.x * map2sim)
    move_y_px = -(G_SIMULATION_HEIGHT_PX - (map_max_height * map2sim))
    move_y_px += -((g_inspect_start_pos.y - (G_MAP_HEIGHT - map_max_height)) * map2sim)
    g_simulation_cv.move("all", move_x_px, move_y_px)
    g_simulation_cv.scale("all", 0, 0, sim_scale, sim_scale)
    g_sim_global.scale_factor = sim_scale


def create_map_window(enable_2d: bool) -> None:
    """
    创建地图窗口

    Args:
        enable_2d (bool): 是否启用2D动画

    Returns:

    """
    global G_MAP_WIDTH, G_MAP_HEIGHT, g_map_cv, g_map_origin
    if enable_2d:
        map_window = tkinter.Toplevel()
        map_window.geometry(f"{G_MAP_WIDTH}x{G_MAP_HEIGHT}+0+0")
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


# 需要添加__name__，否则sphinx会尝试运行main，然后报错
if __name__ == "__main__":
    args.Parser()

    init_logger(args.ENABLE_LOG)

    rn = RoadNetwork()
    rnp = RoadNetworkParser(rn)
    traffic = Traffic()
    tp = TrafficParser(traffic)
    rnp.parse()
    tp.parse()

    real_root = tkinter.Tk()
    real_root.withdraw()

    # 注意这里的random_seed,不设置或者设置为None都是固定值
    env = sim.Environment(random_seed="*", time_unit="milliseconds")

    CarGenerator(road_network=rn, traffic=traffic)

    set_animate(env, args.ENABLE_2D, args.ENABLE_3D)

    create_map_window(args.ENABLE_2D)
    # visualization
    if args.ENABLE_2D:
        rn.draw(g_map_cv, G_MAP_WIDTH, G_MAP_HEIGHT)
        # 注意,这里不能传入resolution,因为直接调用tkinter
        rn.draw(
            g_simulation_cv, G_SIMULATION_WIDTH_PX, G_SIMULATION_HEIGHT_PX, "red", False
        )

    env.run(common.DAY_MILLISECOND * 0.01)

    record(args.ENABLE_LOG)
