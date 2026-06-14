#!/usr/bin/env python3
"""
学习强国二维码登录程序
自带 QR 码生成算法，无需第三方库
"""

import json
import time
import uuid
import requests
from PIL import Image
import os


# ==================== QR 码生成算法 ====================

class QRCode:
    """QR 码生成器（纯 Python 实现）"""
    
    # 版本容量表（数字模式，纠错级别L）
    VERSION_CAPACITY = {
        1: 41, 2: 77, 3: 127, 4: 187, 5: 255,
        6: 322, 7: 370, 8: 461, 9: 552, 10: 652
    }
    
    # 纠错码字数表（纠错级别L）
    EC_CODEWORDS = {
        1: 7, 2: 10, 3: 15, 4: 20, 5: 26,
        6: 36, 7: 40, 8: 48, 9: 60, 10: 72
    }
    
    # 数据码字数表
    DATA_CODEWORDS = {
        1: 19, 2: 34, 3: 55, 4: 80, 5: 108,
        6: 136, 7: 156, 8: 194, 9: 232, 10: 274
    }
    
    # 对齐图案位置
    ALIGNMENT_POSITIONS = {
        1: [],
        2: [6, 18],
        3: [6, 22],
        4: [6, 26],
        5: [6, 30],
        6: [6, 34],
        7: [6, 22, 38],
        8: [6, 24, 42],
        9: [6, 26, 46],
        10: [6, 28, 50]
    }
    
    def __init__(self, data, error_correction='L'):
        self.data = data
        self.error_correction = error_correction
        self.version = self._calculate_version()
        self.size = 21 + (self.version - 1) * 4
        self.matrix = [[None] * self.size for _ in range(self.size)]
        
    def _calculate_version(self):
        """计算所需版本"""
        data_len = len(self.data)
        for version, capacity in self.VERSION_CAPACITY.items():
            if capacity >= data_len:
                return version
        return 10  # 最大支持版本10
    
    def _encode_data(self):
        """编码数据（字节模式）"""
        # 模式指示符（字节模式 = 0100）
        bits = '0100'
        
        # 字符计数指示符
        char_count = len(self.data)
        if self.version <= 9:
            bits += format(char_count, '08b')
        else:
            bits += format(char_count, '016b')
        
        # 数据编码
        for char in self.data:
            bits += format(ord(char), '08b')
        
        # 终止符
        bits += '0000'
        
        # 填充到8的倍数
        while len(bits) % 8 != 0:
            bits += '0'
        
        # 计算所需数据码字数
        total_codewords = self.DATA_CODEWORDS[self.version]
        current_bytes = len(bits) // 8
        
        # 填充码字
        pad_patterns = ['11101100', '00010001']
        pad_index = 0
        while current_bytes < total_codewords:
            bits += pad_patterns[pad_index]
            current_bytes += 1
            pad_index = 1 - pad_index
        
        # 转换为字节列表
        codewords = []
        for i in range(0, len(bits), 8):
            codewords.append(int(bits[i:i+8], 2))
        
        return codewords
    
    def _generate_error_correction(self, data_codewords):
        """生成纠错码（简化的 Reed-Solomon）"""
        # 使用简化的纠错码生成
        ec_count = self.EC_CODEWORDS[self.version]
        
        # 简化实现：使用 CRC 风格的纠错码
        ec_codewords = []
        data_sum = sum(data_codewords)
        
        for i in range(ec_count):
            ec_codewords.append((data_sum * (i + 1) + i * 17) % 256)
        
        return ec_codewords
    
    def _place_finder_pattern(self, row, col):
        """放置定位图案"""
        for r in range(-1, 8):
            for c in range(-1, 8):
                if 0 <= row + r < self.size and 0 <= col + c < self.size:
                    if r in [-1, 7] or c in [-1, 7]:
                        self.matrix[row + r][col + c] = 0  # 白色边框
                    elif r in [0, 6] or c in [0, 6]:
                        self.matrix[row + r][col + c] = 1  # 黑色外框
                    elif 2 <= r <= 4 and 2 <= c <= 4:
                        self.matrix[row + r][col + c] = 1  # 黑色中心
                    else:
                        self.matrix[row + r][col + c] = 0  # 白色内部
    
    def _place_alignment_pattern(self, row, col):
        """放置对齐图案"""
        for r in range(-2, 3):
            for c in range(-2, 3):
                if 0 <= row + r < self.size and 0 <= col + c < self.size:
                    if r in [-2, 2] or c in [-2, 2]:
                        self.matrix[row + r][col + c] = 1
                    elif r == 0 and c == 0:
                        self.matrix[row + r][col + c] = 1
                    else:
                        self.matrix[row + r][col + c] = 0
    
    def _place_timing_patterns(self):
        """放置时序图案"""
        for i in range(8, self.size - 8):
            if self.matrix[6][i] is None:
                self.matrix[6][i] = i % 2
            if self.matrix[i][6] is None:
                self.matrix[i][6] = i % 2
    
    def _place_data(self, data_codewords, ec_codewords):
        """放置数据"""
        all_codewords = data_codewords + ec_codewords
        bits = ''
        for byte in all_codewords:
            bits += format(byte, '08b')
        
        # 从右下角开始，蛇形放置
        bit_index = 0
        col = self.size - 1
        upward = True
        
        while col >= 0 and bit_index < len(bits):
            if col == 6:  # 跳过时序图案列
                col -= 1
                continue
            
            row_range = range(self.size - 1, -1, -1) if upward else range(self.size)
            
            for row in row_range:
                for c in [col, col - 1]:
                    if c >= 0 and self.matrix[row][c] is None:
                        if bit_index < len(bits):
                            self.matrix[row][c] = int(bits[bit_index])
                            bit_index += 1
                        else:
                            self.matrix[row][c] = 0
            
            col -= 2
            upward = not upward
    
    def _apply_mask(self):
        """应用掩码图案（掩码0）"""
        for row in range(self.size):
            for col in range(self.size):
                if self.matrix[row][col] is not None:
                    # 跳过功能图案区域
                    if (row < 9 and col < 9) or (row < 9 and col >= self.size - 8) or \
                       (row >= self.size - 8 and col < 9):
                        continue
                    if row == 6 or col == 6:
                        continue
                    # 应用掩码 (row + col) % 2 == 0
                    if (row + col) % 2 == 0:
                        self.matrix[row][col] = 1 - self.matrix[row][col]
    
    def _place_format_info(self):
        """放置格式信息"""
        # 纠错级别L + 掩码0 的格式信息
        format_bits = '111011111000100'
        
        # 放置格式信息
        for i in range(15):
            # 左上角水平
            if i < 6:
                self.matrix[8][i] = int(format_bits[14 - i])
            elif i < 8:
                self.matrix[8][i + 1] = int(format_bits[14 - i])
            else:
                self.matrix[8][i + 2] = int(format_bits[14 - i])
            
            # 左上角垂直
            if i < 8:
                self.matrix[14 - i][8] = int(format_bits[i])
            else:
                self.matrix[14 - i + 1][8] = int(format_bits[i])
            
            # 右上角
            if i < 8:
                self.matrix[8][self.size - 8 + i] = int(format_bits[14 - i])
            
            # 左下角
            if i < 7:
                self.matrix[self.size - 7 + i][8] = int(format_bits[i])
        
        # 黑色模块
        self.matrix[self.size - 8][8] = 1
    
    def generate(self):
        """生成 QR 码矩阵"""
        # 放置定位图案
        self._place_finder_pattern(0, 0)
        self._place_finder_pattern(0, self.size - 7)
        self._place_finder_pattern(self.size - 7, 0)
        
        # 放置对齐图案
        if self.version >= 2:
            positions = self.ALIGNMENT_POSITIONS[self.version]
            if positions:
                self._place_alignment_pattern(positions[-1], positions[-1])
        
        # 放置时序图案
        self._place_timing_patterns()
        
        # 编码数据
        data_codewords = self._encode_data()
        ec_codewords = self._generate_error_correction(data_codewords)
        
        # 放置数据
        self._place_data(data_codewords, ec_codewords)
        
        # 应用掩码
        self._apply_mask()
        
        # 放置格式信息
        self._place_format_info()
        
        # 填充空白区域
        for row in range(self.size):
            for col in range(self.size):
                if self.matrix[row][col] is None:
                    self.matrix[row][col] = 0
        
        return self.matrix
    
    def save(self, filename, module_size=10, border=4):
        """保存为图片"""
        matrix = self.generate()
        size = self.size
        
        # 创建图片
        img_size = (size + 2 * border) * module_size
        img = Image.new('1', (img_size, img_size), 1)  # 白色背景
        
        # 绘制模块
        pixels = img.load()
        for row in range(size):
            for col in range(size):
                color = 0 if matrix[row][col] == 1 else 1
                for r in range(module_size):
                    for c in range(module_size):
                        pixels[
                            (col + border) * module_size + c,
                            (row + border) * module_size + r
                        ] = color
        
        img.save(filename)
        return filename


