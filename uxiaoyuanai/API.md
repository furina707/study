# U校园自动学习 - API文档

## 目录
- [认证体系](#认证体系)
- [UAI平台 API](#uai平台-api-uaiunipuscn)
- [UContent平台 API](#ucontent平台-api-ucontentunipuscn)
- [错误码](#错误码)
- [Group类型](#group类型)
- [AES加密](#aes加密)
- [Python代码示例](#python代码示例)

---

## 认证体系

### 1. SSO登录

**请求：**
```http
POST https://sso.unipus.cn/sso/0.1/sso/login
Content-Type: application/json
X-Requested-With: XMLHttpRequest

{
  "service": "https://u.unipus.cn/user/comm/login?school_id=",
  "username": "手机号",
  "password": "密码",
  "captcha": "",
  "rememberMe": "on",
  "captchaCode": "",
  "encodeCaptha": ""
}
```

**响应示例（成功）：**
```json
{
  "code": "0",
  "rs": {
    "serviceTicket": "ST-12345-xxx",
    "openId": "2256906d61ab4304851b706b0364c4e8",
    "userId": "1234567",
    "userName": "用户姓名"
  }
}
```

**响应示例（需要验证码）：**
```json
{
  "code": "1502",
  "msg": "请输入验证码"
}
```

**验证码获取：**
```http
POST https://sso.unipus.cn/sso/4.0/sso/image_captcha2
```

**响应：**
```json
{
  "code": "0",
  "rs": {
    "image": "/9j/4AAQSkZJRgABAQAAAQ...",
    "encodeCaptha": "abc123"
  }
}
```

### 2. Ticket认证

SSO登录后，使用serviceTicket建立session：

```http
GET https://u.unipus.cn/user/comm/login?school_id=&ticket={serviceTicket}
```

### 3. 前端JWT Token生成

UContent平台使用前端生成的JWT Token进行认证。

**算法参数：**
| 参数 | 值 |
|------|-----|
| 算法 | HS256 |
| 密钥 | `a824b379f126b8b7aa5e33dee83fb0a05aa7462c` |
| 签发者(iss) | `c4f772063dcfa98e9c50` |
| 受众(aud) | `edx.unipus.cn` |

**Payload结构：**
```json
{
  "open_id": "2256906d61ab4304851b706b0364c4e8",
  "name": "",
  "email": "",
  "administrator": false,
  "exp": 1765432100000,
  "iss": "c4f772063dcfa98e9c50",
  "aud": "edx.unipus.cn"
}
```

**认证头：**
```http
X-Annotator-Auth-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## UAI平台 API (uai.unipus.cn)

### 登录

```http
POST https://sso.unipus.cn/sso/0.1/sso/login
Content-Type: application/json

{
  "service": "https://uai.unipus.cn",
  "username": "手机号",
  "password": "密码",
  "captcha": "",
  "rememberMe": "on",
  "captchaCode": "",
  "encodeCaptha": ""
}
```

### 课程列表

```http
GET https://uai.unipus.cn/learn/api/v2/course/list
X-Annotator-Auth-Token: {jwt_token}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "courses": [
      {
        "courseId": "course-v1:xxx+xxx+xxx",
        "courseName": "大学英语",
        "progress": 75,
        "totalUnits": 12
      }
    ]
  }
}
```

### 课程进度提交

```http
POST https://uai.unipus.cn/learn/api/v2/record/progress
Content-Type: application/json
X-Annotator-Auth-Token: {jwt_token}

{
  "courseId": "course-v1:xxx+xxx+xxx",
  "unitId": "unit_001",
  "openId": "2256906d61ab4304851b706b0364c4e8",
  "duration": 30
}
```

---

## UContent平台 API (ucontent.unipus.cn)

### 认证方式

所有请求需要携带JWT Token：
```http
X-Annotator-Auth-Token: {jwt_token}
```

### 获取课程结构

```http
GET /course/api/v4/lms/course/details?courseId={courseId}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "course": {
      "id": "course-v2:75bd6c9770028fd+ljddzg_rw+20230403",
      "name": "全新版大学进阶英语综合教程2",
      "units": [
        {
          "id": "64f1e6350000caa",
          "name": "Unit 1",
          "groups": [
            {
              "id": "64f1f5410001019",
              "name": "Lead-in",
              "tab_type": "text"
            }
          ]
        }
      ]
    }
  }
}
```

### 课程内容

```http
GET /course/api/v3/content/{courseId}/{groupId}/default
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "content": "unipus.xxx...",
    "type": "encrypted"
  }
}
```

### 答案与解析

```http
GET /course/api/v3/answer/{courseId}/{groupId}/{mode}
```

参数说明：
- `mode`: `default` 或 `preview`

### 进度保存（仅标记浏览）

适用于 `tab_type: "text"` 和 `"video"` 类型的group。

```http
POST /api/mobile/user_group/{courseId}/{groupId}/progress
Content-Type: application/json

{
  "groupId": "64f1f5410001019",
  "status": 2,
  "version": "default"
}
```

**响应示例（成功）：**
```json
{
  "code": 0,
  "success": true,
  "msg": "success"
}
```

### 提交答案（标记完成）

适用于 `tab_type: "task"` 类型的group，必须调用此API才能标记为完成。

```http
POST /course/api/v3/newExploration/submit
Content-Type: application/json

{
  "quesDatas": [
    {
      "instanceId": "ques_001",
      "answer": "{\"key\":\"value\"}",
      "context": "{}",
      "contextVersion": 0,
      "answerVersion": 0
    }
  ],
  "groupId": "657ebd3c0000d13",
  "isCompleted": [true],
  "thirdPartyJudges": "[]",
  "submitType": 1,
  "hideLoading": true,
  "associationGroupId": "",
  "associationUnitId": "",
  "courseId": "course-v2:75bd6c9770028fd+ljddzg_rw+20230403",
  "openId": "2256906d61ab4304851b706b0364c4e8",
  "version": "default"
}
```

**重要说明：**
- `quesDatas` 数组长度必须与题目数量完全匹配，否则返回 `code:300100`
- 短时间内重复提交会返回 `code:600002`（操作过于频繁）
- `task_mini_score_pct=0` 表示即使答案错误也能通过

### 查询课程进度

```http
GET /course/api/v2/course_progress/{courseId}/{openId}/{mode}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "units": [
      {
        "unitId": "64f1e6350000caa",
        "progress": 100
      }
    ]
  }
}
```

### 查询单元进度

```http
GET /course/api/v2/course_progress/{courseId}/{unitId}/{openId}/{mode}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "leafs": {
      "64f1f5410001019": {
        "state": {
          "pass": 1,
          "score_pct": 100
        }
      }
    }
  }
}
```

### 查询Group状态

```http
GET /api/mobile/user_module/{courseId}/{groupId}/progress/v2
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "state": {
      "pass": 1,
      "score_pct": 100,
      "status": 2,
      "task_mini_score_pct": 0
    }
  }
}
```

### 查询用户答案

```http
GET /api/mobile/user_module/{courseId}/{groupId}-{version}
```

---

## 错误码

| Code | 含义 | 解决方案 |
|------|------|----------|
| 0 | 成功 | - |
| 1 | 失败 | 检查请求参数 |
| 1502 | 需要验证码 | 调用验证码接口获取 |
| 300100 | 题目数量不匹配 | 检查quesDatas数组长度 |
| 600001 | 答案数据不正确 | 检查answer格式 |
| 600002 | 操作过于频繁 | 等待几分钟后重试 |

---

## Group类型

| tab_type | 说明 | 完成方式 |
|----------|------|----------|
| text | 阅读/文本内容 | 调用 progress API |
| video | 视频内容 | 调用 progress API |
| task | 练习/题目 | 必须调用 submit API |

### 如何判断group类型

通过查询单元进度接口，检查 `tab_type` 字段：

```python
# 伪代码
if group["tab_type"] in ["text", "video"]:
    # 只需调用 progress API
    save_progress(group_id)
