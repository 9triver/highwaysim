import salabim as sim

from components.car_generator import CarGenerator
from data_parser_and_holder.traffic import Traffic
from highway_sim.data_parser_and_holder.road import Road

road = Road()
traffic = Traffic()

road.parse()
traffic.parse()
with open("log.log", "w") as log:
    env = sim.Environment(trace=log)
    CarGenerator(road=road, traffic=traffic)
    env.run(1000000)
