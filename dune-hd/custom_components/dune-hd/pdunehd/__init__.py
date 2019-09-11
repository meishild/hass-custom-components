import requests
import re

BASE_COMMAND_URL_FORMAT = "http://{}/cgi-bin/do"

PLAYBACK_SPEED_PLAY = 256
PLAYBACK_SPEED_PAUSE = 0
PLAYBACK_SPEED_FFWD = 512
PLAYBACK_SPEED_RWD = -512

STATE_PARSER = re.compile('.*name="(.*)" value="(.*)"')


class DuneHDPlayer():
    def __init__(self, address):
        self._address = address
        self.update_state()

    def launch_media_url(self, media_url):
        return self.__send_command('launch_media_url', {'media_url': media_url})

    def ui_action_enter(self, item_id):
        return self.__send_command('ui_action_enter', {'item_id': item_id})

    def ui_action_return(self, count=-1):
        return self.__send_command('ui_action_return', {'count': count})

    def play(self):
        return self.__change_playback_speed(PLAYBACK_SPEED_PLAY)

    def pause(self):
        return self.__change_playback_speed(PLAYBACK_SPEED_PAUSE)

    def ffwd(self):
        return self.__change_playback_speed(PLAYBACK_SPEED_FFWD)

    def rwd(self):
        return self.__change_playback_speed(PLAYBACK_SPEED_RWD)

    def stop(self):
        return self.__send_command('standby')

    def update_state(self):
        return self.__send_command('ui_state')

    def turn_on(self):
        return self.__send_ir_code('A05FBF00')

    def turn_off(self):
        return self.__send_ir_code('A15EBF00')

    def previous_track(self):
        return self.__send_ir_code('B649BF00')

    def next_track(self):
        return self.__send_ir_code('E21DBF00')

    def volumeUp(self):
        state = self.update_state()
        return self.__send_command('set_playback_state', {'volume': max(100, int(state.get('playback_volume', 0)) + 10)})

    def volumeDown(self):
        state = self.update_state()
        return self.__send_command('set_playback_state', {'volume': min(0, int(state.get('playback_volume', 0)) - 10)})

    def mute(self, mute=True):
        if mute:
            return self.__send_command('set_playback_state', {'mute': 1})
        else:
            return self.__send_command('set_playback_state', {'mute': 0})

    def get_last_state(self):
        return self._lastState

    def __send_ir_code(self, code):
        return self.__send_command('ir_code', {'ir_code': code})

    def __change_playback_speed(self, newSpeed):
        return self.__send_command('set_playback_state', {'speed': newSpeed})

    def __parse_status(self, status):
        statuses = STATE_PARSER.findall(status)
        self._lastState = {val[0]: val[1] for val in statuses}
        return self._lastState

    def __send_command(self, cmd, params={}):
        params["cmd"] = cmd
        params["result_syntax"] = "json"
        r = requests.get(
            BASE_COMMAND_URL_FORMAT.format(self._address),
            params=params
        )

        if r.status_code == 200:
            self._lastState = r.json()
            return self._lastState
        else:
            raise Exception("Unable to commucate with Dune HD")
