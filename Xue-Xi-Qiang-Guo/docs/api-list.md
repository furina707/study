# 学习强国 API 接口列表

## 一、域名列表

| 域名 | 用途 |
|------|------|
| `www.xuexi.cn` | 主站 |
| `pc.xuexi.cn` | PC 端页面 |
| `pc-api.xuexi.cn` | PC 端 API |
| `login.xuexi.cn` | 登录服务 |
| `boot-img.xuexi.cn` | 图片 CDN |
| `bootcdn.xuexi.cn` | 静态资源 CDN |
| `iflow-api.xuexi.cn` | 日志 API |
| `themis-oss.xuexi.cn` | 灰度配置 |

---

## 二、认证接口

### 1. 检查登录状态

```
GET https://pc-api.xuexi.cn/open/api/auth/check
```

**响应示例：**
```json
{
    "data": null,
    "message": "OK",
    "code": 200,
    "error": null,
    "ok": true
}
```

### 2. 获取登录签名

```
GET https://pc-api.xuexi.cn/open/api/sns/sign?appid=dingoankubyrfkttorhpou
```

**响应示例：**
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

### 3. 社交登录回调

```
GET https://pc-api.xuexi.cn/open/api/sns/callback?code=xxx&state=xxx
```

### 4. 获取用户菜单

```
GET https://pc-api.xuexi.cn/open/api/usr/menu
```

**需要登录状态**

---

## 三、数据接口

### 1. 页面骨架数据

```
GET https://www.xuexi.cn/lgdata/skeleton.json
```

**参数：**
- `_st`: 站点 ID
- `js_v`: JS 版本号

**响应结构：**
```json
{
    "DataSet": [],
    "Layout": {
        "children": [...],
        "props": {...}
    },
    "pageData": {
        "skeleton-page-header": {...},
        "skeleton-page-footer": {...}
    }
}
```

### 2. 内容区块数据

```
GET https://www.xuexi.cn/lgdata/{hash}.json
```

**已知的数据接口：**
- `uten7p4h89nh.json` - 轮播图数据
- `16olij45eud8d.json` - 内容区块
- `15lk6fmld6jph.json` - 内容区块
- `1ooaa665snf.json` - 内容区块
- `1hoa55co0nf.json` - 内容区块

---

## 四、日志接口

### 1. 前端日志上报

```
GET https://px-itrace.xuexi.cn/api/v1/jssdk/upload
```

**参数：**
- `wpk-header`: 加密请求头
- `data`: JSON 日志数据

### 2. PC 端日志

```
POST https://iflow-api.xuexi.cn/logflow_seer/api/v1/pclog
POST https://iflow-api.xuexi.cn/logflow/api/v1/pclog
```

---

## 五、配置接口

### 1. 灰度发布配置

```
GET https://themis-oss.xuexi.cn/h5_gray/pc_web.json
```

---

## 六、请求头说明

### 必需的请求头

```
y-open-ua: TorchApp/1.0 OSType/{os} XueXi/{version} Device/XXQGSpecialTopic
y-open-did: {设备ID}
gateway-channel: inner_https
```

### 设备 ID 生成

```javascript
// 存储在 localStorage
localStorageKey: "xxqg_st_did"

// 格式: 16位随机字符串 (UUID 去掉横线后截取)
function generateDeviceId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
        .replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        })
        .replace(/-/g, '')
        .substring(0, 16);
}
```

---

## 七、签名机制

### 签名参数

- `_aop_timestamp`: 时间戳
- `_aop_signature`: 签名值
- `uuid`: 请求唯一标识

### 签名算法

```
签名 = MD5(appSecret + timestamp + uuid)
```

---

## 八、Cookie 说明

### 会话 Cookie

| Cookie 名称 | 说明 | 有效期 |
|------------|------|--------|
| `aliyungf_tc` | 阿里云会话跟踪 | 会话级 |
| `acw_tc` | 阿里云 WAF Cookie | 约 30 分钟 |

### 认证 Cookie

登录成功后，服务器会设置认证相关的 Cookie，用于后续请求的身份验证。
