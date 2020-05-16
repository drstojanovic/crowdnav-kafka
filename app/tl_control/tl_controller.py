import traci

from app.config import Config
from app.streaming.producer import Producer


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
            remaining_time = (traci.trafficlight.getNextSwitch(tl_id) - traci.simulation.getCurrentTime()) / 1000.0
            msg = {
                'tl_id': tl_id,
                'remaining_time': remaining_time,
            }
            phase_index = traci.trafficlight.getPhase(tl_id)
            if phase_index != self._tls[tl_id]['current_phase']:
                self._tls[tl_id]['current_phase'] = phase_index
                status = self._tls[tl_id].get(phase_index, None)
                if status == 'many':
                    print('Many vehicles, increasing this TL state duration!')
                    delta_time = remaining_time * (Config().multipliers_many - 1.0)
                elif status == 'few' and remaining_time >= 6:
                    print('Few vehicles, decreasing this TL state duration!')
                    delta_time = remaining_time * (Config().multipliers_few - 1.0)
                elif status == 'none':
                    print('No vehicles, decreasing this TL state duration!')
                    delta_time = remaining_time * (Config().multipliers_none - 1.0)
                else:
                    print('Regular number of vehicles, not changing anything...')
                    delta_time = 0.0
                traci.trafficlight.setPhaseDuration(tl_id, round(remaining_time + delta_time))
                msg['delta_time'] = delta_time
            Producer.publish(msg, Config().kafka_topic_tl_times)
