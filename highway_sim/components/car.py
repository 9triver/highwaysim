import salabim as sim

from config import fitting_data as fit
from entity.location import TollPlaza
from util.distribution import gamma_distribution


class Car(sim.Component):
    MILLI = 1000

    def setup(self, road, traffic):
        self.road = road
        self.traffic = traffic
        self.location = self.road.get_entrance_by_prob()

    def process(self):
        if isinstance(self.location, TollPlaza):
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 10
                )
                * self.MILLI
            )
        else:
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * self.MILLI
            )
        self.location = self.location.get_next_location(True)
        while len(self.location.downstream) > 0:
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * self.MILLI
            )
            self.location = self.location.get_next_location(True)
