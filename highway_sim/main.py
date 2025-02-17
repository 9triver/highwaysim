import logging
import time

import salabim as sim

from highway_sim.components.car_generator import CarGenerator
from highway_sim.config import common
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.stats import default as stats_default

# CENTER_Latitude = 31.0
# CENTER_Longitude = 121.0
# window_length = 0.1
# window_width = 0.1
# display_length = 0.1

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

# 注意这里的random_seed,不设置或者设置为None都是固定值
env = sim.Environment(random_seed="*", time_unit="milliseconds")
CarGenerator(road=road, traffic=traffic)

env.run(common.DAY_MILLISECOND * 1)
env.speed(0)

end_time = time.time()
logger.info("spend %fs", end_time - start_time)
stats_default.record(logger)
