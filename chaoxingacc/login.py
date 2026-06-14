"""
超星学习通登录模块
处理账号密码登录和Cookie管理
"""

import requests
from curl_cffi import requests as cffi_requests
import urllib3
from typing import Optional, Dict
from crypto_utils import ChaoxingCrypto


# 修改TLS指纹以绕过检测
urllib3.util.ssl_.DEFAULT_CIPHERS = ":".join([
    "DH+AESGCM", "ECDH+AES", "DH+AES",
    "RSA+AESGCM", "RSA+AES", "!aNULL", "!eNULL", "!MD5", "!DSS",
])


class ChaoxingLogin:
    """超星学习通登录类"""
    
    # API端点
    LOGIN_URL = "https://passport2.chaoxing.com/fanyalogin"
    BASE_URL = "https://i.chaoxing.com/base"
    
    # 默认请求头
    DEFAULT_HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://passport2.chaoxing.com/login',
    }
    
    def __init__(self):
        self.session = cffi_requests.Session()
        self.cookies: Dict[str, str] = {}
        self.uid: Optional[str] = None
        self.is_logged_in = False
    
    def login(self, username: str, password: str) -> bool:
        """
        使用账号密码登录
        
        Args:
            username: 用户名（手机号/邮箱）
            password: 密码
            
        Returns:
            登录是否成功
        """
        try:
            # 加密用户名和密码
            encrypted_username = ChaoxingCrypto.encrypt_username(username)
            encrypted_password = ChaoxingCrypto.encrypt_password(password)
            
            print(f"正在登录用户: {username}")
            
            # 准备登录数据
            data = {
                'uname': encrypted_username,
                'password': encrypted_password,
                'refer': 'https%3A%2F%2Fi.chaoxing.com%2F',
                't': 'true',
            }
            
            # 第一次请求：登录
            response = self.session.post(
                self.LOGIN_URL,
                headers=self.DEFAULT_HEADERS,
                data=data
            )
            
            if response.status_code != 200:
                print(f"登录请求失败，状态码: {response.status_code}")
                return False
            
            # 检查登录结果
            result = response.json()
            if not result.get('status', False):
                print(f"登录失败: {result.get('msg', '未知错误')}")
                return False
            
            print("登录成功，正在获取Cookie...")
            
            # 第二次请求：获取完整Cookie
            base_response = self.session.get(
                self.BASE_URL,
                headers=self.DEFAULT_HEADERS
            )
            
            # 保存Cookie
            self.cookies = dict(self.session.cookies)
            
            # 提取UID
            self.uid = self.cookies.get('UID') or self._extract_uid()
            
            if self.uid:
                print(f"登录成功，UID: {self.uid}")
                self.is_logged_in = True
                return True
            else:
                print("警告: 未能提取UID，但登录可能已成功")
                self.is_logged_in = True
                return True
                
        except Exception as e:
            print(f"登录异常: {e}")
            return False
    
    def _extract_uid(self) -> Optional[str]:
        """从Cookie中提取UID"""
        # 尝试从不同Cookie字段提取
        for key in ['UID', 'uid', 'fid']:
            if key in self.cookies:
                return self.cookies[key]
        return None
    
    def get_cookies(self) -> Dict[str, str]:
        """获取当前Cookie"""
        return self.cookies
    
    def get_uid(self) -> Optional[str]:
        """获取用户ID"""
        return self.uid
    
    def check_login_status(self) -> bool:
        """检查登录状态是否有效"""
        if not self.is_logged_in:
            return False
        
        try:
            response = self.session.get(
                self.BASE_URL,
                headers=self.DEFAULT_HEADERS,
                cookies=self.cookies
            )
            return response.status_code == 200
        except:
            return False
    
    def save_cookies_to_file(self, filepath: str = "cookies.txt"):
        """保存Cookie到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for key, value in self.cookies.items():
                f.write(f"{key}={value}\n")
        print(f"Cookie已保存到: {filepath}")
    
    def load_cookies_from_file(self, filepath: str = "cookies.txt") -> bool:
        """从文件加载Cookie"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self.cookies[key] = value
            
            self.session.cookies.update(self.cookies)
            self.uid = self._extract_uid()
            self.is_logged_in = True
            print(f"已从文件加载Cookie")
            return True
        except FileNotFoundError:
            print(f"Cookie文件不存在: {filepath}")
            return False
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return False


if __name__ == "__main__":
    # 测试登录
    login = ChaoxingLogin()
    
    # 从文件加载Cookie或登录
    if not login.load_cookies_from_file():
        username = input("请输入用户名: ")
        password = input("请输入密码: ")
        if login.login(username, password):
            login.save_cookies_to_file()
        else:
            print("登录失败")
    else:
        print("使用已保存的Cookie")
    
    if login.is_logged_in:
        print(f"当前UID: {login.get_uid()}")
        print(f"登录状态: {login.check_login_status()}")
