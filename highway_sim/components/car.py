import logging

import salabim as sim

from highway_sim.config import common
from highway_sim.config import fitting_data as fit
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.entity.location import TollPlaza, Location
from highway_sim.stats import default as stats_default
from highway_sim.util.distribution import gamma_distribution

logger = logging.getLogger(__name__)


class Car(sim.Component):

    def setup(self, road, traffic):
        self.road: Road = road
        self.traffic: Traffic = traffic
        self.location: Location = self.road.get_entrance_by_prob()
        self.gantry_num: int = 1
        self.start_time: float = self.env.now()
        # self.last_time: float = self.start_time

    def process(self):
        stats_default.entry_hour_info(self.env.now(), logger)
        stats_default.entry_hex_info(self.location.hex_code, logger)
        if isinstance(self.location, TollPlaza):
            self.hold(
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 10
                )
                * common.SECOND_MILLISECOND
            )
            # self.last_time = self.env.now()
        else:
            duration = (
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * common.SECOND_MILLISECOND
            )
            self.hold(duration)
            stats_default.gantry_time_info(duration, logger)
        self.location = self.location.get_next_location(True)
        while len(self.location.downstream) > 0:
            self.gantry_num += 1
            duration = (
                gamma_distribution(
                    fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                )
                * common.SECOND_MILLISECOND
            )
            self.hold(duration)
            stats_default.gantry_time_info(duration, logger)
            self.location = self.location.get_next_location(True)
        now = self.env.now()
        stats_default.num_passed_info(self.gantry_num, logger)
        stats_default.total_time_info(now, self.start_time, logger)
        stats_default.exit_hour_info(now, logger)
        stats_default.exit_hex_info(self.location.hex_code, logger)
