import salabim as sim
from scipy.stats import uniform

from components.car import Car
from config import fitting_data as fit


class CarGenerator(sim.Component):
    def setup(self, road, traffic):
        self.road = road
        self.traffic = traffic

    def process(self):
        while True:
            Car(road=self.road, traffic=self.traffic)
            self.hold(self.gen_interval_ms())

    def gen_interval_ms(self) -> int:
        hour: int = int(self.env.now() / (60 * 60 * 1000)) % 24
        interval1 = self.traffic.hour_2_interval_ms[(hour + 23) % 24]
        interval2 = self.traffic.hour_2_interval_ms[hour]
        interval3 = self.traffic.hour_2_interval_ms[(hour + 1) % 24]
        low = min(interval1, interval2, interval3) - 5
        high = max(interval1, interval2, interval3) + 5
        return int(uniform(low, high).rvs() * (1 - fit.PROVINCE_ENTRANCE_RATION))