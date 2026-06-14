#!/usr/bin/env python3
"""
学习强国 Cookie 失效测试脚本

使用方法:
1. 登录学习强国后，从浏览器获取 Cookie
2. 运行此脚本进行测试
   python test_cookie.py --cookie "your_cookie_here"
"""

import argparse
import time
import json
import requests
from datetime import datetime


class CookieTester:
    def __init__(self, cookie):
        self.cookie = cookie
        self.base_url = "https://pc-api.xuexi.cn"
        self.headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "y-open-ua": "TorchApp/1.0 OSType/Windows XueXi/1.0 Device/XXQGSpecialTopic",
            "y-open-did": "test_device_001",
            "gateway-channel": "inner_https",
            "Content-Type": "application/json",
        }
        self.results = []

    def check_auth(self):
        """检查登录状态"""
        try:
            response = requests.get(
                f"{self.base_url}/open/api/auth/check",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_cookie(self, interval=60, max_tests=100):
        """
        测试 Cookie 失效时间

        Args:
            interval: 测试间隔（秒）
            max_tests: 最大测试次数
        """
        print(f"开始测试 Cookie 失效时间...")
        print(f"测试间隔: {interval} 秒")
        print(f"最大测试次数: {max_tests}")
        print("-" * 50)

        start_time = datetime.now()

        for i in range(max_tests):
            current_time = datetime.now()
            elapsed = (current_time - start_time).total_seconds()

            result = self.check_auth()
            status = "有效" if result.get("ok") else "失效"

            log_entry = {
                "test_num": i + 1,
                "time": current_time.isoformat(),
                "elapsed_seconds": elapsed,
                "status": status,
                "response": result
            }
            self.results.append(log_entry)

            print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"测试 #{i+1} | 已过 {int(elapsed)} 秒 | 状态: {status}")

            # 如果 Cookie 失效，记录并退出
            if not result.get("ok"):
                print("-" * 50)
                print(f"Cookie 失效！")
                print(f"失效时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"有效时长: {int(elapsed)} 秒 ({int(elapsed/60)} 分钟)")
                break

            # 等待下一次测试
            if i < max_tests - 1:
                time.sleep(interval)

        return self.results

    def save_results(self, filename="cookie_test_results.json"):
        """保存测试结果"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"测试结果已保存到: {filename}")


def main():
    parser = argparse.ArgumentParser(description="学习强国 Cookie 失效测试")
    parser.add_argument("--cookie", required=True, help="登录后的 Cookie")
    parser.add_argument("--interval", type=int, default=60, help="测试间隔（秒），默认 60 秒")
    parser.add_argument("--max-tests", type=int, default=100, help="最大测试次数，默认 100 次")
    parser.add_argument("--output", default="cookie_test_results.json", help="输出文件名")

    args = parser.parse_args()

    tester = CookieTester(args.cookie)
    tester.test_cookie(interval=args.interval, max_tests=args.max_tests)
    tester.save_results(args.output)


if __name__ == "__main__":
    main()
