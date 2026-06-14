#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 查询 Group 状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_group_state(group_id: str, course_id: str = None,
                    jwt_token: str = None) -> dict:
    """
    查询 Group 状态
    
    Args:
        group_id: Group ID
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "state": dict}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/api/mobile/user_module/{course_id}/{group_id}/progress/v2"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response(f"UContent - Group状态 (group: {group_id})", resp)
    
    if data and data.get("code") == 0:
        state = data.get("data", {}).get("state", {})
        passed = state.get("pass") == 1
        status = "✅ 已通过" if passed else "❌ 未通过"
        print_result(True, f"状态: {status}, 得分: {state.get('score_pct', 0)}%")
        return {"success": True, "state": state}
    
    print_result(False, "获取 Group 状态失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查询 Group 状态")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_group_state(args.group_id, args.course_id)
