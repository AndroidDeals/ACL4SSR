#!/usr/bin/env python3
"""
完全自动化的地理位置国家分组生成器
支持自动修改现有配置文件，添加缺失的国家分组
"""

import os
import re
import sys
import socket
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Optional, Tuple, List

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
    'MX': {'name': '墨西哥', 'emoji': '🇲🇽', 'patterns': ['墨', '墨西哥', 'MX', 'Mexico']},
    'TR': {'name': '土耳其', 'emoji': '🇹🇷', 'patterns': ['土', '土耳其', 'TR', 'Turkey']},
    'SE': {'name': '瑞典', 'emoji': '🇸🇪', 'patterns': ['瑞典', 'SE', 'Sweden', 'Stockholm']},
    'UA': {'name': '乌克兰', 'emoji': '🇺🇦', 'patterns': ['乌', '乌克兰', 'UA', 'Ukraine', 'Kyiv']},
    'CH': {'name': '瑞士', 'emoji': '🇨🇭', 'patterns': ['瑞士', 'CH', 'Switzerland']},
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
    'ZA': {'name': '南非', 'emoji': '🇿🇦', 'patterns': ['南', '南非', 'ZA', 'South Africa']},
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
    """三层识别机制"""
    
    def __init__(self):
        self.ip_to_country = self._load_baipiao()
        self.dns_cache = {}
        
    def _load_baipiao(self) -> Dict[str, str]:
        """加载 baipiao.txt"""
        ip_to_country = {}
        
        if not os.path.exists('baipiao.txt'):
            return ip_to_country
        
        try:
            with open('baipiao.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '#' not in line:
                        continue
                    
                    match = re.match(r'^([0-9.]+):\d+#([A-Z]{2})$', line)
                    if match:
                        ip = match.group(1)
                        country = match.group(2)
                        ip_to_country[ip] = country
        except:
            pass
        
        return ip_to_country
    
    def _is_valid_ip(self, hostname: str) -> bool:
        """检查是否为有效IP"""
        return bool(re.match(r'^[0-9.]+$', hostname))
    
    def _dns_resolve(self, hostname: str) -> Optional[str]:
        """DNS反查"""
        if hostname in self.dns_cache:
            return self.dns_cache[hostname]
        
        try:
            ip = socket.gethostbyname(hostname)
            self.dns_cache[hostname] = ip
            return ip
        except:
            self.dns_cache[hostname] = None
            return None
    
    def identify(self, proxy_name: str, proxy_server: str) -> Optional[Tuple[str, str]]:
        """综合识别: (country_code, method)"""
        
        # 优先级1：从节点名称提取国家代码
        match = re.search(r'\b([A-Z]{2})\b', proxy_name)
        if match:
            code = match.group(1)
            if code in COUNTRY_INFO:
                return (code, "代码提取")
        
        # 优先级2：中文国家名称
        for country_code, info in COUNTRY_INFO.items():
            for pattern in info['patterns']:
                if pattern in proxy_name:
                    return (country_code, "名称匹配")
        
        # 优先级3：通过IP查询
        ip = None
        if self._is_valid_ip(proxy_server):
            ip = proxy_server
        else:
            ip = self._dns_resolve(proxy_server)
        
        if ip and ip in self.ip_to_country:
            return (self.ip_to_country[ip], "IP查询")
        
        return None


# ============================================================================
# INI配置修改器
# ============================================================================

class INIConfigUpdater:
    """自动修改INI配置文件，添加缺失的国家分组"""
    
    def __init__(self):
        self.identifier = CountryIdentifier()
    
    def update_config_files(self) -> Dict[str, List[str]]:
        """更新所有INI配置文件"""
        config_dir = 'Clash/config'
        if not os.path.exists(config_dir):
            print(f"✗ 目录不存在: {config_dir}")
            return {}
        
        ini_files = list(Path(config_dir).glob('*.ini'))
        if not ini_files:
            print(f"✗ 未找到INI文件")
            return {}
        
        results = {}
        
        for ini_file in ini_files:
            print(f"\n📝 处理: {ini_file.name}")
            added_countries = self._update_ini_file(str(ini_file))
            results[ini_file.name] = added_countries
            print(f"  ✓ 添加了 {len(added_countries)} 个国家分组")
            
            for country_code in added_countries:
                info = COUNTRY_INFO.get(country_code, {})
                print(f"    - {info.get('emoji', '')} {country_code} ({info.get('name', '')})")
        
        return results
    
    def _update_ini_file(self, filepath: str) -> List[str]:
        """更新单个INI文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找出文件中已有的国家分组
        existing_groups = self._find_existing_groups(content)
        
        # 找出所有需要添加的国家
        detected_countries = self._find_referenced_countries(content)
        
        # 计算需要添加的国家
        new_countries = detected_countries - existing_groups
        
        if not new_countries:
            return []
        
        # 添加新的分组定义
        content = self._add_group_definitions(content, new_countries)
        
        # 添加到节点选择等关键分组
        content = self._add_to_select_groups(content, new_countries)
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return sorted(new_countries)
    
    def _find_existing_groups(self, content: str) -> Set[str]:
        """找出文件中已有的国家分组"""
        groups = set()
        
        # 查找 custom_proxy_group=🇨🇳 COUNTRY 节点 格式
        for country_code, info in COUNTRY_INFO.items():
            emoji = info['emoji']
            name = info['name']
            
            pattern = rf"custom_proxy_group={re.escape(emoji)}\s*{re.escape(name)}节点"
            if re.search(pattern, content):
                groups.add(country_code)
        
        return groups
    
    def _find_referenced_countries(self, content: str) -> Set[str]:
        """找出内容中提及的所有国家"""
        countries = set()
        
        # 查找所有 []🇭🇰 香港节点 类型的引用
        for country_code, info in COUNTRY_INFO.items():
            emoji = info['emoji']
            name = info['name']
            
            pattern = rf"\[\]{re.escape(emoji)}\s*{re.escape(name)}节点"
            if re.search(pattern, content):
                countries.add(country_code)
        
        return countries
    
    def _add_group_definitions(self, content: str, new_countries: Set[str]) -> str:
        """添加新的分组定义"""
        
        # 找到最后一个 custom_proxy_group 定义
        matches = list(re.finditer(r'^custom_proxy_group=.*$', content, re.MULTILINE))
        if not matches:
            return content
        
        last_match = matches[-1]
        insert_pos = last_match.end()
        
        new_lines = []
        for country_code in sorted(new_countries):
            info = COUNTRY_INFO[country_code]
            emoji = info['emoji']
            name = info['name']
            
            # 使用国家代码作为匹配模式
            group_name = f"{emoji} {name}节点"
            pattern = f"({country_code}|{emoji})"
            line = f"\ncustom_proxy_group={group_name}`url-test`{pattern}`http://www.gstatic.com/generate_204`300,,50"
            new_lines.append(line)
        
        return content[:insert_pos] + ''.join(new_lines) + content[insert_pos:]
    
    def _add_to_select_groups(self, content: str, new_countries: Set[str]) -> str:
        """将新国家添加到节点选择等分组中"""
        
        # 需要更新的分组关键词
        target_groups = [
            '🚀 节点选择',
            '♻️ 自动选择',
            '📲 电报消息',
            '🤖 OpenAi',
            '📹 油管视频',
            '🎥 奈飞视频',
            '🌍 国外媒体',
            '🐟 漏网之鱼',
            '📢 谷歌FCM',
        ]
        
        for country_code in new_countries:
            info = COUNTRY_INFO[country_code]
            emoji = info['emoji']
            name = info['name']
            group_name = f"{emoji} {name}节点"
            
            # 对每个目标分组添加新国家
            for target in target_groups:
                # 查找形如 custom_proxy_group=🚀 节点选择`select`...
                pattern = rf"(custom_proxy_group={re.escape(target)}`select`)(.*?)($|\n)"
                
                def replacer(match):
                    prefix = match.group(1)
                    content_part = match.group(2)
                    
                    # 检查是否已包含这个分��
                    if f"[]{group_name}" in content_part:
                        return match.group(0)
                    
                    # 在末尾添加新分组（保留DIRECT等特殊项）
                    # 如果包含DIRECT，添加到DIRECT之前
                    if '[]DIRECT' in content_part:
                        content_part = content_part.replace('[]DIRECT', f"[]{group_name}`[]DIRECT")
                    else:
                        content_part = content_part + f"`[]{group_name}"
                    
                    return prefix + content_part + match.group(3)
                
                content = re.sub(pattern, replacer, content, flags=re.MULTILINE)
        
        return content


# ============================================================================
# YAML配置修改器
# ============================================================================

class YAMLConfigUpdater:
    """自动修改YAML配置文件"""
    
    def update_yaml(self, countries: Set[str]) -> bool:
        """更新yaml/bdg.yaml"""
        yaml_path = 'yaml/bdg.yaml'
        
        if not os.path.exists(yaml_path):
            print(f"✗ 文件不存在: {yaml_path}")
            return False
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        existing = self._find_existing_yaml_groups(content)
        new_countries = countries - existing
        
        if not new_countries:
            print("  ✓ YAML文件已包含所有国家分组")
            return True
        
        print(f"\n🔧 更新YAML配置...")
        print(f"  添加 {len(new_countries)} 个国家:")
        
        # 在GLOBAL分组前插入新的分组定义
        for country_code in sorted(new_countries):
            info = COUNTRY_INFO[country_code]
            emoji = info['emoji']
            name = info['name']
            auto_name = f"{country_code} AUTO"
            icon_url = f"https://testingcf.jsdelivr.net/gh/Orz-3/mini@master/Color/{country_code}.png"
            
            new_group = f"""  - icon: {icon_url}
    include-all: true
    exclude-filter: (?i)GB|Traffic|Expire|Premium|频道|订阅|ISP|流量|到期|重置
    filter: ({country_code}|{emoji})
    name: {auto_name}
    type: url-test
    interval: 300

"""
            
            # 在GLOBAL分组前插入
            global_pattern = r"(\s*-\s*icon:[^\n]+Global\.png)"
            content = re.sub(global_pattern, new_group + r"\1", content, count=1)
            
            print(f"    - {emoji} {country_code} ({name})")
        
        # 也要添加到PROXY等分组的proxies列表中
        content = self._add_to_proxy_lists(content, new_countries)
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ 已更新 {yaml_path}")
        return True
    
    def _find_existing_yaml_groups(self, content: str) -> Set[str]:
        """查找YAML中已有的国家分组"""
        groups = set()
        
        for country_code in COUNTRY_INFO.keys():
            auto_name = f"{country_code} AUTO"
            if f"name: {auto_name}" in content:
                groups.add(country_code)
        
        return groups
    
    def _add_to_proxy_lists(self, content: str, new_countries: Set[str]) -> str:
        """添加到PROXY/Telegram/Google等分组的proxies列表"""
        
        for country_code in new_countries:
            auto_name = f"{country_code} AUTO"
            
            # 查找PROXY/Telegram/Google/GLOBAL等分组的proxies块
            patterns = ['PROXY', 'Telegram', 'Google', 'GLOBAL']
            
            for target in patterns:
                # 查找该分组的proxies列表
                pattern = rf"(name:\s*{target}\s*\n\s*type:\s*select\s*\n\s*proxies:\s*\n(?:\s*-\s*[^\n]+\n)+)"
                
                def replacer(match):
                    block = match.group(0)
                    if auto_name in block:
                        return block
                    
                    # 在最后一项前添加新分组
                    lines = block.splitlines(keepends=True)
                    if lines[-1].strip():
                        lines.append(f"      - {auto_name}\n")
                    else:
                        lines.insert(-1, f"      - {auto_name}\n")
                    
                    return ''.join(lines)
                
                content = re.sub(pattern, replacer, content, flags=re.MULTILINE)
        
        return content


# ============================================================================
# 主程序
# ============================================================================

def main():
    print("=" * 70)
    print("ACL4SSR - 完全自动化国家分组配置器")
    print("=" * 70)
    print()
    
    # 1. 更新INI配置
    print("[1/2] 更新INI配置文件...")
    ini_updater = INIConfigUpdater()
    ini_results = ini_updater.update_config_files()
    
    # ���集所有添加的国家
    all_countries = set()
    for countries in ini_results.values():
        all_countries.update(countries)
    
    if not ini_results:
        print("✗ 未找到INI配置文件")
    
    # 2. 更新YAML配置
    print("\n[2/2] 更新YAML配置文件...")
    yaml_updater = YAMLConfigUpdater()
    yaml_updater.update_yaml(all_countries)
    
    # 统计
    print("\n" + "=" * 70)
    print("✓ 完成！")
    print("=" * 70)
    print(f"总共添加了 {len(all_countries)} 个国家分组:")
    
    for country_code in sorted(all_countries):
        info = COUNTRY_INFO[country_code]
        print(f"  {info['emoji']} {country_code} ({info['name']})")
    
    if all_countries:
        print("\n✓ 配置已自动保存，重启Clash客户端后生效")
    else:
        print("\n ℹ️  未发现新的国家分组需要添加")


if __name__ == '__main__':
    main()
