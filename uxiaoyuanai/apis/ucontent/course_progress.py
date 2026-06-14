#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 查询课程进度
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_course_progress(course_id: str = None, open_id: str = None,
                        jwt_token: str = None) -> dict:
    """
    查询课程进度
    
    Args:
        course_id: 课程ID
        open_id: 用户OpenID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "progress": dict}
    """
    course_id = course_id or COURSE_ID
    open_id = open_id or OPEN_ID
    jwt_token = jwt_token or generate_jwt(open_id)
    
    url = f"{UCONTENT_URL}/course/api/v2/course_progress/{course_id}/{open_id}/default"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response("UContent - 课程进度", resp)
    
    if data and data.get("code") == 0:
        print_result(True, "获取课程进度成功")
        return {"success": True, "progress": data.get("data")}
    
    print_result(False, "获取课程进度失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查询课程进度")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_course_progress(args.course_id)
