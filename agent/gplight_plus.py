from . import MaxPressureAgent
from common.registry import Registry
from collections import defaultdict


@Registry.register_model('gplight_plus')
class GPLightPlus(MaxPressureAgent):
    ARITY = 8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule = None

    def get_action(self, ob, phase, test=True):

        lvw = self.world.get_info("lane_waiting_count")
        lvc = self.world.get_info("lane_count")
        if self.inter_obj.current_phase_time < self.t_min:
            return self.inter_obj.current_phase

        max_urgency = None
        action = -1
        for phase_id in range(len(self.inter_obj.phases)):
            lane_links = [(start, end)
                          for start, end in self.inter_obj.phase_available_lanelinks[phase_id]
                          if not start.endswith('2')]
            # TODO: start.endswith('2') is only applicable to three-lane scenarios

            list_dict = defaultdict(list)
            for key, value in lane_links:
                list_dict[key].append(value)
            TMs = [[key] + sorted(values) for key, values in list_dict.items()]

            urgency = 0.0
            for tm in TMs:
                t = [lvw[lane] for lane in tm]
                t.extend([lvc[lane] for lane in tm])
                urgency += self.rule(*t)

            if max_urgency is None or urgency > max_urgency:
                action = phase_id
                max_urgency = urgency

        return action
