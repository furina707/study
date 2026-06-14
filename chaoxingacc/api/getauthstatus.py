"""
超星学习通二维码状态查询 API
GET https://passport2.chaoxing.com/getauthstatus
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests
import urllib3
import time

# 修改TLS指纹
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])


class GetAuthStatusAPI:
    """
    超星学习通二维码登录 - 查询扫码状态
    
    API端点: GET https://passport2.chaoxing.com/getauthstatus
    """
    
    URL = "https://passport2.chaoxing.com/getauthstatus"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    # 状态码映射
    STATUS_MAP = {
        0: '未登录',
        1: '已扫描',
        2: '取消扫描',
        3: '验证通过',
        4: '已过期',
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_status(self, uuid: str) -> dict:
        """
        查询二维码扫码状态
        
        Args:
            uuid: 二维码UUID
            
        Returns:
            结果字典:
            - status_code: int 状态码 (0-4)
            - status_text: str 状态文本
            - is_logged_in: bool 是否已登录
            - cookies: dict Cookie信息（登录成功时）
            - msg: str 消息
        """
        params = {
            'uuid': uuid,
        }
        
        try:
            response = self.session.get(
                self.URL,
                headers=self.HEADERS,
                params=params
            )
            
            result = response.json()
            status_code = result.get('status', 0)
            status_text = self.STATUS_MAP.get(status_code, '未知状态')
            
            # 获取Cookie
            cookies = dict(self.session.cookies)
            
            return {
                'status_code': status_code,
                'status_text': status_text,
                'is_logged_in': status_code == 3,
                'cookies': cookies,
                'msg': result.get('msg', status_text),
                'response': result,
            }
            
        except Exception as e:
            return {
                'status_code': -1,
                'status_text': '请求异常',
                'is_logged_in': False,
                'cookies': {},
                'msg': f'请求异常: {e}',
                'response': {},
            }
    
    def wait_for_scan(self, uuid: str, interval: int = 2, timeout: int = 120) -> dict:
        """
        等待扫码完成
        
        Args:
            uuid: 二维码UUID
            interval: 查询间隔（秒）
            timeout: 超时时间（秒）
            
        Returns:
            最终状态结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_status(uuid)
            
            print(f"状态: {result['status_text']}")
            
            if result['is_logged_in']:
                print("登录成功!")
                return result
            
            if result['status_code'] in [2, 4]:  # 取消或过期
                print(f"扫码{result['status_text']}")
                return result
            
            time.sleep(interval)
        
        return {
            'status_code': 4,
            'status_text': '超时',
            'is_logged_in': False,
            'cookies': {},
            'msg': '等待超时',
            'response': {},
        }


def main():
    """测试查询状态"""
    print("=" * 50)
    print("超星学习通二维码登录 - 查询扫码状态")
    print("=" * 50)
    
    uuid = input("请输入二维码UUID: ").strip()
    
    if not uuid:
        print("UUID不能为空")
        return
    
    api = GetAuthStatusAPI()
    
    print("\n开始查询状态...")
    result = api.wait_for_scan(uuid)
    
    if result['is_logged_in']:
        print(f"\n登录成功!")
        print(f"Cookie数量: {len(result['cookies'])}")
    else:
        print(f"\n最终状态: {result['status_text']}")


if __name__ == "__main__":
    main()
