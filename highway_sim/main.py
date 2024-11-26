import logging
import time

import salabim as sim

from highway_sim.components.car_generator import CarGenerator
from highway_sim.config import common
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.stats import default as stats_default

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

# 注意这里的random_seed,不设置或者设置为None都是固定值,salabim的作者有点幽默了
env = sim.Environment(random_seed="*", time_unit="milliseconds")
CarGenerator(road=road, traffic=traffic)
env.run(common.DAY_MILLISECOND * 0.1)

end_time = time.time()
logger.info("spend %fs", end_time - start_time)
stats_default.record(logger)
