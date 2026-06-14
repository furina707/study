#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 查询用户答案
获取用户已提交的答案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_user_answer(group_id: str, version: str = "default",
                    course_id: str = None, jwt_token: str = None) -> dict:
    """
    查询用户答案
    
    Args:
        group_id: Group ID
        version: 版本 (默认 default)
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "answer": dict}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/api/mobile/user_module/{course_id}/{group_id}-{version}"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response(f"UContent - 用户答案 (group: {group_id})", resp)
    
    if data and data.get("code") == 0:
        answer_data = data.get("data", {})
        print_result(True, "获取用户答案成功")
        return {"success": True, "answer": answer_data}
    
    print_result(False, "获取用户答案失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查询用户答案")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-v", "--version", default="default", help="版本")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_user_answer(args.group_id, args.version, args.course_id)
