"""
超星学习通账号密码登录 API
POST https://passport2.chaoxing.com/fanyalogin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests
import urllib3
from crypto_utils import ChaoxingCrypto

# 修改TLS指纹
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])


class FanyaloginAPI:
    """
    超星学习通账号密码登录
    
    API端点: POST https://passport2.chaoxing.com/fanyalogin
    Content-Type: application/x-www-form-urlencoded; charset=UTF-8
    """
    
    URL = "https://passport2.chaoxing.com/fanyalogin"
    
    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
        'Origin': 'https://passport2.chaoxing.com',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def login(self, username: str, password: str, fid: str = "", refer: str = None) -> dict:
        """
        执行登录
        
        Args:
            username: 用户名（手机号/邮箱）
            password: 密码
            fid: 机构ID（可选）
            refer: 跳转地址（可选）
            
        Returns:
            登录结果字典:
            - status: bool 是否成功
            - msg: str 消息
            - cookies: dict Cookie信息
        """
        # 加密用户名和密码
        encrypted_username = ChaoxingCrypto.encrypt_username(username)
        encrypted_password = ChaoxingCrypto.encrypt_password(password)
        
        # 准备请求数据
        data = {
            'fid': fid,
            'uname': encrypted_username,
            'password': encrypted_password,
            'refer': refer or 'https%3A%2F%2Fi.chaoxing.com%2F',
            't': 'true',
            'forbidotherlogin': '0',
            'validate': '',
        }
        
        try:
            response = self.session.post(
                self.URL,
                headers=self.HEADERS,
                data=data
            )
            
            result = response.json()
            
            # 获取Cookie
            cookies = dict(self.session.cookies)
            
            return {
                'status': result.get('status', False),
                'msg': result.get('msg2') or result.get('msg', '未知错误'),
                'cookies': cookies,
                'response': result,
            }
            
        except Exception as e:
            return {
                'status': False,
                'msg': f'请求异常: {e}',
                'cookies': {},
                'response': {},
            }


def main():
    """测试登录"""
    print("=" * 50)
    print("超星学习通账号密码登录")
    print("=" * 50)
    
    username = input("请输入用户名（手机号/邮箱）: ").strip()
    password = input("请输入密码: ").strip()
    
    if not username or not password:
        print("用户名或密码不能为空")
        return
    
    api = FanyaloginAPI()
    result = api.login(username, password)
    
    if result['status']:
        print("\n登录成功!")
        print(f"消息: {result['msg']}")
        print(f"\nCookie数量: {len(result['cookies'])}")
        for key, value in list(result['cookies'].items())[:5]:
            print(f"  {key}: {value[:20]}..." if len(value) > 20 else f"  {key}: {value}")
    else:
        print(f"\n登录失败: {result['msg']}")


if __name__ == "__main__":
    main()
