"""
超星学习通手机验证码发送 API
POST https://passport2.chaoxing.com/register/sendcode
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


class SendCodeAPI:
    """
    超星学习通发送手机验证码
    
    API端点: POST https://passport2.chaoxing.com/register/sendcode
    """
    
    URL = "https://passport2.chaoxing.com/register/sendcode"
    
    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
        'Origin': 'https://passport2.chaoxing.com',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def send_code(self, phone: str) -> dict:
        """
        发送手机验证码
        
        Args:
            phone: 手机号
            
        Returns:
            结果字典:
            - status: bool 是否成功
            - msg: str 消息
        """
        data = {
            'phone': phone,
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
    """测试发送验证码"""
    print("=" * 50)
    print("超星学习通发送手机验证码")
    print("=" * 50)
    
    phone = input("请输入手机号: ").strip()
    
    if not phone:
        print("手机号不能为空")
        return
    
    if len(phone) != 11 or not phone.isdigit():
        print("手机号格式不正确")
        return
    
    api = SendCodeAPI()
    result = api.send_code(phone)
    
    if result['status']:
        print(f"\n验证码发送成功!")
        print(f"消息: {result['msg']}")
    else:
        print(f"\n发送失败: {result['msg']}")


if __name__ == "__main__":
    main()
