#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 获取课程详情
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_course_details(course_id: str = None, jwt_token: str = None) -> dict:
    """
    获取课程详情
    
    Args:
        course_id: 课程ID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "course": dict}
    """
    course_id = course_id or COURSE_ID
    jwt_token = jwt_token or generate_jwt(OPEN_ID)
    
    url = f"{UCONTENT_URL}/course/api/v4/lms/course/details?courseId={course_id}"
    
    session = create_session(jwt_token)
    resp = session.get(url)
    data = print_response("UContent - 课程详情", resp)
    
    if data and data.get("code") == 0:
        course = data.get("data", {}).get("course", {})
        units = course.get("units", [])
        print_result(True, f"课程: {course.get('name')}, 共 {len(units)} 个单元")
        return {"success": True, "course": course}
    
    print_result(False, "获取课程详情失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取课程详情")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    get_course_details(args.course_id)
