#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取验证码 API
当登录返回 code=1502 时调用
"""

import sys
import os
import base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import *

def get_captcha(save_path: str = "/data/user/work/captcha.jpg") -> dict:
    """
    获取验证码图片
    
    Args:
        save_path: 验证码图片保存路径
    
    Returns:
        dict: {"success": bool, "encode_captha": str, "image_path": str}
    """
    url = f"{SSO_URL}/sso/4.0/sso/image_captcha2"
    
    session = create_session()
    resp = session.post(url)
    data = print_response("获取验证码", resp)
    
    if data and data.get("code") == "0":
        rs = data.get("rs", {})
        image_b64 = rs.get("image", "")
        encode_captha = rs.get("encodeCaptha", "")
        
        # 保存验证码图片
        if image_b64:
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(image_b64))
            print_result(True, f"验证码已保存", {"image_path": save_path, "encode_captha": encode_captha})
            return {"success": True, "encode_captha": encode_captha, "image_path": save_path}
    
    print_result(False, "获取验证码失败")
    return {"success": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="获取验证码")
    parser.add_argument("-o", "--output", default="/data/user/work/captcha.jpg", help="验证码保存路径")
    args = parser.parse_args()
    
    get_captcha(args.output)
