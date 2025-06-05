from . import MaxPressureAgent
from common.registry import Registry
from collections import defaultdict


@Registry.register_model('gplight')
class GPLight(MaxPressureAgent):
    ARITY = 16

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule = None

    def get_action(self, ob, phase, test=True):
        # get lane pressure
        lvc = self.world.get_info("lane_count")
        lvw = self.world.get_info("lane_waiting_count")
        if self.inter_obj.current_phase_time < self.t_min:
            return self.inter_obj.current_phase

        max_pressure = None
        action = -1
        for phase_id in range(len(self.inter_obj.phases)):
            lanelinks = [(start, end)
                 for start, end in self.inter_obj.phase_available_lanelinks[phase_id]
                 if not start.endswith('2')]

            fr_set, tolist = [], []
            for fr, to in lanelinks:
                fr_set.append(fr);
                tolist.append(to)
            t = [lvw[fr_set[0]], lvw[fr_set[-1]]]
            t.extend([lvw[i] for i in tolist])

            t.extend([lvc[fr_set[0]], lvc[fr_set[-1]]])
            t.extend([lvc[i] for i in tolist])

            pressure = self.rule(*t)
            if max_pressure is None or pressure > max_pressure:
                action = phase_id
                max_pressure = pressure

        return action
