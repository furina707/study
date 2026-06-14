"""
超星学习通用户注册 API
POST https://passport2.chaoxing.com/register
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


class RegisterAPI:
    """
    超星学习通用户注册
    
    API端点: POST https://passport2.chaoxing.com/register
    """
    
    URL = "https://passport2.chaoxing.com/register"
    
    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
        'Origin': 'https://passport2.chaoxing.com',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def register(self, phone: str, code: str, password: str, name: str = "") -> dict:
        """
        用户注册
        
        Args:
            phone: 手机号
            code: 验证码
            password: 密码
            name: 姓名（可选）
            
        Returns:
            结果字典:
            - status: bool 是否成功
            - msg: str 消息
        """
        data = {
            'phone': phone,
            'code': code,
            'password': password,
            'name': name,
        }
        
        try:
            response = self.session.post(
                self.URL,
                headers=self.HEADERS,
                data=data
            )
            
            result = response.json()
            
            return {
                'status': result.get('result', False),
                'msg': result.get('msg', '未知错误'),
                'response': result,
            }
            
        except Exception as e:
            return {
                'status': False,
                'msg': f'请求异常: {e}',
                'response': {},
            }


def main():
    """测试注册"""
    print("=" * 50)
    print("超星学习通用户注册")
    print("=" * 50)
    
    phone = input("请输入手机号: ").strip()
    code = input("请输入验证码: ").strip()
    password = input("请输入密码: ").strip()
    name = input("请输入姓名（可选）: ").strip()
    
    if not phone or not code or not password:
        print("手机号、验证码和密码不能为空")
        return
    
    api = RegisterAPI()
    result = api.register(phone, code, password, name)
    
    if result['status']:
        print(f"\n注册成功!")
        print(f"消息: {result['msg']}")
    else:
        print(f"\n注册失败: {result['msg']}")


if __name__ == "__main__":
    main()
