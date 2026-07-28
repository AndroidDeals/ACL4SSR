#!/usr/bin/env python3
"""
高级地理位置国家分组生成器
支持IP直接识别、域名DNS反查、节点备注国家代码三层识别机制
"""

import os
import re
import sys
import json
import socket
import gzip
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Optional, Tuple

# ============================================================================
# 国家信息映射表
# ============================================================================
COUNTRY_INFO = {
    'HK': {'name': '香港', 'emoji': '🇭🇰', 'patterns': ['港', 'HK', 'Hong Kong', 'HongKong']},
    'US': {'name': '美国', 'emoji': '🇺🇲', 'patterns': ['美', '美国', 'US', 'United States', 'USA']},
    'JP': {'name': '日本', 'emoji': '🇯🇵', 'patterns': ['日本', '日', 'JP', 'Japan', 'Tokyo', 'Osaka']},
    'SG': {'name': '狮城', 'emoji': '🇸🇬', 'patterns': ['新加坡', '狮城', 'SG', 'Singapore']},
    'TW': {'name': '台湾', 'emoji': '🇹🇼', 'patterns': ['台', '台湾', 'TW', 'Taiwan']},
    'KR': {'name': '韩国', 'emoji': '🇰🇷', 'patterns': ['韩', '韓', 'KR', 'Korea', 'Seoul']},
    'DE': {'name': '德国', 'emoji': '🇩🇪', 'patterns': ['德', '德国', 'DE', 'Germany', 'Frankfurt']},
    'GB': {'name': '英国', 'emoji': '🇬🇧', 'patterns': ['英', '英国', 'GB', 'UK', 'United Kingdom', 'London']},
    'NL': {'name': '荷兰', 'emoji': '🇳🇱', 'patterns': ['荷', '荷兰', 'NL', 'Netherlands', 'Amsterdam']},
    'FR': {'name': '法国', 'emoji': '🇫🇷', 'patterns': ['法', '法国', 'FR', 'France', 'Paris']},
    'CA': {'name': '加拿大', 'emoji': '🇨🇦', 'patterns': ['加', '加拿大', 'CA', 'Canada']},
    'AU': {'name': '澳大利亚', 'emoji': '🇦🇺', 'patterns': ['澳', '澳大利亚', 'AU', 'Australia', 'Sydney']},
    'RU': {'name': '俄罗斯', 'emoji': '🇷🇺', 'patterns': ['俄', '俄罗斯', 'RU', 'Russia', 'Moscow']},
    'BR': {'name': '巴西', 'emoji': '🇧🇷', 'patterns': ['巴', '巴西', 'BR', 'Brazil']},
    'IN': {'name': '印度', 'emoji': '🇮🇳', 'patterns': ['印', '印度', 'IN', 'India']},
    'MX': {'name': '墨西哥', 'emoji': '🇲🇽', 'patterns': ['墨', '��西哥', 'MX', 'Mexico']},
    'TR': {'name': '土耳其', 'emoji': '🇹🇷', 'patterns': ['土', '土耳其', 'TR', 'Turkey']},
    'SE': {'name': '瑞典', 'emoji': '🇸🇪', 'patterns': ['瑞', '瑞典', 'SE', 'Sweden', 'Stockholm']},
    'UA': {'name': '乌克兰', 'emoji': '🇺🇦', 'patterns': ['乌', '乌克兰', 'UA', 'Ukraine', 'Kyiv']},
    'CH': {'name': '瑞士', 'emoji': '🇨🇭', 'patterns': ['瑞', '瑞士', 'CH', 'Switzerland']},
    'IT': {'name': '意大利', 'emoji': '🇮🇹', 'patterns': ['意', '意大利', 'IT', 'Italy', 'Milan']},
    'ES': {'name': '西班牙', 'emoji': '🇪🇸', 'patterns': ['西', '西班牙', 'ES', 'Spain', 'Madrid']},
    'CZ': {'name': '捷克', 'emoji': '🇨🇿', 'patterns': ['捷', '捷克', 'CZ', 'Czech']},
    'PL': {'name': '波兰', 'emoji': '🇵🇱', 'patterns': ['波', '波兰', 'PL', 'Poland', 'Warsaw']},
    'RO': {'name': '罗马尼亚', 'emoji': '🇷🇴', 'patterns': ['罗', '罗马尼亚', 'RO', 'Romania']},
    'HU': {'name': '匈牙利', 'emoji': '🇭🇺', 'patterns': ['匈', '匈牙利', 'HU', 'Hungary', 'Budapest']},
    'AT': {'name': '奥地利', 'emoji': '🇦🇹', 'patterns': ['奥', '奥地利', 'AT', 'Austria', 'Vienna']},
    'BG': {'name': '保加利亚', 'emoji': '🇧🇬', 'patterns': ['保', '保加利亚', 'BG', 'Bulgaria', 'Sofia']},
    'GR': {'name': '希腊', 'emoji': '🇬🇷', 'patterns': ['希', '希腊', 'GR', 'Greece', 'Athens']},
    'IE': {'name': '爱尔兰', 'emoji': '🇮🇪', 'patterns': ['爱', '爱尔兰', 'IE', 'Ireland', 'Dublin']},
    'IL': {'name': '以色列', 'emoji': '🇮🇱', 'patterns': ['以', '以色列', 'IL', 'Israel', 'Tel Aviv']},
    'AE': {'name': '阿联酋', 'emoji': '🇦🇪', 'patterns': ['阿', '阿联酋', 'AE', 'UAE', 'Dubai']},
    'SA': {'name': '沙特阿拉伯', 'emoji': '🇸🇦', 'patterns': ['沙', '沙特', 'SA', 'Saudi']},
    'PH': {'name': '菲律宾', 'emoji': '🇵🇭', 'patterns': ['菲', '菲律宾', 'PH', 'Philippines', 'Manila']},
    'TH': {'name': '泰国', 'emoji': '🇹🇭', 'patterns': ['泰', '泰国', 'TH', 'Thailand', 'Bangkok']},
    'MY': {'name': '马来西亚', 'emoji': '🇲🇾', 'patterns': ['马', '马来西亚', 'MY', 'Malaysia', 'Kuala']},
    'VN': {'name': '越南', 'emoji': '🇻🇳', 'patterns': ['越', '越南', 'VN', 'Vietnam', 'Hanoi']},
    'ID': {'name': '印度尼西亚', 'emoji': '🇮🇩', 'patterns': ['印', '印度尼西亚', 'ID', 'Indonesia', 'Jakarta']},
    'KZ': {'name': '哈萨克斯坦', 'emoji': '🇰🇿', 'patterns': ['哈', '哈萨克', 'KZ', 'Kazakhstan']},
    'ZA': {'name': '��非', 'emoji': '🇿🇦', 'patterns': ['南', '南非', 'ZA', 'South Africa']},
    'NZ': {'name': '新西兰', 'emoji': '🇳🇿', 'patterns': ['新西', '新西兰', 'NZ', 'New Zealand']},
    'CL': {'name': '智利', 'emoji': '🇨🇱', 'patterns': ['智', '智利', 'CL', 'Chile']},
    'AR': {'name': '阿根廷', 'emoji': '🇦🇷', 'patterns': ['阿', '阿根廷', 'AR', 'Argentina']},
    'LV': {'name': '拉脱维亚', 'emoji': '🇱🇻', 'patterns': ['拉', '拉脱维亚', 'LV', 'Latvia']},
    'LT': {'name': '立陶宛', 'emoji': '🇱🇹', 'patterns': ['立', '立陶宛', 'LT', 'Lithuania']},
    'EE': {'name': '爱沙尼亚', 'emoji': '🇪🇪', 'patterns': ['爱', '爱沙尼亚', 'EE', 'Estonia']},
    'DK': {'name': '丹麦', 'emoji': '🇩🇰', 'patterns': ['丹', '丹麦', 'DK', 'Denmark']},
    'BE': {'name': '比利时', 'emoji': '🇧🇪', 'patterns': ['比', '比利时', 'BE', 'Belgium']},
    'PT': {'name': '葡萄牙', 'emoji': '🇵🇹', 'patterns': ['葡', '葡萄牙', 'PT', 'Portugal']},
    'IS': {'name': '冰岛', 'emoji': '🇮🇸', 'patterns': ['冰', '冰岛', 'IS', 'Iceland']},
    'LU': {'name': '卢森堡', 'emoji': '🇱🇺', 'patterns': ['卢', '卢森堡', 'LU', 'Luxembourg']},
    'MT': {'name': '马耳他', 'emoji': '🇲🇹', 'patterns': ['马', '马耳他', 'MT', 'Malta']},
    'CY': {'name': '塞浦路斯', 'emoji': '🇨🇾', 'patterns': ['塞', '塞浦路斯', 'CY', 'Cyprus']},
    'MO': {'name': '澳门', 'emoji': '🇲🇴', 'patterns': ['澳', '澳门', 'MO', 'Macau']},
    'MN': {'name': '蒙古', 'emoji': '🇲🇳', 'patterns': ['蒙', '蒙古', 'MN', 'Mongolia']},
    'FI': {'name': '芬兰', 'emoji': '🇫🇮', 'patterns': ['芬', '芬兰', 'FI', 'Finland', 'Helsinki']},
    'NO': {'name': '挪威', 'emoji': '🇳🇴', 'patterns': ['挪', '挪威', 'NO', 'Norway', 'Oslo']},
    'SK': {'name': '斯洛伐克', 'emoji': '🇸🇰', 'patterns': ['斯', '斯洛伐克', 'SK', 'Slovakia']},
}

