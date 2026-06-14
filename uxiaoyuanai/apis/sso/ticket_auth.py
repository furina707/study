#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSO - Ticket认证
使用 serviceTicket 建立 session
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def ticket_auth(service_ticket: str) -> dict:
    """
    Ticket认证
    
    Args:
        service_ticket: SSO登录返回的 serviceTicket
    
    Returns:
        dict: {"success": bool, "cookies": dict}
    """
    url = f"https://u.unipus.cn/user/comm/login?school_id=&ticket={service_ticket}"
    
    session = create_session()
    resp = session.get(url)
    
    print(f"\n{'='*60}")
    print(f"📡 SSO - Ticket认证")
    print(f"{'='*60}")
    print(f"Status: {resp.status_code}")
    print(f"URL: {resp.url}")
    
    # 获取 cookies
    cookies = dict(session.cookies)
    
    if resp.status_code == 200:
        print_result(True, "Ticket认证成功")
        print(f"\nCookies: {cookies}")
        return {"success": True, "cookies": cookies, "session": session}
    
    print_result(False, "Ticket认证失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SSO Ticket认证")
    parser.add_argument("-t", "--ticket", required=True, help="serviceTicket")
    args = parser.parse_args()
    
    ticket_auth(args.ticket)