elif group["tab_type"] == "task":
    # 需要调用 submit API
    submit_answers(group_id, answers)
```

---

## AES加密

UContent平台使用AES-CBC加密课程内容。

**加密参数：**
| 参数 | 值 |
|------|-----|
| 算法 | AES-256-CBC |
| Key | `8AD70B641C024C7ADA2ECD082EC0334F` |
| IV | `0102030405060708090A0B0C0D0E0F10` |
| 填充 | PKCS7 |
| 输出格式 | `unipus.{base64编码的加密数据}` |

**Python解密示例：**
```python
from Crypto.Cipher import AES
import base64

def decrypt_content(encrypted_data: str) -> str:
    """解密UContent内容"""
    if not encrypted_data.startswith("unipus."):
        return encrypted_data
    
    key = bytes.fromhex("8AD70B641C024C7ADA2ECD082EC0334F")
    iv = bytes.fromhex("0102030405060708090A0B0C0D0E0F10")
    
    encrypted = base64.b64decode(encrypted_data[7:])  # 去掉 "unipus." 前缀
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    
    # 去除PKCS7填充
    pad_len = decrypted[-1]
    return decrypted[:-pad_len].decode('utf-8')
```

---

## Python代码示例

### 完整登录流程

```python
import json
import time
import hmac
import hashlib
import base64
import requests
from requests import Session

# 配置
USERNAME = "你的手机号"
PASSWORD = "你的密码"
OPEN_ID = "你的open_id"