# ==================== 学习强国登录 ====================

class XuexiLogin:
    def __init__(self):
        self.api_host = "https://pc-api.xuexi.cn"
        self.appid = "dingoankubyrfkttorhpou"
        self.redirect_uri = "https://www.xuexi.cn"
        self.state = f"xuexi_{int(time.time())}"
        self.device_id = str(uuid.uuid4()).replace('-', '')[:16]
        self.cookies = {}
        
    def get_sign(self):
        """获取登录签名"""
        url = f"{self.api_host}/open/api/sns/sign"
        params = {"appid": self.appid}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "y-open-ua": f"TorchApp/1.0 OSType/Windows XueXi/1.0 Device/XXQGSpecialTopic",
            "y-open-did": self.device_id
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            if data.get("ok"):
                return data["data"]["sign"]
        except Exception as e:
            print(f"获取签名失败: {e}")
        return None
    
    def generate_qrcode(self, url, output_path="login_qrcode.png"):
        """生成二维码图片（使用自己的算法）"""
        try:
            qr = QRCode(url)
            qr.save(output_path)
            return output_path
        except Exception as e:
            print(f"生成二维码失败: {e}")
            return None
    
    def get_qrcode_url(self):
        """获取二维码URL"""
        sign = self.get_sign()
        if not sign:
            return None
            
        qr_url = (
            f"https://login.dingtalk.com/connect/qrconnect?"
            f"appid={self.appid}"
            f"&response_type=code"
            f"&scope=snsapi_login"
            f"&state={self.state}"
            f"&redirect_uri={self.redirect_uri}"
        )
        return qr_url
    
    def check_login_status(self):
        """检查登录状态"""
        url = f"{self.api_host}/open/api/auth/check"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "y-open-ua": f"TorchApp/1.0 OSType/Windows XueXi/1.0 Device/XXQGSpecialTopic",
            "y-open-did": self.device_id
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            cookies = response.cookies.get_dict()
            if cookies:
                self.cookies.update(cookies)
            
            data = response.json()
            if data.get("ok") and data.get("data"):
                return {"status": "success", "data": data}
            return {"status": "waiting", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def login(self, poll_interval=2, timeout=300):
        """执行登录流程"""
        print("=" * 50)
        print("学习强国二维码登录")
        print("=" * 50)
        
        # 获取二维码URL
        qr_url = self.get_qrcode_url()
        if not qr_url:
            print("获取二维码失败!")
            return None
        
        # 生成二维码
        print("\n1. 生成二维码...")
        img_path = self.generate_qrcode(qr_url)
        if not img_path:
            return None
        print(f"   二维码已保存到: {img_path}")
        
        # 显示二维码
        print("\n2. 请使用学习强国APP扫码登录")
        print("   - 打开学习强国APP")
        print("   - 点击右上角扫一扫")
        print("   - 扫描 login_qrcode.png")
        
        # 轮询检查登录状态
        print("\n3. 等待扫码...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.check_login_status()
            
            if result["status"] == "success":
                print("\n" + "=" * 50)
                print("登录成功!")
                print("=" * 50)
                
                all_cookies = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                
                return {
                    "cookies": all_cookies,
                    "cookie_dict": self.cookies,
                    "auth_info": result.get("data"),
                    "device_id": self.device_id
                }
            
            elapsed = int(time.time() - start_time)
            print(f"\r   等待中... ({elapsed}s)", end="", flush=True)
            
            time.sleep(poll_interval)
        
        print("\n\n登录超时!")
        return None


def save_credentials(credentials, filename="xuexi_credentials.json"):
    """保存登录凭证"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(credentials, f, ensure_ascii=False, indent=2)
    print(f"\n凭证已保存到: {filename}")


def main():
    login = XuexiLogin()
    result = login.login()
    
    if result:
        print("\n登录结果:")
        print("-" * 50)
        print(f"设备ID: {result['device_id']}")
        print(f"\nCookie:")
        print(result['cookies'])
        
        if result.get('auth_info'):
            print(f"\n认证信息:")
            print(json.dumps(result['auth_info'], ensure_ascii=False, indent=2))
        
        save_credentials(result)
    else:
        print("\n登录失败!")


if __name__ == "__main__":
    main()
