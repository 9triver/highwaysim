import salabim as sim
from scipy.stats import uniform

from components.car import Car
from config import fitting_data as fit
from data_parser_and_holder.traffic import Traffic


class CarGenerator(sim.Component):
    def setup(self):
        pass

    def process(self):
        Car()
        self.hold(self.gen_interval_ms())

    def gen_interval_ms(self) -> int:
        hour: int = int(self.env.now() / (60 * 60 * 1000)) % 24
        interval1 = Traffic.hour_2_interval_ms[(hour + 23) % 24]
        interval2 = Traffic.hour_2_interval_ms[hour]
        interval3 = Traffic.hour_2_interval_ms[(hour + 1) % 24]
        low = min(interval1, interval2, interval3) - 5
        high = max(interval1, interval2, interval3) + 5
        return int(uniform(low, high) * (1 - fit.PROVINCE_ENTRANCE_RATION))
