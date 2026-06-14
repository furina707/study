#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 获取课程内容
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_content(group_id: str, course_id: str = None, jwt_token: str = None) -> dict:
    """
    获取课程内容
    
    Args:
        group_id: Group ID
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "content": str}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/course/api/v3/content/{course_id}/{group_id}/default"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response(f"UContent - 课程内容 (group: {group_id})", resp)
    
    if data and data.get("code") == 0:
        content = data.get("data", {}).get("content", "")
        print_result(True, "获取内容成功")
        return {"success": True, "content": content}
    
    print_result(False, "获取内容失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取课程内容")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_content(args.group_id, args.course_id)
