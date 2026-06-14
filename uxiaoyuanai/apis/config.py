#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共配置文件
所有 API 脚本共享此配置
"""

import json
import time
import hmac
import hashlib
import base64
import requests
from requests import Session
from typing import Optional, Dict, Any

# ==================== 账号配置 ====================
USERNAME = "17716841865"
PASSWORD = "ff@00000"
OPEN_ID = "2256906d61ab4304851b706b0364c4e8"
COURSE_ID = "course-v2:75bd6c9770028fd+ljddzg_rw+20230403"

# ==================== JWT 配置 ====================
JWT_SECRET = "a824b379f126b8b7aa5e33dee83fb0a05aa7462c"
JWT_ISS = "c4f772063dcfa98e9c50"
JWT_AUD = "edx.unipus.cn"

# ==================== URL 配置 ====================
SSO_URL = "https://sso.unipus.cn"
UAI_URL = "https://uai.unipus.cn"
UCONTENT_URL = "https://ucontent.unipus.cn"


def base64url_encode(data: bytes) -> str:
    """Base64URL 编码"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def generate_jwt(open_id: str) -> str:
    """生成 JWT Token"""
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


def create_session(jwt_token: str = None) -> Session:
    """创建带默认请求头的 Session"""
    session = Session()
    session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest"
    })
    if jwt_token:
        session.headers["X-Annotator-Auth-Token"] = jwt_token
    return session


def print_response(title: str, response: requests.Response) -> Optional[Dict]:
    """打印响应结果"""
    print(f"\n{'='*60}")
    print(f"📡 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"\nResponse:")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    except:
        print(response.text[:1000])
        return None


def print_result(success: bool, message: str, data: Any = None):
    """打印结果"""
    status = "✅" if success else "❌"
    print(f"\n{status} {message}")
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
