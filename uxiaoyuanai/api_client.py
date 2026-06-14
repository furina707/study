#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园 API 调试客户端
交互式命令行工具，用于测试和调试各种 API
"""

import json
import time
import hmac
import hashlib
import base64
import requests
from requests import Session
from typing import Optional, Dict, Any


class UClient:
    """U校园 API 客户端"""
    
    def __init__(self):
        self.session = Session()
        self.username = ""
        self.password = ""
        self.open_id = ""
        self.service_ticket = ""
        self.jwt_token = ""
        self.course_id = ""
        
        # JWT 配置
        self.JWT_SECRET = "a824b379f126b8b7aa5e33dee83fb0a05aa7462c"
        self.JWT_ISS = "c4f772063dcfa98e9c50"
        self.JWT_AUD = "edx.unipus.cn"
        
        # 基础 URL
        self.SSO_URL = "https://sso.unipus.cn"
        self.UAI_URL = "https://uai.unipus.cn"
        self.UCONTENT_URL = "https://ucontent.unipus.cn"
        
        # 设置默认请求头
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })
    
    def _base64url_encode(self, data: bytes) -> str:
        """Base64URL 编码"""
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')
    
    def generate_jwt(self, open_id: str) -> str:
        """生成 JWT Token"""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "open_id": open_id,
            "name": "",
            "email": "",
            "administrator": False,
            "exp": int(time.time() * 1000) + 31536000000,
            "iss": self.JWT_ISS,
            "aud": self.JWT_AUD,
        }
        
        header_b64 = self._base64url_encode(json.dumps(header, separators=(',', ':')).encode())
        payload_b64 = self._base64url_encode(json.dumps(payload, separators=(',', ':')).encode())
        signing_input = f"{header_b64}.{payload_b64}"
        
        signature = hmac.new(
            self.JWT_SECRET.encode(),
            signing_input.encode(),
            hashlib.sha256
        ).digest()
        
        return f"{header_b64}.{payload_b64}.{self._base64url_encode(signature)}"
    
    def print_response(self, title: str, response: requests.Response):
        """打印响应结果"""
        print(f"\n{'='*60}")
        print(f"📡 {title}")
        print(f"{'='*60}")
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        print(f"\nHeaders:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'set-cookie', 'x-request-id']:
                print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except:
            print(response.text[:500])
            return None
    
    # ==================== SSO 登录 ====================
    
    def sso_login(self, username: str = None, password: str = None) -> bool:
        """SSO 登录"""
        if username:
            self.username = username
        if password:
            self.password = password
            
        url = f"{self.SSO_URL}/sso/0.1/sso/login"
        data = {
            "service": "https://u.unipus.cn/user/comm/login?school_id=",
            "username": self.username,
            "password": self.password,
            "captcha": "",
            "rememberMe": "on",
            "captchaCode": "",
            "encodeCaptha": ""
        }
        
        print(f"\n🔑 正在登录: {self.username}")
        resp = self.session.post(url, json=data)
        result = self.print_response("SSO 登录", resp)
        
        if result and result.get("code") == "0":
            rs = result.get("rs", {})
            self.open_id = rs.get("openId", "")
            self.service_ticket = rs.get("serviceTicket", "")
            self.jwt_token = self.generate_jwt(self.open_id)
            self.session.headers["X-Annotator-Auth-Token"] = self.jwt_token
            print(f"\n✅ 登录成功!")
            print(f"   Open ID: {self.open_id}")
            print(f"   JWT Token: {self.jwt_token[:50]}...")
            return True
        elif result and result.get("code") == "1502":
            print(f"\n⚠️ 需要验证码")
            return self._handle_captcha()
        else:
            print(f"\n❌ 登录失败: {result.get('msg', '未知错误')}")
            return False
    
    def _handle_captcha(self) -> bool:
        """处理验证码"""
        url = f"{self.SSO_URL}/sso/4.0/sso/image_captcha2"
        resp = self.session.post(url)
        result = self.print_response("获取验证码", resp)
        
        if result and result.get("code") == "0":
            rs = result.get("rs", {})
            image_b64 = rs.get("image", "")
            encode_captcha = rs.get("encodeCaptha", "")
            
            # 保存验证码图片
            import base64
            with open('/data/user/work/captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(image_b64))
            print(f"\n📸 验证码已保存到 /data/user/work/captcha.jpg")
            
            # 手动输入验证码
            captcha_code = input("请输入验证码: ").strip()
            
            # 重新登录
            url = f"{self.SSO_URL}/sso/0.1/sso/login"
            data = {
                "service": "https://u.unipus.cn/user/comm/login?school_id=",
                "username": self.username,
                "password": self.password,
                "captcha": captcha_code,
                "rememberMe": "on",
                "captchaCode": captcha_code,
                "encodeCaptha": encode_captcha
            }
            
            resp = self.session.post(url, json=data)
            result = self.print_response("验证码登录", resp)
            
            if result and result.get("code") == "0":
                rs = result.get("rs", {})
                self.open_id = rs.get("openId", "")
                self.service_ticket = rs.get("serviceTicket", "")
                self.jwt_token = self.generate_jwt(self.open_id)
                self.session.headers["X-Annotator-Auth-Token"] = self.jwt_token
                print(f"\n✅ 登录成功!")
                return True
        
        return False
    
    # ==================== UAI 平台 API ====================
    
    def uai_get_courses(self):
        """UAI - 获取课程列表"""
        url = f"{self.UAI_URL}/learn/api/v2/course/list"
        resp = self.session.get(url)
        return self.print_response("UAI - 课程列表", resp)
    
    def uai_submit_progress(self, course_id: str, unit_id: str, duration: int = 30):
        """UAI - 提交课程进度"""
        url = f"{self.UAI_URL}/learn/api/v2/record/progress"
        data = {
            "courseId": course_id,
            "unitId": unit_id,
            "openId": self.open_id,
            "duration": duration
        }
        resp = self.session.post(url, json=data)
        return self.print_response("UAI - 提交进度", resp)
    
    # ==================== UContent 平台 API ====================
    
    def ucontent_course_details(self, course_id: str = None):
        """UContent - 获取课程详情"""
        if course_id:
            self.course_id = course_id
        url = f"{self.UCONTENT_URL}/course/api/v4/lms/course/details?courseId={self.course_id}"
        resp = self.session.get(url)
        return self.print_response("UContent - 课程详情", resp)
    
    def ucontent_get_content(self, group_id: str):
        """UContent - 获取课程内容"""
        url = f"{self.UCONTENT_URL}/course/api/v3/content/{self.course_id}/{group_id}/default"
        resp = self.session.get(url)
        return self.print_response(f"UContent - 课程内容 (group: {group_id})", resp)
    
    def ucontent_get_answer(self, group_id: str, mode: str = "default"):
        """UContent - 获取答案与解析"""
        url = f"{self.UCONTENT_URL}/course/api/v3/answer/{self.course_id}/{group_id}/{mode}"
        resp = self.session.get(url)
        return self.print_response(f"UContent - 答案解析 (group: {group_id})", resp)
    
    def ucontent_save_progress(self, group_id: str):
        """UContent - 保存进度（text/video 类型）"""
        url = f"{self.UCONTENT_URL}/api/mobile/user_group/{self.course_id}/{group_id}/progress"
        data = {
            "groupId": group_id,
            "status": 2,
            "version": "default"
        }
        resp = self.session.post(url, json=data)
        return self.print_response(f"UContent - 保存进度 (group: {group_id})", resp)
    
    def ucontent_submit_task(self, group_id: str, question_count: int = 1):
        """UContent - 提交答案（task 类型）"""
        url = f"{self.UCONTENT_URL}/course/api/v3/newExploration/submit"
        
        # 构造答案数据
        ques_datas = []
        for i in range(question_count):
            ques_datas.append({
                "instanceId": f"ques_{i}",
                "answer": "{}",
                "context": "{}",
                "contextVersion": 0,
                "answerVersion": 0
            })
        
        data = {
            "quesDatas": ques_datas,
            "groupId": group_id,
            "isCompleted": [True],
            "thirdPartyJudges": "[]",
            "submitType": 1,
            "hideLoading": True,
            "associationGroupId": "",
            "associationUnitId": "",
            "courseId": self.course_id,
            "openId": self.open_id,
            "version": "default"
        }
        
        resp = self.session.post(url, json=data)
        return self.print_response(f"UContent - 提交答案 (group: {group_id})", resp)
    
    def ucontent_course_progress(self):
        """UContent - 查询课程进度"""
        url = f"{self.UCONTENT_URL}/course/api/v2/course_progress/{self.course_id}/{self.open_id}/default"
        resp = self.session.get(url)
        return self.print_response("UContent - 课程进度", resp)
    
    def ucontent_unit_progress(self, unit_id: str):
        """UContent - 查询单元进度"""
        url = f"{self.UCONTENT_URL}/course/api/v2/course_progress/{self.course_id}/{unit_id}/{self.open_id}/default"
        resp = self.session.get(url)
        return self.print_response(f"UContent - 单元进度 (unit: {unit_id})", resp)
    
    def ucontent_group_state(self, group_id: str):
        """UContent - 查询 Group 状态"""
        url = f"{self.UCONTENT_URL}/api/mobile/user_module/{self.course_id}/{group_id}/progress/v2"
        resp = self.session.get(url)
        return self.print_response(f"UContent - Group状态 (group: {group_id})", resp)
    
    def ucontent_user_answer(self, group_id: str, version: str = "default"):
        """UContent - 查询用户答案"""
        url = f"{self.UCONTENT_URL}/api/mobile/user_module/{self.course_id}/{group_id}-{version}"
        resp = self.session.get(url)
        return self.print_response(f"UContent - 用户答案 (group: {group_id})", resp)


def interactive_menu():
    """交互式菜单"""
    client = UClient()
    
    print("\n" + "="*60)
    print("🎓 U校园 API 调试客户端")
    print("="*60)
    
    # 配置账号
    print("\n📋 账号配置")
    client.username = input("用户名 (手机号): ").strip() or "17716841865"
    client.password = input("密码: ").strip() or "ff@00000"
    client.course_id = input("课程ID: ").strip() or "course-v2:75bd6c9770028fd+ljddzg_rw+20230403"
    
    # 登录
    if not client.sso_login():
        print("登录失败，退出")
        return
    
    while True:
        print("\n" + "="*60)
        print("📚 请选择要测试的 API:")
        print("="*60)
        print("\n【UAI 平台】")
        print("  1. 获取课程列表")
        print("  2. 提交课程进度")
        print("\n【UContent 平台】")
        print("  3. 获取课程详情")
        print("  4. 获取课程内容")
        print("  5. 获取答案与解析")
        print("  6. 保存进度 (text/video)")
        print("  7. 提交答案 (task)")
        print("  8. 查询课程进度")
        print("  9. 查询单元进度")
        print("  10. 查询 Group 状态")
        print("  11. 查询用户答案")
        print("\n【其他】")
        print("  0. 退出")
        print("="*60)
        
        choice = input("\n请输入选项: ").strip()
        
        if choice == "0":
            print("\n👋 再见!")
            break
            
        elif choice == "1":
            client.uai_get_courses()
            
        elif choice == "2":
            unit_id = input("单元ID: ").strip()
            duration = int(input("学习时长(秒): ").strip() or "30")
            client.uai_submit_progress(client.course_id, unit_id, duration)
            
        elif choice == "3":
            client.ucontent_course_details()
            
        elif choice == "4":
            group_id = input("Group ID: ").strip()
            client.ucontent_get_content(group_id)
            
        elif choice == "5":
            group_id = input("Group ID: ").strip()
            mode = input("Mode (default/preview): ").strip() or "default"
            client.ucontent_get_answer(group_id, mode)
            
        elif choice == "6":
            group_id = input("Group ID: ").strip()
            client.ucontent_save_progress(group_id)
            
        elif choice == "7":
            group_id = input("Group ID: ").strip()
            count = int(input("题目数量: ").strip() or "1")
            client.ucontent_submit_task(group_id, count)
            
        elif choice == "8":
            client.ucontent_course_progress()
            
        elif choice == "9":
            unit_id = input("单元ID: ").strip()
            client.ucontent_unit_progress(unit_id)
            
        elif choice == "10":
            group_id = input("Group ID: ").strip()
            client.ucontent_group_state(group_id)
            
        elif choice == "11":
            group_id = input("Group ID: ").strip()
            client.ucontent_user_answer(group_id)
            
        else:
            print("\n❌ 无效选项")
        
        input("\n按回车继续...")


if __name__ == "__main__":
    interactive_menu()
