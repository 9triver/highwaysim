import salabim as sim

from highway_sim.config import fitting_data as fit
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.entity.location import TollPlaza, Location
from highway_sim.util.distribution import gamma_distribution


class Car(sim.Component):
    MILLI = 1000

    def setup(self, road, traffic):
        self.road: Road = road
        self.traffic: Traffic = traffic
        self.location: Location = self.road.get_entrance_by_prob()
        self.gantry_num: int = 1
        self.start_time: int = int(self.env.now())
        self.last_time: int = self.start_time

    def process(self):
        if isinstance(self.location, TollPlaza):
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 10
                )
                * self.MILLI
            )
            self.last_time = self.env.now()
        else:
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * self.MILLI
            )
            this_time = self.env.now()
            print(f"this_time {this_time - self.last_time} to pass a gantry")
            self.last_time = this_time
        self.location = self.location.get_next_location(True)
        while len(self.location.downstream) > 0:
            self.gantry_num += 1
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * self.MILLI
            )
            this_time = self.env.now()
            print(f"thisatime {this_time - self.last_time} to pass a gantry")
            self.last_time = this_time
            self.location = self.location.get_next_location(True)
        total_time_used = int(self.env.now()) - self.start_time
        print(f"{self.name()} passed {self.gantry_num} gantry")
        print(f"{self.name()} totalatime {total_time_used} ms")
