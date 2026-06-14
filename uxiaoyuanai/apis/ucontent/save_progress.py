#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 保存进度
适用于 text/video 类型的 group
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def save_progress(group_id: str, course_id: str = None, jwt_token: str = None) -> dict:
    """
    保存进度 (text/video 类型)
    
    Args:
        group_id: Group ID
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/api/mobile/user_group/{course_id}/{group_id}/progress"
    
    payload = {
        "groupId": group_id,
        "status": 2,
        "version": "default"
    }
    
    session = create_session(jwt_token)
    resp = session.post(url, json=payload)
    data = print_response(f"UContent - 保存进度 (group: {group_id})", resp)
    
    if data and data.get("code") == 0:
        print_result(True, "进度保存成功")
        return {"success": True}
    
    print_result(False, f"进度保存失败: {data.get('msg', '') if data else '无响应'}")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="保存进度 (text/video)")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    save_progress(args.group_id, args.course_id)
