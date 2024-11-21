import salabim as sim

from highway_sim.components.car_generator import CarGenerator
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic

road = Road()
traffic = Traffic()

road.parse()
traffic.parse()
with open("log.log", "w") as log:
    env = sim.Environment(trace=log)
    CarGenerator(road=road, traffic=traffic)
    # 7天
    env.run(100000)
