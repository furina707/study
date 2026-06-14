"""
超星学习通加密模块
处理AES加密和MD5签名
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import hashlib
import base64


class ChaoxingCrypto:
    """超星学习通加密工具类"""
    
    # AES加密密钥
    AES_KEY = "u2oh6Vu^HWe4_AES"
    
    @classmethod
    def encrypt_aes(cls, plaintext: str) -> str:
        """
        AES-CBC加密（学习通使用的方式）
        
        Args:
            plaintext: 明文内容
            
        Returns:
            Base64编码的加密结果
        """
        try:
            # 使用密钥作为IV
            key = cls.AES_KEY.encode('utf-8')
            iv = key  # IV与key相同
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise Exception(f"AES加密失败: {e}")
    
    @classmethod
    def encrypt_username(cls, username: str) -> str:
        """加密用户名"""
        return cls.encrypt_aes(username)
    
    @classmethod
    def encrypt_password(cls, password: str) -> str:
        """加密密码"""
        return cls.encrypt_aes(password)
    
    @classmethod
    def generate_md5_sign(cls, *args) -> str:
        """
        生成MD5签名
        
        Args:
            *args: 需要签名的参数
            
        Returns:
            32位MD5签名
        """
        content = "".join(str(arg) for arg in args)
        return hashlib.md5(content.encode('utf-8')).hexdigest().upper()


if __name__ == "__main__":
    # 测试加密
    test_username = "13588888888"
    test_password = "123456"
    
    print(f"原始用户名: {test_username}")
    print(f"加密后: {ChaoxingCrypto.encrypt_username(test_username)}")
    print(f"原始密码: {test_password}")
    print(f"加密后: {ChaoxingCrypto.encrypt_password(test_password)}")
    
    # 测试MD5签名
    sign = ChaoxingCrypto.generate_md5_sign("param1", "param2", "param3")
    print(f"MD5签名: {sign}")