JWT_SECRET = "a824b379f126b8b7aa5e33dee83fb0a05aa7462c"
JWT_ISS = "c4f772063dcfa98e9c50"
JWT_AUD = "edx.unipus.cn"

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def generate_jwt(open_id):
    """生成JWT Token"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "open_id": open_id,
        "name": "",
        "email": "",
        "administrator": False,
        "exp": int(time.time() * 1000) + 31536000000,
        "iss": JWT_ISS,
        "aud": JWT_AUD,
    }
    
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode())
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode())
    signing_input = f"{header_b64}.{payload_b64}"
    
    signature = hmac.new(
        JWT_SECRET.encode(),
        signing_input.encode(),
        hashlib.sha256
    ).digest()
    
    return f"{header_b64}.{payload_b64}.{base64url_encode(signature)}"

def sso_login(session, username, password):
    """SSO登录"""
    url = "https://sso.unipus.cn/sso/0.1/sso/login"
    data = {
        "service": "https://u.unipus.cn/user/comm/login?school_id=",
        "username": username,
        "password": password,
        "captcha": "",
        "rememberMe": "on",
        "captchaCode": "",
        "encodeCaptha": ""
    }
    
    resp = session.post(
        url,
        data=json.dumps(data, separators=(',', ':')),
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    result = resp.json()
    
    if result.get("code") == "0":
        return True, result.get("rs")
    return False, result

# 使用示例
session = Session()
success, login_data = sso_login(session, USERNAME, PASSWORD)
if success:
    jwt_token = generate_jwt(login_data["openId"])
    session.headers["X-Annotator-Auth-Token"] = jwt_token
    print(f"登录成功，JWT: {jwt_token[:50]}...")
```

### 提交进度（text/video类型）

```python
def save_group_progress(session, course_id, group_id):
    """保存group进度（适用于text/video类型）"""
    url = f"https://ucontent.unipus.cn/api/mobile/user_group/{course_id}/{group_id}/progress"
    
    payload = {
        "groupId": group_id,
        "status": 2,
        "version": "default"
    }
    
    resp = session.post(url, json=payload)
    result = resp.json()
    
    if result.get("code") == 0:
        print(f"✅ Group {group_id} 进度已保存")
        return True
    else:
        print(f"❌ Group {group_id} 失败: {result}")
        return False
```

### 提交答案（task类型）

```python
def submit_task_answers(session, course_id, group_id, open_id, question_count):
    """提交task类型group的答案"""
    url = "https://ucontent.unipus.cn/course/api/v3/newExploration/submit"
    
    # 构造空的答案数据（task_mini_score_pct=0时可全错通过）
    ques_datas = []
    for i in range(question_count):
        ques_datas.append({
            "instanceId": f"ques_{i}",
            "answer": "{}",
            "context": "{}",
            "contextVersion": 0,
            "answerVersion": 0
        })
    
    payload = {
        "quesDatas": ques_datas,
        "groupId": group_id,
        "isCompleted": [True],
        "thirdPartyJudges": "[]",
        "submitType": 1,
        "hideLoading": True,
        "associationGroupId": "",
        "associationUnitId": "",
        "courseId": course_id,
        "openId": open_id,
        "version": "default"
    }
    
    resp = session.post(url, json=payload)
    result = resp.json()
    
    if result.get("code") == 0:
        print(f"✅ Group {group_id} 提交成功")
        return True
    elif result.get("code") == 300100:
        print(f"❌ 题目数量不匹配")
        return False
    elif result.get("code") == 600002:
        print(f"⚠️ 操作过于频繁，请等待")
        return False
    else:
        print(f"❌ 提交失败: {result}")
        return False
```

### 查询所有group完成状态

```python
def check_unit_progress(session, course_id, unit_id, open_id):
    """查询单元内所有group的完成状态"""
    url = f"https://ucontent.unipus.cn/course/api/v2/course_progress/{course_id}/{unit_id}/{open_id}/default"
    
    resp = session.get(url)
    result = resp.json()
    
    if result.get("code") != 0:
        return None
    
    leafs = result.get("data", {}).get("leafs", {})
    
    completed = []
    incomplete = []
    
    for group_id, info in leafs.items():
        state = info.get("state", {})
        if state.get("pass") == 1:
            completed.append(group_id)
        else:
            incomplete.append(group_id)
    
    return {
        "completed": completed,
        "incomplete": incomplete,
        "total": len(leafs)
    }

# 使用示例
status = check_unit_progress(session, "course_id", "unit_id", "open_id")
print(f"已完成: {len(status['completed'])}/{status['total']}")
print(f"未完成: {len(status['incomplete'])}/{status['total']}")
```

### 批量处理课程

```python
def process_course(session, course_id, open_id, units):
    """
    批量处理课程的所有group
    units: [(unit_id, [(node_id, group_id, tab_type), ...]), ...]
    """
    for unit_id, groups in units:
        print(f"\n处理单元: {unit_id}")
        
        for node_id, group_id, tab_type in groups:
            if tab_type in ["text", "video"]:
                # text/video类型：直接标记进度
                save_group_progress(session, course_id, group_id)
                
            elif tab_type == "task":
                # task类型：需要提交答案
                # 先获取题目数量
                # 然后提交对应数量的空答案
                submit_task_answers(session, course_id, group_id, open_id, question_count=6)
            
            time.sleep(2)  # 避免请求过快
```

---

## 注意事项

1. **频率限制**：submit API有严格的频率限制，短时间内多次调用会返回 `code:600002`，建议每次调用间隔 3-5 秒

2. **题目数量**：task类型group提交时必须提供正确数量的答案，可通过分析课程内容或尝试不同数量来确定

3. **JWT有效期**：生成的JWT有效期约1年（31536000000毫秒），通常不需要频繁重新生成

4. **Session保持**：登录后保持session复用，避免重复登录触发验证码
