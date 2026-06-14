#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园课程观看器 - 纯标准库 GUI 版本
仅使用 Python 内置模块：tkinter + urllib，不依赖 requests 及其他第三方包。
"""

import base64
import datetime
import hashlib
import hmac
import http.cookiejar
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from tkinter import *
from tkinter import messagebox, scrolledtext, ttk

USERNAME = "17716841865"
PASSWORD = "ff@00000"
OPEN_ID = "2256906d61ab4304851b706b0364c4e8"
COURSE_ID = "course-v2:75bd6c9770028fd+ljddzg_rw+20230403"

JWT_SECRET = "a824b379f126b8b7aa5e33dee83fb0a05aa7462c"
JWT_ISS = "c4f772063dcfa98e9c50"
JWT_AUD = "edx.unipus.cn"

SSO_URL = "https://sso.unipus.cn"
UCONTENT_URL = "https://ucontent.unipus.cn"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "gui_config.json")
PROGRESS_DIR = os.path.join(SCRIPT_DIR, "progress")


class StandardResponse:
    def __init__(self, status_code, body, url, headers):
        self.status_code = status_code
        self.text = body
        self.url = url
        self.headers = headers

    def json(self):
        return json.loads(self.text)


class StandardSession:
    def __init__(self, jwt_token=None):
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookiejar),
            urllib.request.HTTPHandler(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        if jwt_token:
            self.headers["X-Annotator-Auth-Token"] = jwt_token

    def request(self, method, url, data=None, headers=None, json_data=None):
        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)

        body = None
        if json_data is not None:
            body = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif data is not None:
            body = data

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with self.opener.open(req, timeout=30) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                return StandardResponse(resp.getcode(), text, resp.geturl(), dict(resp.headers))
        except urllib.error.HTTPError as err:
            text = err.read().decode("utf-8", errors="ignore")
            return StandardResponse(err.code, text, err.geturl(), dict(err.headers))
        except urllib.error.URLError as err:
            raise RuntimeError(f"网络错误: {err}") from err

    def get(self, url, headers=None):
        return self.request("GET", url, headers=headers)

    def post(self, url, json=None, headers=None):
        return self.request("POST", url, json_data=json, headers=headers)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def generate_jwt(open_id: str) -> str:
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
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{base64url_encode(signature)}"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(username, password, open_id, course_id):
    data = {
        "username": username,
        "password": password,
        "open_id": open_id,
        "course_id": course_id,
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_progress(course_id):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    progress_file = os.path.join(PROGRESS_DIR, f"progress_{course_id.replace(':', '_')}.json")
    if not os.path.exists(progress_file):
        return set()
    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("completed_groups", []))
    except Exception:
        return set()


def save_progress(course_id, completed_groups):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    progress_file = os.path.join(PROGRESS_DIR, f"progress_{course_id.replace(':', '_')}.json")
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump({"completed_groups": sorted(completed_groups), "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def sso_login(session, username, password):
    url = f"{SSO_URL}/sso/0.1/sso/login"
    payload = {
        "service": "https://u.unipus.cn/user/comm/login?school_id=",
        "username": username,
        "password": password,
        "captcha": "",
        "rememberMe": "on",
        "captchaCode": "",
        "encodeCaptha": ""
    }
    response = session.post(url, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"登录失败，HTTP {response.status_code}")
    result = response.json()
    if result.get("code") == "0":
        rs = result.get("rs", {})
        open_id = rs.get("openId", "")
        if not open_id:
            raise RuntimeError("登录成功但未返回 openId")
        jwt_token = generate_jwt(open_id)
        session.headers["X-Annotator-Auth-Token"] = jwt_token
        return open_id, jwt_token
    if result.get("code") == "1502":
        raise RuntimeError("需要验证码登录，GUI 版本暂不支持自动验证码登录")
    raise RuntimeError(f"登录失败: {result.get('msg', '未知错误')} ({result.get('code')})")


def fetch_course_structure(session, course_id):
    course_id_safe = urllib.parse.quote(course_id, safe=":/+")
    url = f"{UCONTENT_URL}/course/api/v4/lms/course/details?courseId={course_id_safe}"
    response = session.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"获取课程结构失败，HTTP {response.status_code}")
    result = response.json()
    if result.get("code") != 0:
        raise RuntimeError(f"获取课程结构失败: {result.get('msg', '未知错误')}")

    course = result.get("data", {}).get("course", {})
    units = course.get("units", [])
    groups = []
    for unit in units:
        unit_name = unit.get("name", "")
        for group in unit.get("groups", []):
            groups.append({
                "group_id": group.get("id", ""),
                "name": group.get("name", ""),
                "unit_name": unit_name,
                "tab_type": group.get("tab_type", "text"),
            })
    return groups


def complete_group(session, course_id, open_id, group):
    group_id = group["group_id"]
    tab_type = group["tab_type"]

    if tab_type in ["text", "video"]:
        url = f"{UCONTENT_URL}/api/mobile/user_group/{urllib.parse.quote(course_id, safe=':/+')}/{urllib.parse.quote(group_id, safe='')}"
        payload = {"groupId": group_id, "status": 2, "version": "default"}
        response = session.post(url, json=payload)
        result = response.json() if response.status_code == 200 else {"msg": response.text}
        return response.status_code == 200 and result.get("code") == 0, result

    if tab_type == "task":
        for trial in range(1, 6):
            url = f"{UCONTENT_URL}/course/api/v3/newExploration/submit"
            payload = {
                "quesDatas": [
                    {"instanceId": f"ques_{i}", "answer": "{}", "context": "{}", "contextVersion": 0, "answerVersion": 0}
                    for i in range(5)
                ],
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
            response = session.post(url, json=payload)
            result = response.json() if response.status_code == 200 else {"msg": response.text}
            if response.status_code == 200 and result.get("code") == 0:
                return True, result
            time.sleep(1)
        return False, result

    return False, {"msg": f"未知类型: {tab_type}"}


class CourseWatcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 U校园课程观看器（标准库版）")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.session = None
        self.open_id = ""
        self.jwt_token = ""
        self.groups = []
        self.current_index = 0
        self.is_running = False
        self.is_paused = False
        self.completed_ids = set()

        self._create_widgets()
        self._load_saved_config()
        self._set_controls(enabled=False)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        config_frame = ttk.LabelFrame(main_frame, text="📋 配置", padding=10)
        config_frame.pack(fill=X, pady=(0, 10))

        row1 = ttk.Frame(config_frame)
        row1.pack(fill=X, pady=5)
        ttk.Label(row1, text="用户名:").pack(side=LEFT)
        self.entry_username = ttk.Entry(row1, width=20)
        self.entry_username.pack(side=LEFT, padx=5)
        ttk.Label(row1, text="密码:").pack(side=LEFT, padx=(20, 0))
        self.entry_password = ttk.Entry(row1, width=20, show="*")
        self.entry_password.pack(side=LEFT, padx=5)
        ttk.Label(row1, text="OpenID:").pack(side=LEFT, padx=(20, 0))
        self.entry_openid = ttk.Entry(row1, width=30)
        self.entry_openid.pack(side=LEFT, padx=5)

        row2 = ttk.Frame(config_frame)
        row2.pack(fill=X, pady=5)
        ttk.Label(row2, text="课程ID:").pack(side=LEFT)
        self.entry_courseid = ttk.Entry(row2, width=64)
        self.entry_courseid.pack(side=LEFT, padx=5, fill=X, expand=True)

        row3 = ttk.Frame(config_frame)
        row3.pack(fill=X, pady=5)
        self.btn_login = ttk.Button(row3, text="🔑 登录", command=self._do_login)
        self.btn_login.pack(side=LEFT, padx=5)
        self.btn_load_course = ttk.Button(row3, text="📚 获取课程", command=self._load_course)
        self.btn_load_course.pack(side=LEFT, padx=5)
        ttk.Button(row3, text="💾 保存配置", command=self._save_config).pack(side=RIGHT, padx=5)

        self.label_status = ttk.Label(row3, text="未登录", foreground="gray")
        self.label_status.pack(side=LEFT, padx=20)

        progress_frame = ttk.LabelFrame(main_frame, text="📊 进度", padding=10)
        progress_frame.pack(fill=X, pady=(0, 10))

        self.progress_var = DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=X, pady=5)

        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=X)
        self.label_total = ttk.Label(stats_frame, text="总计: 0")
        self.label_total.pack(side=LEFT, padx=10)
        self.label_completed = ttk.Label(stats_frame, text="已完成: 0")
        self.label_completed.pack(side=LEFT, padx=10)
        self.label_failed = ttk.Label(stats_frame, text="失败: 0")
        self.label_failed.pack(side=LEFT, padx=10)
        self.label_current = ttk.Label(stats_frame, text="当前: -")
        self.label_current.pack(side=LEFT, padx=10)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, pady=10)
        self.btn_start = ttk.Button(control_frame, text="▶️ 开始", command=self._start_watching)
        self.btn_start.pack(side=LEFT, padx=5)
        self.btn_pause = ttk.Button(control_frame, text="⏸️ 暂停", command=self._pause_watching)
        self.btn_pause.pack(side=LEFT, padx=5)
        self.btn_stop = ttk.Button(control_frame, text="⏹️ 停止", command=self._stop_watching)
        self.btn_stop.pack(side=LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="📝 日志", padding=10)
        log_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True)

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{timestamp}] {message}\n")
        self.log_text.see(END)
        self.root.update_idletasks()

    def _load_saved_config(self):
        config = load_config()
        self.entry_username.insert(0, config.get("username", ""))
        self.entry_password.insert(0, config.get("password", ""))
        self.entry_openid.insert(0, config.get("open_id", ""))
        self.entry_courseid.insert(0, config.get("course_id", COURSE_ID))
        self._log("✅ 已加载本地配置")

    def _save_config(self):
        success = save_config(
            self.entry_username.get().strip(),
            self.entry_password.get().strip(),
            self.entry_openid.get().strip(),
            self.entry_courseid.get().strip() or COURSE_ID,
        )
        if success:
            self._log("✅ 配置已保存")
        else:
            self._log("❌ 配置保存失败")

    def _set_controls(self, enabled=False, running=False):
        self.btn_load_course.config(state=NORMAL if enabled else DISABLED)
        self.btn_start.config(state=NORMAL if enabled and not running else DISABLED)
        self.btn_pause.config(state=NORMAL if running else DISABLED)
        self.btn_stop.config(state=NORMAL if running else DISABLED)

    def _do_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        open_id = self.entry_openid.get().strip()

        if not username and not password and not open_id:
            messagebox.showwarning("警告", "请输入用户名/密码，或填写 OpenID")
            return

        self._log("🔑 正在登录...")
        self.btn_login.config(state=DISABLED)

        def run_login():
            try:
                self.session = StandardSession()
                if open_id and not username and not password:
                    self.open_id = open_id
                    self.jwt_token = generate_jwt(self.open_id)
                    self.session.headers["X-Annotator-Auth-Token"] = self.jwt_token
                    self.root.after(0, self._on_login_success)
                    return

                if not username or not password:
                    raise RuntimeError("用户名和密码不能为空")

                self.open_id, self.jwt_token = sso_login(self.session, username, password)
                self.root.after(0, self._on_login_success)
            except Exception as err:
                self.root.after(0, lambda: self._log(f"❌ 登录失败: {err}"))
                self.root.after(0, lambda: self.btn_login.config(state=NORMAL))

        threading.Thread(target=run_login, daemon=True).start()

    def _on_login_success(self):
        self._log(f"✅ 登录成功，OpenID: {self.open_id[:16]}...")
        self.label_status.config(text="已登录", foreground="green")
        self.btn_login.config(state=DISABLED)
        self._set_controls(enabled=True)

    def _load_course(self):
        course_id = self.entry_courseid.get().strip() or COURSE_ID
        if not self.session:
            messagebox.showwarning("警告", "请先登录")
            return

        self._log("📚 正在获取课程结构...")
        self.btn_load_course.config(state=DISABLED)

        def run_load():
            try:
                self.groups = fetch_course_structure(self.session, course_id)
                self.completed_ids = load_progress(course_id)
                self.current_course_id = course_id
                self.current_index = 0
                self.root.after(0, self._on_course_loaded)
            except Exception as err:
                self.root.after(0, lambda: self._log(f"❌ 获取课程失败: {err}"))
                self.root.after(0, lambda: self.btn_load_course.config(state=NORMAL))

        threading.Thread(target=run_load, daemon=True).start()

    def _on_course_loaded(self):
        total = len(self.groups)
        self._log(f"✅ 课程结构加载完成，共 {total} 个学习点")
        self.label_total.config(text=f"总计: {total}")
        self.label_completed.config(text=f"已完成: {len(self.completed_ids)}")
        self.label_failed.config(text="失败: 0")
        self.label_current.config(text="当前: -")
        self.progress_var.set(0)
        self._set_controls(enabled=True, running=False)

    def _start_watching(self):
        if self.is_running:
            return
        if not self.groups:
            messagebox.showwarning("警告", "请先获取课程结构")
            return

        self.is_running = True
        self.is_paused = False
        self.current_index = 0
        self.stats_done = 0
        self.stats_failed = 0
        self._set_controls(enabled=True, running=True)
        self._log("▶️ 开始自动完成课程")

        threading.Thread(target=self._watch_loop, daemon=True).start()

    def _pause_watching(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        label = "继续" if self.is_paused else "暂停"
        self.btn_pause.config(text=f"{label}")
        self._log("⏸️ 已暂停" if self.is_paused else "▶️ 继续运行")

    def _stop_watching(self):
        if not self.is_running:
            return
        self.is_running = False
        self._log("⏹️ 已停止")
        self._set_controls(enabled=True, running=False)
        self.btn_pause.config(text="⏸️ 暂停")

    def _watch_loop(self):
        total = len(self.groups)
        for index, group in enumerate(self.groups, start=1):
            if not self.is_running:
                break
            while self.is_paused and self.is_running:
                time.sleep(0.2)

            group_id = group["group_id"]
            title = f"[{index}/{total}] {group['unit_name']} > {group['name']} ({group['tab_type']})"
            if group_id in self.completed_ids:
                self._log(f"{title} - 已跳过")
                self.current_index = index
                self._update_ui(index, total)
                continue

            self._log(f"{title} - 开始")
            try:
                success, result = complete_group(self.session, self.current_course_id, self.open_id, group)
                if success:
                    self.completed_ids.add(group_id)
                    self.stats_done += 1
                    self._log(f"   ✅ 完成")
                else:
                    self.stats_failed += 1
                    self._log(f"   ❌ 失败: {result.get('msg', result)}")
            except Exception as err:
                self.stats_failed += 1
                self._log(f"   ❌ 异常: {err}")

            save_progress(self.current_course_id, self.completed_ids)
            self.current_index = index
            self._update_ui(index, total)
            time.sleep(2)

        self.is_running = False
        self.root.after(0, lambda: self._set_controls(enabled=True, running=False))
        self.root.after(0, lambda: self.btn_pause.config(text="⏸️ 暂停"))
        self._log("✅ 自动完成已结束")

    def _update_ui(self, index, total):
        percent = int(index / total * 100) if total else 0
        self.root.after(0, lambda: self.progress_var.set(percent))
        self.root.after(0, lambda: self.label_completed.config(text=f"已完成: {self.stats_done}"))
        self.root.after(0, lambda: self.label_failed.config(text=f"失败: {self.stats_failed}"))
        current = self.groups[index - 1] if 0 < index <= len(self.groups) else None
        current_text = current["name"] if current else "-"
        self.root.after(0, lambda: self.label_current.config(text=f"当前: {current_text}"))


def main():
    root = Tk()
    app = CourseWatcherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
