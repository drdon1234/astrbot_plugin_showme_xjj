# 适配 AstrBot 的随机小姐姐美图短视频插件

## 安装方法

1. **通过 插件市场 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右上角 Search"  
- 搜索任何与本项目相关的关键词，找到插件后点击安装
- 推荐通过唯一标识符搜索：```astrbot_plugin_showme_xjj```

2. **通过 Github仓库链接 安装**  
- 打开 "AstrBot WebUI" -> "插件市场" -> "右下角 '+' 按钮"  
- 输入以下地址并点击安装：
```
https://github.com/drdon1234/astrbot_plugin_showme_xjj
```

---

## 使用说明

### 指令帮助

- **随机短视频**  
```xjj视频```

- **随机美图**  
```xjj图片```

---

## 配置文件修改（重要！）

使用前请先修改配置文件 `config.yaml`：

### 平台设置
```
platform:
  type: "napcat" # 消息平台，兼容 napcat, llonebot, lagrange
  http_host: "127.0.0.1" # HTTP 服务器 IP，非 docker 部署一般为 127.0.0.1，docker 部署一般为宿主机局域网 IP
  http_port: 2333 # HTTP 服务器端口，通常为 2333 或 3000
  api_token: "" # HTTP 服务器 token，没有则不填
```

### 接口设置
```

```

### 缓存设置
```
download:
  cache_folder: "/app/sharedFolder" # 媒体文件需要下载时使用的保存路径
```

---

## 依赖库安装（重要！）

使用前请先安装以下依赖库：
- aiohttp
- PyYAML

在你的终端输入以下命令并回车：
```
pip install <module>
```
*使用具体模块名替换 &lt;module&gt;*
