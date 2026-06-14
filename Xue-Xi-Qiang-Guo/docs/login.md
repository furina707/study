# 学习强国登录逻辑分析

## 一、登录方式

学习强国 PC 端支持以下登录方式：

| 登录方式 | 说明 |
|---------|------|
| 学习强国 APP 扫码 | 使用学习强国 APP 扫描二维码登录 |
| 钉钉扫码 | 使用钉钉 APP 扫码登录 |

**注意：PC 端不支持手机验证码登录**

---

## 二、登录流程

### 1. 学习强国 APP 扫码登录

```
1. 访问登录页面
   GET https://pc.xuexi.cn/points/login.html

2. 页面加载登录配置
   - 获取二维码 URL
   - 显示二维码

3. 用户扫码
   - 使用学习强国 APP 扫描二维码
   - APP 确认登录

4. 轮询检查登录状态
   - 前端定时请求检查接口
   - 检测到登录成功后获取 Cookie/Token

5. 跳转到目标页面
```

### 2. 钉钉扫码登录

```
1. 构建钉钉登录 URL
   https://login.dingtalk.com/connect/qrconnect?
     appid=dingoankubyrfkttorhpou
     &response_type=code
     &scope=snsapi_login
     &state=xuexi
     &redirect_uri=https://www.xuexi.cn

2. 获取登录签名
   GET https://pc-api.xuexi.cn/open/api/sns/sign?appid=dingoankubyrfkttorhpou

3. 用户扫码授权

4. 回调处理
   GET https://pc-api.xuexi.cn/open/api/sns/callback?code=xxx&state=xxx

5. 获取用户信息
```

---

## 三、登录配置

```javascript
// 生产环境配置
const prodConfig = {
    pointApiHost: "https://pc-api.xuexi.cn",
    outerLinkHost: "https://pc-ref-link.xuexi.cn",
    dingdingAppId: "dingoankubyrfkttorhpou",
    dingHostOapi: "oapi.dingtalk.com",
    dingHostLogin: "login.dingtalk.com",
    qgHostLogin: "https://login.xuexi.cn",
    domain: ".xuexi.cn",
    pcDomain: "https://www.xuexi.cn"
};

// 测试环境配置
const testConfig = {
    pointApiHost: "https://pc-api-test.xxptcs.com",
    outerLinkHost: "https://pc-ref-link-pre.xxptcs.com",
    dingdingAppId: "dingoadmvzsevntk5celzy",
    dingHostOapi: "oapi.dingtalk.com",
    dingHostLogin: "login.dingtalk.com",
    qgHostLogin: "https://login-test.xxptcs.com",
    domain: ".xxptcs.com",
    pcDomain: "https://pretest.xxptcs.com"
};
```

---

## 四、登录相关文案

从 JS 代码中提取：

- `"用学习强国扫码登录，如未安装扫码下载"`
- `"扫码登录，如未安装扫码下载"`
- `"用户登录"`
- `"登录信息已过期，请重新登录"`
- `"当前登录人数过多，请您稍后再来"`

---

## 五、认证流程图

```
┌─────────────────┐
│   访问登录页面   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   获取登录签名   │ ◄── GET /open/api/sns/sign
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   显示二维码     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   用户扫码授权   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   轮询登录状态   │ ◄── GET /open/api/auth/check
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   获取用户凭证   │
│   (Cookie/Token) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   登录成功       │
└─────────────────┘
```

---

## 六、关键接口详解

### 1. 获取签名

```bash
curl -s "https://pc-api.xuexi.cn/open/api/sns/sign?appid=dingoankubyrfkttorhpou"
```

**响应：**
```json
{
    "data": {
        "sign": "5970feb0699446f69717c27c164c3e14"
    },
    "message": "OK",
    "code": 200,
    "error": null,
    "ok": true
}
```

### 2. 检查登录状态

```bash
curl -s "https://pc-api.xuexi.cn/open/api/auth/check"
```

**未登录响应：**
```json
{
    "data": null,
    "message": "OK",
    "code": 200,
    "error": null,
    "ok": true
}
```

**已登录响应：**
```json
{
    "data": {
        "userId": "xxx",
        "userName": "xxx",
        "token": "xxx"
    },
    "message": "OK",
    "code": 200,
    "error": null,
    "ok": true
}
```

---

## 七、安全机制

### 1. 请求签名

- 使用 `_aop_timestamp` 和 `_aop_signature` 进行请求签名
- 防止请求被篡改

### 2. 设备绑定

- 使用 `y-open-did` 标识设备
- 防止账号被盗用

### 3. CSP 策略

- 严格的 Content Security Policy
- 防止 XSS 攻击

### 4. Cookie 安全

- HttpOnly 标记
- Secure 标记（HTTPS）
- SameSite 属性
