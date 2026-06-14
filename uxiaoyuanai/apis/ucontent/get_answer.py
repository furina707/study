#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 获取答案与解析
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_answer(group_id: str, mode: str = "default", 
               course_id: str = None, jwt_token: str = None) -> dict:
    """
    获取答案与解析
    
    Args:
        group_id: Group ID
        mode: 模式 (default/preview)
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "answer": dict}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/course/api/v3/answer/{course_id}/{group_id}/{mode}"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response(f"UContent - 答案解析 (group: {group_id})", resp)
    
    if data and data.get("code") == 0:
        print_result(True, "获取答案成功")
        return {"success": True, "answer": data.get("data")}
    
    print_result(False, "获取答案失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取答案与解析")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-m", "--mode", default="default", help="模式 (default/preview)")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_answer(args.group_id, args.mode, args.course_id)
