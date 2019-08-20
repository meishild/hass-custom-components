# HA-AIRX
`airx的home assistant插件`

#### 配置修改

需要在configuration.yaml中开启packages
```yaml
homeassistant:
  packages: !include_dir_named packages
```

需要自己根据自己的情况修改airx.yaml和secrets.yaml
获取自己的token、userid、deviceid办法
https://bbs.hassbian.com/thread-2113-1-1.html

```yaml
fan:
  - platform: airx
    name: airx
    # 以下信息可通过 https://bbs.hassbian.com/thread-2113-1-1.html 这个帖子里的办法获取
    token: airx000000000000000000000000
    user_id: 000000
    device_id: 000000
```

效果

![图片](https://wx1.sinaimg.cn/large/56e89fd7ly1foydn9uyysj20en0ehjs5.jpg)

![图片](https://wx3.sinaimg.cn/large/56e89fd7ly1foydnyozc8j20b90awmxk.jpg)
