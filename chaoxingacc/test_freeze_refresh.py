#!/usr/bin/env python3
"""
测试超星学习通登录错误计数的刷新时间
"""

import sys
import time
sys.path.append('/home/furina/Desktop/study/chaoxingacc')

from api.fanyalogin import FanyaloginAPI

def wait_for_unfreeze(api, username, max_wait=1200):
    """等待账号解冻"""
    print("等待账号解冻...")
    start = time.time()
    
    while time.time() - start < max_wait:
        result = api.login(username, 'test_unfreeze')
        msg = result['msg']
        
        if '冻结' not in msg:
            print(f"账号已解冻! (等待了 {int(time.time() - start)} 秒)")
            return True
        
        print(f"  仍在冻结: {msg}")
        time.sleep(30)
    
    print("等待超时")
    return False


def test_error_count_refresh(api, username):
    """测试错误计数刷新时间"""
    print("\n=== 测试错误计数刷新 ===")
    
    # 第1次错误
    print("\n--- 错误第1次 ---")
    result = api.login(username, 'wrong_1')
    print(f"  返回: {result['msg']}")
    
    if '冻结' in result['msg']:
        print("意外触发冻结，测试终止")
        return
    
    # 等待30秒
    print("\n等待30秒...")
    time.sleep(30)
    
    # 第2次错误
    print("\n--- 等待30秒后错误第2次 ---")
    result = api.login(username, 'wrong_2')
    print(f"  返回: {result['msg']}")
    
    # 分析结果
    if '6次' in result['msg'] or '5次' in result['msg']:
        print("\n结论: 错误计数在30秒内未重置")
    elif '用户名或密码错误' in result['msg']:
        print("\n结论: 错误计数在30秒内重置了!")
    
    # 等待2分钟
    print("\n等待2分钟...")
    time.sleep(120)
    
    # 再次错误
    print("\n--- 等待2分钟后再错误 ---")
    result = api.login(username, 'wrong_3')
    print(f"  返回: {result['msg']}")
    
    if '用户名或密码错误' in result['msg']:
        print("\n结论: 错误计数在2分钟后重置了!")
    else:
        print("\n结论: 错误计数在2分钟后仍未重置")


def main():
    api = FanyaloginAPI()
    username = '15982477461'
    
    # 先检查是否已解冻
    result = api.login(username, 'check_status')
    print(f"当前状态: {result['msg']}")
    
    if '冻结' in result['msg']:
        # 等待解冻
        if not wait_for_unfreeze(api, username):
            return
    
    # 测试错误计数刷新
    test_error_count_refresh(api, username)


if __name__ == '__main__':
    main()
