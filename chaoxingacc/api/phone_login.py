"""
超星学习通手机号验证码登录 API
POST https://passport2.chaoxing.com/login
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests
import urllib3

# 修改TLS指纹
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])


class PhoneLoginAPI:
    """
    超星学习通手机号验证码登录
    
    API端点: POST https://passport2.chaoxing.com/login
    """
    
    URL = "https://passport2.chaoxing.com/login"
    
    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
        'Origin': 'https://passport2.chaoxing.com',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def login(self, phone: str, code: str, fid: str = "") -> dict:
        """
        验证码登录
        
        Args:
            phone: 手机号
            code: 验证码
            fid: 机构ID（可选）
            
        Returns:
            结果字典:
            - status: bool 是否成功
            - msg: str 消息
            - cookies: dict Cookie信息
        """
        data = {
            'fid': fid,
            'phone': phone,
            'code': code,
            't': 'true',
            'refer': 'https%3A%2F%2Fi.chaoxing.com%2F',
            'forbidotherlogin': '0',
        }
        
        try:
            response = self.session.post(
                self.URL,
                headers=self.HEADERS,
                data=data
            )
            
            # 获取Cookie
            cookies = dict(self.session.cookies)
            
            # 检查是否登录成功（通过响应内容或重定向判断）
            if response.status_code in [200, 302]:
                # 尝试解析JSON响应
                try:
                    result = response.json()
                    status = result.get('status', False)
                    msg = result.get('msg', '')
                except:
                    # 非JSON响应，可能是重定向成功
                    status = True
                    msg = '登录成功'
                
                return {
                    'status': status or len(cookies) > 0,
                    'msg': msg or '登录成功',
                    'cookies': cookies,
                }
            else:
                return {
                    'status': False,
                    'msg': f'请求失败，状态码: {response.status_code}',
                    'cookies': {},
                }
            
        except Exception as e:
            return {
                'status': False,
                'msg': f'请求异常: {e}',
                'cookies': {},
            }


def main():
    """测试验证码登录"""
    print("=" * 50)
    print("超星学习通手机号验证码登录")
    print("=" * 50)
    
    phone = input("请输入手机号: ").strip()
    code = input("请输入验证码: ").strip()
    
    if not phone or not code:
        print("手机号或验证码不能为空")
        return
    
    api = PhoneLoginAPI()
    result = api.login(phone, code)
    
    if result['status']:
        print(f"\n登录成功!")
        print(f"消息: {result['msg']}")
        print(f"\nCookie数量: {len(result['cookies'])}")
    else:
        print(f"\n登录失败: {result['msg']}")


if __name__ == "__main__":
    main()
