import traci

from app.config import Config


class TLController:
    def __init__(self):
        self._tls = {}
        self._performed_phase_action = False

    def update_tls(self, tl_status_list):
        for s in tl_status_list:
            id = s['traffic_light']['id']
            green_phases = set(s['traffic_light']['green_phases'])
            status = s['status']
            if id not in self._tls:
                self._tls[id] = {'current_phase': -1}
            for phase_idx in green_phases:
                self._tls[id][phase_idx] = status

        self._perform_actions()

    def _perform_actions(self):
        for tl_id, statuses in self._tls.items():
            phase_index = traci.trafficlight.getPhase(tl_id)
            if phase_index == self._tls[tl_id]['current_phase']:
                return
            self._tls[tl_id]['current_phase'] = phase_index
            status = self._tls[tl_id].get(phase_index, None)
            remaining_time = (traci.trafficlight.getNextSwitch(tl_id) - traci.simulation.getCurrentTime()) / 1000
            if status == 'many':
                print('Many vehicles, increasing this TL state duration!')
                remaining_time = int(remaining_time * Config().multipliers_many)
            elif status == 'few' and remaining_time >= 6:
                print('Few vehicles, decreasing this TL state duration!')
                remaining_time = int(remaining_time * Config().multipliers_few)
            elif status == 'none':
                print('No vehicles, skipping this TL state!')
                remaining_time = int(remaining_time * Config().multipliers_none)
            else:
                print('Regular number of vehicles, not changing anything...')
            traci.trafficlight.setPhaseDuration(tl_id, remaining_time)
