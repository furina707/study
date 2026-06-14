#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园课程自动观看程序（标准库版）
无第三方依赖：仅使用 Python 内置库，支持登录、获取课程结构、自动完成 text/video/task。
"""

import argparse
import base64
import datetime
import hashlib
import hmac
import http.cookiejar
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USERNAME = "17716841865"
PASSWORD = "ff@00000"
OPEN_ID = "2256906d61ab4304851b706b0364c4e8"
COURSE_ID = "course-v2:75bd6c9770028fd+ljddzg_rw+20230403"

JWT_SECRET = "a824b379f126b8b7aa5e33dee83fb0a05aa7462c"
JWT_ISS = "c4f772063dcfa98e9c50"
JWT_AUD = "edx.unipus.cn"

SSO_URL = "https://sso.unipus.cn"
UAI_URL = "https://uai.unipus.cn"
UCONTENT_URL = "https://ucontent.unipus.cn"

DEFAULT_PROGRESS_DIR = "/data/user/work"


class StandardSession:
    def __init__(self, jwt_token=None):
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookiejar),
            urllib.request.HTTPHandler(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context())
        )
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        if jwt_token:
            self.headers["X-Annotator-Auth-Token"] = jwt_token

    def request(self, method, url, data=None, headers=None):
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with self.opener.open(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return resp.getcode(), body, dict(resp.headers)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="ignore")
            return err.code, body, dict(err.headers)
        except urllib.error.URLError as err:
            raise RuntimeError(f"网络错误: {err}") from err

    def get_json(self, url):
        status, body, _ = self.request("GET", url)
        return status, self._parse_json(body)

    def post_json(self, url, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        status, body, _ = self.request("POST", url, data=data)
        return status, self._parse_json(body)

    def _parse_json(self, text):
        try:
            return json.loads(text)
        except Exception:
            return {"error": "无法解析 JSON", "raw": text}


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


def load_progress(course_id: str, progress_dir: str) -> set:
    progress_file = os.path.join(progress_dir, f"progress_{course_id.replace(':', '_')}.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("completed_groups", []))
        except Exception:
            pass
    return set()


def save_progress(course_id: str, completed_ids: set, progress_dir: str):
    os.makedirs(progress_dir, exist_ok=True)
    progress_file = os.path.join(progress_dir, f"progress_{course_id.replace(':', '_')}.json")
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({"completed_groups": sorted(completed_ids), "timestamp": datetime.datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)


def print_json(title: str, data):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(data)


def sso_login(session: StandardSession, username: str, password: str):
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
    status, result = session.post_json(url, payload)
    if not isinstance(result, dict):
        raise RuntimeError(f"登录返回格式异常: {result}")
    if result.get("code") == "0":
        rs = result.get("rs", {})
        open_id = rs.get("openId", "")
        if not open_id:
            raise RuntimeError("登录成功但未返回 openId")
        jwt_token = generate_jwt(open_id)
        session.headers["X-Annotator-Auth-Token"] = jwt_token
        return open_id, jwt_token
    if result.get("code") == "1502":
        raise RuntimeError("当前账号需要验证码登录，标准库脚本暂不支持自动验证码。请手动登录或使用 open_id 直接运行。")
    raise RuntimeError(f"登录失败: {result.get('msg', '未知错误')} ({result.get('code')})")


def fetch_course_structure(session: StandardSession, course_id: str):
    url = f"{UCONTENT_URL}/course/api/v4/lms/course/details?courseId={urllib.parse.quote(course_id, safe=':/+')}"
    status, result = session.get_json(url)
    if status != 200 or result.get("code") != 0:
        raise RuntimeError(f"获取课程结构失败: {result.get('msg', status)}")

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
                "tab_type": group.get("tab_type", "text")
            })
    return groups


def complete_group(session: StandardSession, course_id: str, open_id: str, group: dict):
    group_id = group["group_id"]
    tab_type = group["tab_type"]

    if tab_type in ["text", "video"]:
        url = f"{UCONTENT_URL}/api/mobile/user_group/{urllib.parse.quote(course_id, safe=':/+')}/{urllib.parse.quote(group_id, safe='')}"
        payload = {"groupId": group_id, "status": 2, "version": "default"}
        status, result = session.post_json(url, payload)
        success = status == 200 and result.get("code") == 0
        return success, result

    if tab_type == "task":
        for count in [6, 5, 4, 3, 2, 1, 7, 8]:
            url = f"{UCONTENT_URL}/course/api/v3/newExploration/submit"
            payload = {
                "quesDatas": [
                    {
                        "instanceId": f"ques_{i}",
                        "answer": "{}",
                        "context": "{}",
                        "contextVersion": 0,
                        "answerVersion": 0
                    }
                    for i in range(count)
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
            status, result = session.post_json(url, payload)
            if status == 200 and isinstance(result, dict):
                if result.get("code") == 0:
                    return True, result
                if result.get("code") in [300100, 600002]:
                    time.sleep(1)
                    continue
            else:
                break
        return False, result

    return False, {"msg": f"未知类型 {tab_type}"}


def parse_args():
    parser = argparse.ArgumentParser(description="U校园课程自动观看程序（标准库版）")
    parser.add_argument("--username", help="SSO 用户名，未提供则使用配置中的默认值")
    parser.add_argument("--password", help="SSO 密码，未提供则使用配置中的默认值")
    parser.add_argument("--open-id", help="OpenID，缺失时会通过用户名/密码登录获取")
    parser.add_argument("--course-id", help="课程ID，缺失时使用配置中的默认值")
    parser.add_argument("--progress-dir", default=DEFAULT_PROGRESS_DIR, help="进度保存目录")
    parser.add_argument("--no-login", action="store_true", help="直接使用 open_id 而不登录（需提供 --open-id 或配置中的默认 OPEN_ID)")
    return parser.parse_args()


def main():
    args = parse_args()

    username = args.username or USERNAME
    password = args.password or PASSWORD
    open_id = args.open_id or OPEN_ID
    course_id = args.course_id or COURSE_ID
    progress_dir = args.progress_dir

    session = StandardSession()

    if args.no_login:
        if not open_id:
            print("错误: 未提供 open_id，无法跳过登录。")
            sys.exit(1)
        jwt_token = generate_jwt(open_id)
        session.headers["X-Annotator-Auth-Token"] = jwt_token
        print(f"使用 open_id 直接运行: {open_id[:10]}...")
    else:
        if open_id and not username and not password:
            jwt_token = generate_jwt(open_id)
            session.headers["X-Annotator-Auth-Token"] = jwt_token
            print(f"使用配置 OpenID 运行: {open_id[:10]}...")
        else:
            print("开始登录...")
            try:
                open_id, jwt_token = sso_login(session, username, password)
                print(f"登录成功, open_id={open_id}")
            except Exception as err:
                print(f"登录失败: {err}")
                sys.exit(1)

    try:
        groups = fetch_course_structure(session, course_id)
    except Exception as err:
        print(f"获取课程结构失败: {err}")
        sys.exit(1)

    if not groups:
        print("没有获取到课程节点，可能课程ID 或接口已变更。")
        sys.exit(1)

    print(f"共获取到 {len(groups)} 个知识点。")

    completed_ids = load_progress(course_id, progress_dir)
    print(f"已加载进度: {len(completed_ids)} 个已完成")

    stats = {"done": 0, "failed": 0, "skipped": 0}

    for index, group in enumerate(groups, start=1):
        group_id = group["group_id"]
        title = f"[{index}/{len(groups)}] {group['unit_name']} > {group['name']} ({group['tab_type']})"
        if group_id in completed_ids:
            print(f"{title} - 已跳过")
            stats["skipped"] += 1
            continue

        print(f"{title} - 开始...")
        try:
            success, result = complete_group(session, course_id, open_id, group)
            if success:
                completed_ids.add(group_id)
                stats["done"] += 1
                print(f"   ✅ 完成")
            else:
                stats["failed"] += 1
                print(f"   ❌ 失败: {result.get('msg', result)}")
        except Exception as err:
            stats["failed"] += 1
            print(f"   ❌ 异常: {err}")

        save_progress(course_id, completed_ids, progress_dir)
        time.sleep(2)

    print("\n=== 运行结果 ===")
    print(f"总数: {len(groups)}")
    print(f"已完成: {stats['done']}")
    print(f"失败: {stats['failed']}")
    print(f"已跳过: {stats['skipped']}")
    print(f"进度文件: {os.path.join(progress_dir, f'progress_{course_id.replace(':', '_')}.json')}")


if __name__ == "__main__":
    main()
