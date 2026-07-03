#!/usr/bin/env python3
import os
import sys
import re

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 add_custom_country.py <Group_Name> <Regex_Pattern>")
        print("Example: python3 add_custom_country.py \"🇳🇱 荷兰节点\" \"(荷兰|Netherlands|Amsterdam)\"")
        sys.exit(1)
        
    group_name = sys.argv[1]
    regex_pattern = sys.argv[2]
    
    # 1. Update all .ini files in Clash/config/
    config_dir = "Clash/config"
    if not os.path.exists(config_dir):
        print(f"Error: Directory {config_dir} not found. Please run this script from the root of the ACL4SSR repo.")
        sys.exit(1)
        
    files = [f for f in os.listdir(config_dir) if f.endswith(".ini")]
    
    for filename in files:
        filepath = os.path.join(config_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Add to select & url-test groups
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("custom_proxy_group="):
                parts = line.split("`")
                g_name = parts[0].replace("custom_proxy_group=", "")
                
                contains_country_markers = any(f"[]{r}" in line for r in ["🇭🇰 香港节点", "🇺🇲 美国节点", "🇯🇵 日本节点"])
                is_domestic_media = "国内媒体" in g_name
                
                if contains_country_markers and not is_domestic_media:
                    # Find insertion point
                    insertion_idx = -1
                    for idx, opt in enumerate(parts):
                        if opt.startswith("[]") and any(x in opt for x in ["节点", "节点"]):
                            insertion_idx = max(insertion_idx, idx)
                            
                    if insertion_idx != -1 and f"[]{group_name}" not in parts:
                        parts = parts[:insertion_idx + 1] + [f"[]{group_name}"] + parts[insertion_idx + 1:]
                        line = "`".join(parts)
                        print(f"[{filename}] Added {group_name} to select group: {g_name}")
            new_lines.append(line)
        content = "\n".join(new_lines)
        
        # Add group definition
        def_pattern = f"^custom_proxy_group={group_name}`url-test`.*$"
        if not re.search(def_pattern, content, re.MULTILINE):
            sibling_found = False
            for sibling in ["🇯🇵 日本节点", "🇺🇲 美国节点", "🇭🇰 香港节点", "🇩🇪 德国节点"]:
                sibling_pattern = rf"^(custom_proxy_group={sibling}`url-test`.*)$"
                match = re.search(sibling_pattern, content, re.MULTILINE)
                if match:
                    sibling_line = match.group(1)
                    new_def = f"custom_proxy_group={group_name}`url-test`{regex_pattern}`http://www.gstatic.com/generate_204`300,,50"
                    content = content.replace(sibling_line, f"{sibling_line}\n{new_def}")
                    print(f"[{filename}] Defined group: {group_name}")
                    sibling_found = True
                    break
            if not sibling_found:
                matches = list(re.finditer(r"^custom_proxy_group=.*$", content, re.MULTILINE))
                if matches:
                    last_match = matches[-1]
                    new_def = f"custom_proxy_group={group_name}`url-test`{regex_pattern}`http://www.gstatic.com/generate_204`300,,50"
                    content = content[:last_match.end()] + f"\n{new_def}" + content[last_match.end():]
                    print(f"[{filename}] Appended group: {group_name}")
                    
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. Update yaml/bdg.yaml if it exists
    yaml_path = "yaml/bdg.yaml"
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()
            
        # Parse short code for YAML flag (e.g. DE, NL, TW)
        short_code_match = re.search(r"([A-Z]{2})", regex_pattern)
        short_code = short_code_match.group(1) if short_code_match else "NL"
        
        clean_name = group_name.replace("节点", "").strip()
        # Remove emoji from clean_name if present
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        emoji = re.search(r'([^\w\s])', group_name)
        emoji_char = emoji.group(1) if emoji else "🇳🇱"
        
        auto_name = f"{short_code} AUTO"
        
        # Insert into PROXY, Telegram, Google, GLOBAL proxies lists
        for target in ["PROXY", "Telegram", "Google", "GLOBAL"]:
            pattern = rf"(name:\s*{target}\s*\n\s*type:\s*select\s*\n\s*proxies:\s*\n(?:\s*-\s*[^\n]+\n)+)"
            match = re.search(pattern, yaml_content)
            if match:
                proxies_block = match.group(1)
                if auto_name not in proxies_block:
                    # Find last - AUTO item
                    lines = proxies_block.splitlines()
                    for i in range(len(lines)-1, -1, -1):
                        if lines[i].strip().startswith("- "):
                            lines.insert(i + 1, f"      - {auto_name}")
                            break
                    new_block = "\n".join(lines) + "\n"
                    yaml_content = yaml_content.replace(match.group(1), new_block)
                    print(f"[bdg.yaml] Added {auto_name} to {target}")
                    
        # Add group definition
        def_pattern = rf"name:\s*{auto_name}\s*\n"
        if not re.search(def_pattern, yaml_content):
            new_def = f"""  - icon: https://testingcf.jsdelivr.net/gh/Orz-3/mini@master/Color/{short_code}.png
    include-all: true
    exclude-filter: (?i)GB|Traffic|Expire|Premium|频道|订阅|ISP|流量|到期|重置
    filter: (?i){clean_name}|{short_code}|{regex_pattern}|{emoji_char}
    name: {auto_name}
    type: url-test
    interval: 300"""
            # Insert before GLOBAL group
            match = re.search(r"(\s*-\s*icon:[^\n]+Global\.png)", yaml_content)
            if match:
                yaml_content = yaml_content.replace(match.group(1), f"\n{new_def}\n" + match.group(1))
                print(f"[bdg.yaml] Defined auto group: {auto_name}")
                
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
            
    print(f"\nSuccessfully added {group_name}!")

if __name__ == "__main__":
    main()
