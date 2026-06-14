# 超星学习通 API 分析

## 一、登录认证 API

### 1. 账号密码登录
- **URL**: `https://passport2.chaoxing.com/fanyalogin`
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded; charset=UTF-8`
- **参数**:
  - `uname`: AES加密后的用户名
  - `password`: AES加密后的密码
  - `refer`: `https%3A%2F%2Fi.chaoxing.com%2F` (URI编码后的跳转地址)
  - `t`: `true`
- **AES加密密钥**: `u2oh6Vu^HWe4_AES`
- **说明**: 用户名和密码需要使用AES加密后传输

### 2. 二维码登录
- **生成二维码**: `https://passport2.chaoxing.com/createqr`
- **获取扫描状态**: `https://passport2.chaoxing.com/getauthstatus`
- **状态说明**:
  - 未登录
  - 已扫描
  - 取消扫描
  - 验证通过（此时返回Cookie）
  - 已过期

### 3. 登录页面
- **URL**: `https://passport2.chaoxing.com/login`

---

## 二、课程相关 API

### 1. 获取课程列表（移动端）
- **URL**: `http://mooc-api.chaoxing.com/mycourse/backclazzdata`
- **Method**: GET
- **需要**: Cookie认证

### 2. 获取课程列表（Web端）
- **URL**: `https://i.chaoxing.com/base?t={timestamp}`
- **Method**: GET
- **需要**: Cookie认证
- **说明**: 返回个人空间数据，课程数据在另一个ajax请求返回

### 3. 课程章节列表
- **URL**: `/api/course/chapter?courseId={courseId}`
- **Method**: GET
- **需要**: X-Token请求头（来自登录成功后的响应头）

### 4. 课程页面Tab切换
- **URL**: `http://data.xxt.aichaoxing.com/analysis/course/tab`
- **Method**: GET
- **参数**:
  - `u`: 用户ID (如: 224217004)
  - `sign`: tab标识 (task/chapters/more)
  - `description`: tab描述 (任务/章节/更多，需URL编码)
  - `enc`: MD5加密签名 (32位)
  - `personid`: 个人ID
  - `classid`: 班级ID
  - `courseid`: 课程ID

### 5. 学习相关 API
- **心跳**: `/api/learning/heartbeat`
- **完成视频**: `/api/learning/finishVideo`
- **视频播放信息**: `/api/learning/video/playInfo`
- **需要**: X-Token请求头

---

## 三、签到/活动 API

### 1. 获取活动列表
- **URL**: `https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist`
- **Method**: GET
- **参数**:
  - `courseId`: 课程ID
  - `classId`: 班级ID
  - `uid`: 用户ID
- **需要**: Cookie认证
- **返回**: activeList数组，包含活动信息

### 2. 签到
- **URL**: `https://mobilelearn.chaoxing.com/pptSign/stuSignajax`
- **Method**: GET
- **参数**:
  - `activeId`: 活动ID（从活动列表的url字段中提取）
  - `uid`: 用户ID
  - `clientip`: 客户端IP（可为空）
  - `latitude`: 纬度（可为-1）
  - `longitude`: 经度（可为-1）
  - `appType`: 应用类型（15）
  - `fid`: fid（0）
- **需要**: Cookie认证
- **返回**: `success` 表示签到成功

### 3. 活动判断逻辑
- `activeType == 2`: 签到活动
- `status == 1`: 未签到状态

---

## 四、加密机制

### 1. 用户名密码加密
- **算法**: AES-256
- **密钥**: `u2oh6Vu^HWe4_AES`
- **说明**: 在JS中实现加密，需要提取加密函数

### 2. enc参数加密
- **算法**: MD5
- **长度**: 32位
- **说明**: 用于接口参数签名验证

### 3. _sign字段
- **来源**: 动态加载的远程JS文件计算
- **说明**: 通过eval动态执行，包含时间戳、视频ID、播放进度、设备指纹等

---

## 五、Cookie说明

### Cookie获取流程
1. 第一次请求 `/fanyalogin` 返回部分Cookie
2. 第二次请求 `/base` 返回更多Cookie
3. 最终Cookie全部来自服务器返回，无本地生成

### Cookie有效期
- 有效期极短
- 每次请求校验 Referer 和 User-Agent 组合
- 勾选"下次自动登录"后保持7天

---

## 六、反自动化检测

### 检测点
1. `navigator.webdriver` 属性
2. `window.outerHeight` 等浏览器特征
3. `navigator.permissions.query` 中的 notifications 状态
4. TLS指纹（加密算法调用顺序）
5. 设备指纹哈希

### 绕过建议
- 使用 `curl_cffi` 库修改TLS指纹
- 覆盖 webdriver 属性
- 使用 Selenium + Chrome 112 版本
- 禁用自动化特征: `--disable-blink-features=AutomationControlled`

---

## 七、请求注意事项

1. **必须携带有效Cookie**
2. **需要正确的User-Agent和Referer**
3. **部分接口需要X-Token请求头**
4. **TLS指纹问题**: 使用 `curl_cffi` 或指定HTTP/1.1协议
5. **Cookie有效期短**: 需要频繁刷新或重新登录

---

## 八、Python请求示例

```python
from curl_cffi import requests
import urllib3

# 修改TLS指纹
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])

session = requests.Session()
headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 ...'
}

# 登录
data = {
    'uname': '加密后的用户名',
    'password': '加密后的密码',
    'refer': 'https%3A%2F%2Fi.chaoxing.com%2F',
    't': 'true',
}
session.post('https://passport2.chaoxing.com/fanyalogin', 
             headers=headers, data=data)

# 获取课程列表
response = session.get('http://mooc-api.chaoxing.com/mycourse/backclazzdata',
                       headers=headers)
```

---

*分析日期: 2026-06-14*