# ============================================================================
# 核心识别引擎
# ============================================================================

class CountryIdentifier:
    """三层识别机制：国家代码 > DNS反查 > 节点备注"""
    
    def __init__(self):
        self.ip_to_country = self._load_baipiao()
        self.dns_cache = {}
        
    def _load_baipiao(self) -> Dict[str, str]:
        """加载 baipiao.txt 的IP地理位置数据"""
        ip_to_country = {}
        
        if not os.path.exists('baipiao.txt'):
            print("⚠️  baipiao.txt 不存在���跳过IP预置数据加载")
            return ip_to_country
        
        try:
            with open('baipiao.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '#' not in line:
                        continue
                    
                    # 格式: IP:PORT#COUNTRY
                    match = re.match(r'^([0-9.]+):\d+#([A-Z]{2})$', line)
                    if match:
                        ip = match.group(1)
                        country = match.group(2)
                        ip_to_country[ip] = country
            
            print(f"✓ 已加载 {len(ip_to_country)} 个IP地理位置映射")
        except Exception as e:
            print(f"✗ 读取 baipiao.txt 失败: {e}")
        
        return ip_to_country
    
    def _is_valid_ip(self, hostname: str) -> bool:
        """检查是否为有效的IP地址"""
        return bool(re.match(r'^[0-9.]+$', hostname))
    
    def _dns_resolve(self, hostname: str) -> Optional[str]:
        """DNS反查：域名 -> IP"""
        if hostname in self.dns_cache:
            return self.dns_cache[hostname]
        
        try:
            ip = socket.gethostbyname(hostname)
            self.dns_cache[hostname] = ip
            return ip
        except:
            self.dns_cache[hostname] = None
            return None
    
    def identify_by_code(self, proxy_name: str) -> Optional[str]:
        """
        方法1：从节点备注提取国家代码
        示例: "UN UA" -> "UA" -> 乌克兰
        """
        # 匹配两个字母的国家代码
        match = re.search(r'\b([A-Z]{2})\b', proxy_name)
        if match:
            code = match.group(1)
            if code in COUNTRY_INFO:
                return code
        
        # 匹配中文国家名称
        for country_code, info in COUNTRY_INFO.items():
            for pattern in info['patterns']:
                if pattern in proxy_name:
                    return country_code
        
        return None
    
    def identify_by_ip(self, hostname: str) -> Optional[str]:
        """
        方法2：通过IP查询国家
        - 直接IP: 在 baipiao.txt 中查询
        - 域名: 先DNS反查再查询
        """
        ip = None
        
        # 如果是IP地址，直接查询
        if self._is_valid_ip(hostname):
            ip = hostname
        else:
            # ���果是域名，先DNS反查
            ip = self._dns_resolve(hostname)
            if not ip:
                return None
        
        # 在baipiao.txt中查询
        return self.ip_to_country.get(ip)
    
    def identify(self, proxy_name: str, proxy_server: str) -> Optional[Tuple[str, str]]:
        """
        综合识别：返回 (country_code, method)
        优先级：国家代码 > IP查询 > 节点名称匹配
        """
        # 优先级1：从节点名称提取国家代码
        code = self.identify_by_code(proxy_name)
        if code:
            return (code, "代码提取")
        
        # 优先级2：通过IP/域名查询地理位置
        code = self.identify_by_ip(proxy_server)
        if code:
            return (code, "IP查询")
        
        # 优先级3：模糊匹配节点名称中的地区关键词
        code = self.identify_by_code(proxy_name)  # 更宽泛的匹配
        if code:
            return (code, "名称匹配")
        
        return None


# ============================================================================
# 配置生成器
# ============================================================================

class ConfigGenerator:
    """生成INI和YAML格式的配置"""
    
    @staticmethod
    def generate_ini_line(country_code: str, ip_list: Set[str] = None) -> str:
        """生成单行INI配置"""
        if country_code not in COUNTRY_INFO:
            return ""
        
        info = COUNTRY_INFO[country_code]
        name = info['name']
        emoji = info['emoji']
        
        # 如果有IP列表，使用IP匹配；否则使用国家代码匹配
        if ip_list:
            pattern = '|'.join(list(ip_list)[:100])  # 限制IP数量
        else:
            pattern = f"({country_code}|{info['emoji']})"
        
        group_name = f"{emoji} {name}节点"
        return f"custom_proxy_group={group_name}`url-test`{pattern}`http://www.gstatic.com/generate_204`300,,50"
    
    @staticmethod
    def generate_yaml_line(country_code: str) -> str:
        """生成单条YAML配置"""
        if country_code not in COUNTRY_INFO:
            return ""
        
        info = COUNTRY_INFO[country_code]
        name = info['name']
        emoji = info['emoji']
        auto_name = f"{country_code} AUTO"
        icon_url = f"https://testingcf.jsdelivr.net/gh/Orz-3/mini@master/Color/{country_code}.png"
        
        return f"""  - icon: {icon_url}
    include-all: true
    exclude-filter: (?i)GB|Traffic|Expire|Premium|频道|订阅|ISP|流量|到期|重置
    filter: ({country_code}|{emoji})
    name: {auto_name}
    type: url-test
    interval: 300
"""


# ============================================================================
# 主程序
# ============================================================================

def main():
    print("=" * 70)
    print("ACL4SSR - 地理位置国家分组生成器 (高级版)")
    print("=" * 70)
    print("识别机制: 国家代码 > IP查询 > 节点名称匹配")
    print()
    
    # 初始化识别引擎
    identifier = CountryIdentifier()
    
    # 统计识别结果
    country_stats = defaultdict(lambda: {'count': 0, 'methods': defaultdict(int)})
    
    # 尝试从Clash配置文件读取节点
    print("[1/3] 扫描代理节点...")
    proxies = _scan_proxies()
    
    if proxies:
        print(f"✓ 发现 {len(proxies)} 个节点\n")
        
        # 识别每个节点的国家
        for proxy_name, proxy_server in proxies:
            result = identifier.identify(proxy_name, proxy_server)
            
            if result:
                country_code, method = result
                country_stats[country_code]['count'] += 1
                country_stats[country_code]['methods'][method] += 1
                print(f"  ✓ {proxy_name:30s} → {country_code} ({method})")
            else:
                print(f"  ✗ {proxy_name:30s} → 未识别")
    else:
        print("⚠️  未找到代理节点配置，仅使用预置数据\n")
    
    # 生成配置
    print("\n[2/3] 生成INI配置...")
    _generate_ini_config(country_stats if proxies else None)
    
    print("[3/3] 生成YAML配置...")
    _generate_yaml_config(country_stats if proxies else None)
    
    # 统计信息
    print("\n" + "=" * 70)
    print("统计信息")
    print("=" * 70)
    
    for country_code in sorted(country_stats.keys()):
        if country_code in COUNTRY_INFO:
            info = COUNTRY_INFO[country_code]
            stats = country_stats[country_code]
            methods = ", ".join([f"{m}({c})" for m, c in stats['methods'].items()])
            print(f"{info['emoji']} {country_code} ({info['name']:15s}): {stats['count']:3d}个 [{methods}]")
    
    print("\n✓ 生成完成！")
    print("  - generated_groups.ini")
    print("  - generated_groups.yaml")


def _scan_proxies() -> list:
    """从Clash配置扫描代理节点"""
    proxies = []
    
    config_paths = [
        'config.yaml',
        'clash_config.yaml',
        'Clash/config/config.yaml'
    ]
    
    for path in config_paths:
        if not os.path.exists(path):
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的YAML解析（查找proxies块）
            if 'proxies:' in content:
                lines = content.split('\n')
                in_proxies = False
                current_proxy = {}
                
                for line in lines:
                    if line.strip() == 'proxies:':
                        in_proxies = True
                        continue
                    
                    if in_proxies:
                        if line.startswith('  - '):
                            if current_proxy:
                                proxies.append(current_proxy)
                            current_proxy = {}
                        elif line.startswith('    name:'):
                            current_proxy['name'] = line.split(':', 1)[1].strip()
                        elif line.startswith('    server:'):
                            current_proxy['server'] = line.split(':', 1)[1].strip()
                            if 'name' in current_proxy:
                                proxies.append((current_proxy['name'], current_proxy['server']))
                        elif not line.startswith('    '):
                            in_proxies = False
            
            break
        except Exception as e:
            continue
    
    return proxies


def _generate_ini_config(country_stats=None):
    """生成INI格式配置"""
    lines = ["; 自动生成的国家分组配置"]
    lines.append("; 基于IP地理位置、域名DNS反查、节点备注识别")
    lines.append("")
    
    countries = sorted(country_stats.keys()) if country_stats else sorted(COUNTRY_INFO.keys())
    
    for country_code in countries:
        if country_code not in COUNTRY_INFO:
            continue
        line = ConfigGenerator.generate_ini_line(country_code)
        if line:
            lines.append(line)
    
    with open('generated_groups.ini', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✓ 已生成: generated_groups.ini")


def _generate_yaml_config(country_stats=None):
    """生成YAML格式配置"""
    lines = ["# 自动生成的国家分组配置", "# 基于IP地理位置、域名DNS反查、节点备注识别", "proxy-groups:", ""]
    
    countries = sorted(country_stats.keys()) if country_stats else sorted(COUNTRY_INFO.keys())
    
    for country_code in countries:
        if country_code not in COUNTRY_INFO:
            continue
        line = ConfigGenerator.generate_yaml_line(country_code)
        if line:
            lines.append(line)
    
    with open('generated_groups.yaml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✓ 已生成: generated_groups.yaml")


if __name__ == '__main__':
    main()
