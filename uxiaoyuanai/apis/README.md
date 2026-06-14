# U校园 API 调试工具集

每个 API 独立一个文件，支持 `.http` (VS Code REST Client) 和 `.py` (Python) 两种格式。

## 目录结构

```
apis/
├── config.py              # 公共配置 (账号、JWT、URL)
├── sso/                   # SSO 平台
│   ├── login.http/py      # SSO 登录
│   ├── captcha.http/py    # 获取验证码
│   └── ticket_auth.http/py # Ticket认证
├── uai/                   # UAI 平台
│   ├── course_list.http/py    # 获取课程列表
│   └── submit_progress.http/py # 提交进度
└── ucontent/              # UContent 平台
    ├── course_details.http/py  # 课程详情
    ├── get_content.http/py     # 获取内容
    ├── get_answer.http/py      # 获取答案
    ├── save_progress.http/py   # 保存进度 (text/video)
    ├── submit_task.http/py     # 提交答案 (task)
    ├── course_progress.http/py # 查询课程进度
    ├── unit_progress.http/py   # 查询单元进度
    ├── group_state.http/py     # 查询 Group 状态
    └── user_answer.http/py     # 查询用户答案
```

## 使用方法

### 1. 配置账号

编辑 `apis/config.py`，填写你的账号信息：

```python
USERNAME = "你的手机号"
PASSWORD = "你的密码"
OPEN_ID = "你的open_id"
COURSE_ID = "你的课程ID"
```

### 2. VS Code REST Client (.http)

1. 安装 VS Code 插件: REST Client
2. 打开任意 `.http` 文件
3. 点击 "Send Request" 发送请求
4. 查看响应结果

### 3. Python 脚本 (.py)

```bash
# SSO 登录
python apis/sso/login.py

# SSO Ticket认证
python apis/sso/ticket_auth.py -t <service_ticket>

# 获取课程列表
python apis/uai/course_list.py

# 保存进度
python apis/ucontent/save_progress.py -g <group_id>

# 提交答案
python apis/ucontent/submit_task.py -g <group_id> -n 6

# 查询单元进度
python apis/ucontent/unit_progress.py -u <unit_id>

# 查询用户答案
python apis/ucontent/user_answer.py -g <group_id>
```

## API 列表

| 平台 | API | 文件 | 说明 |
|------|-----|------|------|
| SSO | 登录 | `sso/login` | 获取 openId 和 JWT |
| SSO | 验证码 | `sso/captcha` | 获取验证码图片 |
| SSO | Ticket认证 | `sso/ticket_auth` | 用 ticket 建立 session |
| UAI | 课程列表 | `uai/course_list` | 获取用户课程 |
| UAI | 提交进度 | `uai/submit_progress` | 提交学习进度 |
| UContent | 课程详情 | `ucontent/course_details` | 获取课程结构 |
| UContent | 获取内容 | `ucontent/get_content` | 获取加密内容 |
| UContent | 获取答案 | `ucontent/get_answer` | 获取答案解析 |
| UContent | 保存进度 | `ucontent/save_progress` | text/video 类型 |
| UContent | 提交答案 | `ucontent/submit_task` | task 类型 |
| UContent | 课程进度 | `ucontent/course_progress` | 查询整体进度 |
| UContent | 单元进度 | `ucontent/unit_progress` | 查询单元详情 |
| UContent | Group状态 | `ucontent/group_state` | 查询单个状态 |
| UContent | 用户答案 | `ucontent/user_answer` | 查询已提交答案 |
