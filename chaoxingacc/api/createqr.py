"""
超星学习通二维码生成 API
GET https://passport2.chaoxing.com/createqr
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests
import urllib3
import uuid

# 修改TLS指纹
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])


class CreateQRCodeAPI:
    """
    超星学习通二维码登录 - 生成二维码
    
    API端点: GET https://passport2.chaoxing.com/createqr
    """
    
    URL = "https://passport2.chaoxing.com/createqr"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def generate_uuid(self) -> str:
        """生成UUID"""
        return str(uuid.uuid4()).replace('-', '')
    
    def create_qrcode(self, uuid_str: str = None) -> dict:
        """
        生成登录二维码
        
        Args:
            uuid_str: UUID字符串，不传则自动生成
            
        Returns:
            结果字典:
            - status: bool 是否成功
            - uuid: str UUID
            - qrcode_url: str 二维码图片URL
            - msg: str 消息
        """
        if not uuid_str:
            uuid_str = self.generate_uuid()
        
        params = {
            'uuid': uuid_str,
        }
        
        try:
            response = self.session.get(
                self.URL,
                headers=self.HEADERS,
                params=params
            )
            
            if response.status_code == 200:
                # 返回的是二维码图片URL
                qrcode_url = response.url
                
                return {
                    'status': True,
                    'uuid': uuid_str,
                    'qrcode_url': qrcode_url,
                    'msg': '二维码生成成功',
                }
            else:
                return {
                    'status': False,
                    'uuid': uuid_str,
                    'qrcode_url': '',
                    'msg': f'请求失败，状态码: {response.status_code}',
                }
                
        except Exception as e:
            return {
                'status': False,
                'uuid': uuid_str,
                'qrcode_url': '',
                'msg': f'请求异常: {e}',
            }


def main():
    """测试生成二维码"""
    print("=" * 50)
    print("超星学习通二维码登录 - 生成二维码")
    print("=" * 50)
    
    api = CreateQRCodeAPI()
    result = api.create_qrcode()
    
    if result['status']:
        print("\n二维码生成成功!")
        print(f"UUID: {result['uuid']}")
        print(f"\n二维码URL: {result['qrcode_url']}")
        print("\n请使用学习通APP扫描此二维码登录")
        print(f"\n下一步: 使用 getauthstatus.py 查询扫码状态")
        print(f"参数 uuid: {result['uuid']}")
    else:
        print(f"\n生成失败: {result['msg']}")


if __name__ == "__main__":
    main()
