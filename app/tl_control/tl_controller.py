import traci


class TLController:
    def __init__(self):
        self._tls = {}
        self._performed_phase_action = False

    def update_tls(self, tl_actions_list):
        for a in tl_actions_list:
            id = a['traffic_light']['id']
            green_phases = set(a['traffic_light']['green_phases'])
            action = a['action']
            if id not in self._tls:
                self._tls[id] = {'current_phase': -1}
            for phase_idx in green_phases:
                self._tls[id][phase_idx] = action

        self._perform_actions()

    def _perform_actions(self):
        with open('/tmp/tl_actions_log.txt', 'a') as f:
            for tl_id, actions in self._tls.items():
                phase_index = traci.trafficlight.getPhase(tl_id)
                if phase_index == self._tls[tl_id]['current_phase']:
                    f.write('Still same phase...\n')
                    return
                self._tls[tl_id]['current_phase'] = phase_index
                f.write('New phase is %s\n' % phase_index)
                action = self._tls[tl_id].get(phase_index, None)
                f.write('Performing action: %s\n' % action)
                remaining_time = (traci.trafficlight.getNextSwitch(tl_id) - traci.simulation.getCurrentTime()) / 1000
                f.write('Remaining time is %s\n' % remaining_time)
                if action == 'prolong':
                    remaining_time = int(remaining_time * 1.5)
                elif action == 'shorten' and remaining_time >= 6:
                    remaining_time = int(remaining_time * 0.5)
                f.write('Setting remaining time to %s\n' % remaining_time)
                traci.trafficlight.setPhaseDuration(tl_id, remaining_time)
