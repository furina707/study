# 学习强国 API 分析

> 本项目用于分析学习强国 (xuexi.cn) 的 API 接口

## 项目结构

```
xuexi-api/
├── README.md           # 项目说明
├── docs/
│   ├── api-list.md     # API 接口列表
│   ├── login.md        # 登录逻辑分析
│   └── cookie-test.md  # Cookie 失效测试
└── scripts/
    ├── get_cookie.py   # 获取 Cookie 脚本
    └── test_cookie.py  # 测试 Cookie 失效时间
```

## 快速开始

### 1. 获取 Cookie

#### 方法一：浏览器开发者工具

1. 打开 https://www.xuexi.cn/
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 在请求头中找到 Cookie 字段

#### 方法二：扫码登录后获取

1. 访问登录页面：https://pc.xuexi.cn/points/login.html
2. 使用学习强国 APP 或钉钉扫码登录
3. 登录成功后，从浏览器开发者工具中获取 Cookie

### 2. 使用 Cookie 调用 API

```python
import requests

cookie = "your_cookie_here"
headers = {
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "y-open-ua": "TorchApp/1.0 OSType/Windows XueXi/1.0",
    "y-open-did": "your_device_id"
}

response = requests.get(
    "https://pc-api.xuexi.cn/open/api/auth/check",
    headers=headers
)
print(response.json())
```

## API 接口列表

### 认证相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/open/api/auth/check` | GET | 检查登录状态 |
| `/open/api/sns/sign` | GET | 获取登录签名 |
| `/open/api/sns/callback` | GET | 社交登录回调 |
| `/open/api/usr/menu` | GET | 获取用户菜单 |

### 数据接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/lgdata/skeleton.json` | GET | 页面骨架数据 |
| `/lgdata/{hash}.json` | GET | 内容区块数据 |

## 登录配置

```javascript
// 生产环境配置
const config = {
    pointApiHost: "https://pc-api.xuexi.cn",
    outerLinkHost: "https://pc-ref-link.xuexi.cn",
    dingdingAppId: "dingoankubyrfkttorhpou",
    dingHostOapi: "oapi.dingtalk.com",
    dingHostLogin: "login.dingtalk.com",
    qgHostLogin: "https://login.xuexi.cn",
    domain: ".xuexi.cn",
    pcDomain: "https://www.xuexi.cn"
};
```

## Cookie 失效测试

### 测试方法

1. 登录后记录 Cookie 和时间
2. 每隔一段时间使用 Cookie 调用 API
3. 记录 API 返回状态
4. 确定 Cookie 失效时间

### 预期结果

- `aliyungf_tc`: 会话跟踪 Cookie
- `acw_tc`: 有效期约 30 分钟

## 注意事项

1. 本项目仅供学习研究使用
2. 请勿用于任何商业或非法用途
3. API 接口可能随时变更
4. 请遵守网站的使用条款

## License

MIT
