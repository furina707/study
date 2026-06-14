#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 VLESS 订阅链接并生成 Xray 负载均衡配置
"""

import base64
import json
import re
import sys
import subprocess
import urllib.parse
import requests

SUBSCRIBE_URL = "https://dash.pqjc.site/api/v1/pq/9471e9898ab4065a6e5f189e37ed5986"
OUTPUT_CONFIG = "xray_config.json"
LOCAL_SOCKS_PORT = 1080
LOCAL_HTTP_PORT = 8080

def parse_vless(url: str) -> dict:
    """解析 vless:// 链接"""
    # vless://uuid@host:port?params#name
    pattern = r"vless://([^@]+)@([^:]+):(\d+)\?(.+)#(.+)"
    match = re.match(pattern, url)
    if not match:
        return None
    
    uuid = match.group(1)
    address = match.group(2)
    port = int(match.group(3))
    params_str = match.group(4)
    name = urllib.parse.unquote(match.group(5))
    
    params = urllib.parse.parse_qs(params_str)
    
    return {
        "uuid": uuid,
        "address": address,
        "port": port,
        "type": params.get("type", ["tcp"])[0],
        "host": params.get("host", [address])[0],
        "path": urllib.parse.unquote(params.get("path", ["/"])[0]),
        "security": params.get("security", ["none"])[0],
        "sni": params.get("sni", [address])[0],
        "fp": params.get("fp", [""])[0],
        "pbk": params.get("pbk", [""])[0],  # REALITY public key
        "sid": params.get("sid", [""])[0],  # REALITY short ID
        "spx": urllib.parse.unquote(params.get("spx", ["/"])[0]),  # REALITY spiderX
        "flow": params.get("flow", [""])[0],  # flow control
        "name": name
    }

def generate_xray_config(nodes: list) -> dict:
    """生成 Xray 配置"""
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "port": LOCAL_SOCKS_PORT,
                "protocol": "socks",
                "settings": {"auth": "noauth", "udp": True},
                "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
            },
            {
                "port": LOCAL_HTTP_PORT,
                "protocol": "http",
                "settings": {"allowTransparent": True}
            }
        ],
        "outbounds": [],
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "balancers": [
                {
                    "tag": "balancer",
                    "selector": ["proxy-"],
                    "strategy": {"type": "roundRobin"}
                }
            ],
            "rules": [
                {
                    "type": "field",
                    "balancerTag": "balancer",
                    "domain": ["geosite:cn"]
                }
            ]
        }
    }
    
    # 添加直连出站
    config["outbounds"].append({
        "tag": "direct",
        "protocol": "freedom"
    })
    
    # 添加代理出站
    for i, node in enumerate(nodes):
        if not node:
            continue
        
        outbound = {
            "tag": f"proxy-{i}",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": node["address"],
                    "port": node["port"],
                    "users": [{"id": node["uuid"], "encryption": "none"}]
                }]
            },
            "streamSettings": {
                "network": node["type"],
                "security": node["security"]
            }
        }
        
        # WebSocket 设置
        if node["type"] == "ws":
            outbound["streamSettings"]["wsSettings"] = {
                "host": node["host"],
                "path": node["path"]
            }
        
        # TLS 设置
        if node["security"] == "tls":
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": node["sni"],
                "fingerprint": node["fp"] if node["fp"] else "chrome"
            }
        
        # REALITY 设置
        if node["security"] == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": node["sni"],
                "fingerprint": node["fp"] if node["fp"] else "chrome",
                "publicKey": node["pbk"],
                "shortId": node["sid"],
                "spiderX": node["spx"]
            }
            if node["flow"]:
                outbound["settings"]["vnext"][0]["users"][0]["flow"] = node["flow"]
        
        config["outbounds"].append(outbound)
    
    # 更新路由规则
    config["routing"]["rules"] = [
        {
            "type": "field",
            "balancerTag": "balancer",
            "network": "tcp,udp"
        }
    ]
    
    return config

def main():
    print(f"正在获取订阅: {SUBSCRIBE_URL}")
    
    # 使用 shell 命令解码 base64（更可靠）
    result = subprocess.run(
        ["curl", "-s", SUBSCRIBE_URL],
        capture_output=True,
        text=True
    )
    encoded = result.stdout.strip()
    
    result = subprocess.run(
        ["base64", "-d"],
        input=encoded,
        capture_output=True,
        text=True
    )
    content = result.stdout
    
    # 解析所有 vless 链接
    lines = content.strip().split("\n")
    nodes = []
    for line in lines:
        line = line.strip()
        if line.startswith("vless://"):
            node = parse_vless(line)
            if node:
                nodes.append(node)
    
    print(f"解析到 {len(nodes)} 个节点")
    
    # 生成配置
    config = generate_xray_config(nodes)
    
    # 保存配置
    with open(OUTPUT_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"配置已保存到: {OUTPUT_CONFIG}")
    print(f"本地 SOCKS5 代理: 127.0.0.1:{LOCAL_SOCKS_PORT}")
    print(f"本地 HTTP 代理: 127.0.0.1:{LOCAL_HTTP_PORT}")
    print(f"\n启动 Xray: xray run -c {OUTPUT_CONFIG}")

if __name__ == "__main__":
    main()
