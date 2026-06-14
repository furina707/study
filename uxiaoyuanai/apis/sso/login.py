#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSO 登录 API
获取 serviceTicket 和 openId
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def sso_login(username: str = None, password: str = None) -> dict:
    """
    SSO 登录
    
    Args:
        username: 手机号 (默认使用 config.py 中的配置)
        password: 密码 (默认使用 config.py 中的配置)
    
    Returns:
        dict: {"success": bool, "open_id": str, "service_ticket": str, "jwt_token": str}
    """
    username = username or USERNAME
    password = password or PASSWORD
    
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
    
    session = create_session()
    resp = session.post(url, json=payload)
    data = print_response("SSO 登录", resp)
    
    if data and data.get("code") == "0":
        rs = data.get("rs", {})
        open_id = rs.get("openId", "")
        service_ticket = rs.get("serviceTicket", "")
        jwt_token = generate_jwt(open_id)
        
        print_result(True, "登录成功", {
            "open_id": open_id,
            "service_ticket": service_ticket,
            "jwt_token": jwt_token[:50] + "..."
        })
        
        return {
            "success": True,
            "open_id": open_id,
            "service_ticket": service_ticket,
            "jwt_token": jwt_token
        }
    
    elif data and data.get("code") == "1502":
        print_result(False, "需要验证码，请先调用 captcha API")
        return {"success": False, "need_captcha": True}
    
    print_result(False, f"登录失败: {data.get('msg', '未知错误') if data else '无响应'}")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SSO 登录")
    parser.add_argument("-u", "--username", help="手机号")
    parser.add_argument("-p", "--password", help="密码")
    args = parser.parse_args()
    
    sso_login(args.username, args.password)
