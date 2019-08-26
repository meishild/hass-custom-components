体感温度插件
整合自[yinjiong](https://github.com/yinjiong/HomeAssistant/blob/master/sensor/apparent_temperature.py)
由于新版本更新原因做了整合。

体感温度能更好的反映人对环境冷热的感知，参考算法如下：
体感温度Tg = To + Tu - Tv
To：百叶箱外温度
Tu：湿度对体感温度的订正值
Tv：风速对体感温度的订正值

又查了相关资料，根据NOAA的公式，因为室内，简化了Tv。简单翻译成了py插件，在ha中使用。

使用需要ha中有温度和湿度传感器。

配置方式
```yaml
sensor:
  - platform: apparent-temperature
    name: at01
    temperature_sensor: sensor.m1_temperature 
    humidity_sensor: sensor.m1_humidity
```

其中，
temperature_sensor填写温度传感器的id，单位为摄氏度。
humidity_sensor填写湿度传感器的id，单位为%或0~1的小数。