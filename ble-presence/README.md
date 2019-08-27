# BLE-PRESENCE
`根据蓝牙信号强度计算距离的home assistant插件`

#### 配置修改

```yaml
sensor:
  - platform: ble-presence
    mac: 11:22:33:aa:bb:cc
    name: test
    friendly_name: test
    arg_a: 85
    arg_n: 1.9
```

### 参数说明

* arg_a 是当蓝牙标签与蓝牙基站相距1米时的rssi的绝对值【可选参数，但建议设置】
* arg_n 环境衰减因子【float型】【可选参数，但建议设置】
* name用于entity_id,如上例，将生成sensor.miband2跟sensor.mix2_presence【可选参数】
* friendly_name 【可选参数】
* mac，蓝牙标签的mac地址【必要参数】