# yeelight组建

虽然直接配置成lamp1也能使用，但是由于色温原因可能导致离线。

增加米家台灯PRO支持，由于系统自带的不升级了，fork系统代码，由于服务依赖等原因，不推荐和系统自带的同时配置。

配置方式
```yaml
custom-yeelight:
  devices:
    10.0.0.64:
      name: living_room_lamp
      model: lamp2
```
