import json
import os
import sys
import unittest

from yeelight import Bulb, Flow, TemperatureTransition, enums
from yeelight.enums import LightType, SceneClass
from yeelight.flow import Action

sys.path.insert(0, os.path.abspath(__file__ + "/../.."))


class SocketMock(object):
    def __init__(self, received=b'{"id": 0, "result": ["ok"]}'):
        self.received = received

    def send(self, data):
        self.sent = json.loads(data.decode("utf8"))

    def recv(self, length):
        return self.received


class Tests(unittest.TestCase):
    def setUp(self):
        self.socket = SocketMock()
        self.bulb = Bulb(ip="", auto_on=True)
        self.bulb._Bulb__socket = self.socket

    def test_rgb1(self):
        self.bulb.set_rgb(255, 255, 0)
        self.assertEqual(self.socket.sent["method"], "set_rgb")
        self.assertEqual(self.socket.sent["params"], [16776960, "smooth", 300])

    def test_rgb2(self):
        self.bulb.effect = "sudden"
        self.bulb.set_rgb(255, 255, 0)
        self.assertEqual(self.socket.sent["method"], "set_rgb")
        self.assertEqual(self.socket.sent["params"], [16776960, "sudden", 300])

    def test_rgb3(self):
        self.bulb.set_rgb(255, 255, 0, effect="sudden")
        self.assertEqual(self.socket.sent["method"], "set_rgb")
        self.assertEqual(self.socket.sent["params"], [16776960, "sudden", 300])

    def test_hsv1(self):
        self.bulb.set_hsv(200, 100, effect="sudden")
        self.assertEqual(self.socket.sent["method"], "set_hsv")
        self.assertEqual(self.socket.sent["params"], [200, 100, "sudden", 300])

    def test_hsv2(self):
        self.bulb.set_hsv(200, 100, 10, effect="sudden", duration=500)
        self.assertEqual(self.socket.sent["method"], "start_cf")
        self.assertEqual(self.socket.sent["params"], [1, 1, "50, 1, 43263, 10"])

    def test_hsv3(self):
        self.bulb.set_hsv(200, 100, 10, effect="smooth", duration=1000)
        self.assertEqual(self.socket.sent["method"], "start_cf")
        self.assertEqual(self.socket.sent["params"], [1, 1, "1000, 1, 43263, 10"])

    def test_hsv4(self):
        self.bulb.effect = "sudden"
        self.bulb.set_hsv(200, 100, 10, effect="smooth", duration=1000)
        self.assertEqual(self.socket.sent["method"], "start_cf")
        self.assertEqual(self.socket.sent["params"], [1, 1, "1000, 1, 43263, 10"])

    def test_toggle1(self):
        self.bulb.toggle()
        self.assertEqual(self.socket.sent["method"], "toggle")
        self.assertEqual(self.socket.sent["params"], ["smooth", 300])

        self.bulb.toggle(duration=3000)
        self.assertEqual(self.socket.sent["params"], ["smooth", 3000])

    def test_turn_off1(self):
        self.bulb.turn_off()
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["off", "smooth", 300])

        self.bulb.turn_off(duration=3000)
        self.assertEqual(self.socket.sent["params"], ["off", "smooth", 3000])

    def test_turn_on1(self):
        self.bulb.turn_on()
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300])

        self.bulb.turn_on(duration=3000)
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 3000])

    def test_turn_on2(self):
        self.bulb.effect = "sudden"
        self.bulb.turn_on()
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "sudden", 300])

    def test_turn_on3(self):
        self.bulb.turn_on(effect="sudden", duration=50)
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "sudden", 50])

    def test_turn_on4(self):
        self.bulb.power_mode = enums.PowerMode.MOONLIGHT
        self.bulb.turn_on()
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300, enums.PowerMode.MOONLIGHT.value])

    def test_turn_on5(self):
        self.bulb.turn_on(power_mode=enums.PowerMode.MOONLIGHT)
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300, enums.PowerMode.MOONLIGHT.value])

    def test_set_power_mode1(self):
        self.bulb.set_power_mode(enums.PowerMode.MOONLIGHT)
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300, enums.PowerMode.MOONLIGHT.value])

    def test_set_power_mode2(self):
        self.bulb.set_power_mode(enums.PowerMode.NORMAL)
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300, enums.PowerMode.NORMAL.value])

    def test_set_power_mode3(self):
        self.bulb.set_power_mode(enums.PowerMode.LAST)
        self.assertEqual(self.socket.sent["method"], "set_power")
        self.assertEqual(self.socket.sent["params"], ["on", "smooth", 300])

    def test_color_temp1(self):
        self.bulb.set_color_temp(1400)
        self.assertEqual(self.socket.sent["method"], "set_ct_abx")
        self.assertEqual(self.socket.sent["params"], [1700, "smooth", 300])

        self.bulb.set_color_temp(1400, duration=3000)
        self.assertEqual(self.socket.sent["params"], [1700, "smooth", 3000])

    def test_color_temp2(self):
        self.bulb.set_color_temp(8400, effect="sudden")
        self.assertEqual(self.socket.sent["method"], "set_ct_abx")
        self.assertEqual(self.socket.sent["params"], [6500, "sudden", 300])

    def test_color_temp_with_model_declared(self):
        self.bulb.model = "ceiling2"
        self.bulb.set_color_temp(1800)
        self.assertEqual(self.socket.sent["method"], "set_ct_abx")
        self.assertEqual(self.socket.sent["params"], [2700, "smooth", 300])

    def test_start_flow(self):
        transitions = [TemperatureTransition(1700, duration=40000), TemperatureTransition(6500, duration=40000)]
        flow = Flow(count=1, action=Action.stay, transitions=transitions)
        self.bulb.start_flow(flow)
        self.assertEqual(self.socket.sent["method"], "start_cf")
        self.assertEqual(self.socket.sent["params"], [2, 1, "40000, 2, 1700, 100, 40000, 2, 6500, 100"])

    def test_set_scene_color(self):
        self.bulb.set_scene(SceneClass.COLOR, 255, 255, 0, 10)
        self.assertEqual(self.socket.sent["method"], "set_scene")
        self.assertEqual(self.socket.sent["params"], ["color", 16776960, 10])

    def test_set_scene_color_ambilight(self):
        self.bulb.set_scene(SceneClass.COLOR, 255, 255, 0, 10, light_type=LightType.Ambient)
        self.assertEqual(self.socket.sent["method"], "bg_set_scene")
        self.assertEqual(self.socket.sent["params"], ["color", 16776960, 10])

    def test_set_scene_color_temperature(self):
        self.bulb.set_scene(SceneClass.CT, 2000, 15)
        self.assertEqual(self.socket.sent["method"], "set_scene")
        self.assertEqual(self.socket.sent["params"], ["ct", 2000, 15])

    def test_set_scene_hsv(self):
        self.bulb.set_scene(SceneClass.HSV, 200, 100, 10)
        self.assertEqual(self.socket.sent["method"], "set_scene")
        self.assertEqual(self.socket.sent["params"], ["hsv", 200, 100, 10])

    def test_set_scene_color_flow(self):
        transitions = [TemperatureTransition(1700, duration=40000), TemperatureTransition(6500, duration=40000)]
        flow = Flow(count=1, action=Action.stay, transitions=transitions)
        self.bulb.set_scene(SceneClass.CF, flow)
        self.assertEqual(self.socket.sent["method"], "set_scene")
        self.assertEqual(self.socket.sent["params"], ["cf", 2, 1, "40000, 2, 1700, 100, 40000, 2, 6500, 100"])

    def test_set_scene_auto_delay_off(self):
        self.bulb.set_scene(SceneClass.AUTO_DELAY_OFF, 20, 1)
        self.assertEqual(self.socket.sent["method"], "set_scene")
        self.assertEqual(self.socket.sent["params"], ["auto_delay_off", 20, 1])


if __name__ == "__main__":
    unittest.main()
