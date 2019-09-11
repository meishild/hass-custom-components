# yeelight 组件

虽然直接配置成lamp1也能使用，但是由于色温原因可能导致离线。

增加米家台灯PRO支持，由于系统自带的不升级了，fork系统代码，由于服务依赖等原因，不推荐和系统自带的同时配置。

### 打开管理

下载 yeelight app，然后完成添加设备以后，点选设备，选择右下角，选择局域网控制。

### 配置方式
```yaml
custom-yeelight:
  devices:
    10.0.0.64:
      unique_id: living_lamp2_1
      name: living_room_lamp
      model: lamp2
```
