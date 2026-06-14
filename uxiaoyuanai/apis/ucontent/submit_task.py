#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UContent - 提交答案
适用于 task 类型的 group
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def submit_task(group_id: str, question_count: int = 1,
                course_id: str = None, open_id: str = None,
                jwt_token: str = None) -> dict:
    """
    提交答案 (task 类型)
    
    Args:
        group_id: Group ID
        question_count: 题目数量
        course_id: 课程ID
        open_id: 用户OpenID
        jwt_token: JWT Token
    
    Returns:
        dict: {"success": bool, "code": int}
    """
    course_id = course_id or COURSE_ID
    open_id = open_id or OPEN_ID
    jwt_token = jwt_token or generate_jwt(open_id)
    
    url = f"{UCONTENT_URL}/course/api/v3/newExploration/submit"
    
    # 构造答案数据
    ques_datas = []
    for i in range(question_count):
        ques_datas.append({
            "instanceId": f"ques_{i}",
            "answer": "{}",
            "context": "{}",
            "contextVersion": 0,
            "answerVersion": 0
        })
    
    payload = {
        "quesDatas": ques_datas,
        "groupId": group_id,
        "isCompleted": [True],
        "thirdPartyJudges": "[]",
        "submitType": 1,
        "hideLoading": True,
        "associationGroupId": "",
        "associationUnitId": "",
        "courseId": course_id,
        "openId": open_id,
        "version": "default"
    }
    
    session = create_session(jwt_token)
    resp = session.post(url, json=payload)
    data = print_response(f"UContent - 提交答案 (group: {group_id})", resp)
    
    if data:
        code = data.get("code")
        if code == 0:
            print_result(True, "提交成功")
            return {"success": True, "code": code}
        elif code == 300100:
            print_result(False, "题目数量不匹配，请调整 question_count 参数")
            return {"success": False, "code": code}
        elif code == 600002:
            print_result(False, "操作过于频繁，请稍后重试")
            return {"success": False, "code": code}
        else:
            print_result(False, f"提交失败: {data.get('msg', '')}")
            return {"success": False, "code": code}
    
    print_result(False, "无响应")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="提交答案 (task)")
    parser.add_argument("-g", "--group_id", required=True, help="Group ID")
    parser.add_argument("-n", "--count", type=int, default=1, help="题目数量")
    parser.add_argument("-c", "--course_id", help="课程ID")
    args = parser.parse_args()
    
    submit_task(args.group_id, args.count, args.course_id)
