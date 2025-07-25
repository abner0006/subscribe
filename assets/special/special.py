#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直播源自动整理工具（assets/special/special.py）
========================================
【核心功能】
1. 从网络订阅源拉取直播内容，自动兼容两种格式：
   - 普通文本格式（每行"频道名,链接"或纯链接）
   - M3U格式（自动解析#EXTINF标识的频道名和对应链接）

2. 严格过滤无效内容：
   - 排除含"#genre#"的行
   - 仅保留"频道名,链接"格式（必须含","和"://"）
   - 通过黑名单文件过滤指定内容

3. 增强功能：
   - 名称标准化（将不同写法的频道名统一，如"央视1台"→"CCTV1"）
   - 自动去重（去除重复的直播源）
   - 容错机制（缺失文件自动创建，避免运行中断）

【文件位置及说明】
所有文件均与本脚本（special.py）在同一目录：
- 脚本自身路径：assets/special/special.py

- 必须文件（无则使用默认配置）：
  - urls.txt（路径：assets/special/urls.txt）
    作用：存储订阅源链接，每行1个
    示例内容：
    https://example.com/playlist1.txt
    https://example.com/playlist2.txt
    若文件为空或不存在：自动使用内置默认链接

- 自动维护文件：
  - ExcludeList.txt（路径：assets/special/ExcludeList.txt）
    作用：黑名单，每行1个关键词，完全匹配时过滤该直播源
    示例内容：
    广告
    badurl.com
    测试源
    若文件不存在：自动创建空文件（路径同上）

- 可选文件（无则跳过对应功能）：
  - rename.txt（路径：assets/special/rename.txt）
    作用：名称映射规则，格式为"目标名称,待替换名称1,待替换名称2..."
    示例内容：
    CCTV1,[BD]cctv1,央视1台,高清CCTV-1
    CCTV2,[HD]cctv2,财经频道

- 输出文件：
  - special_output_live.txt（路径：assets/special/special_output_live.txt）
    作用：最终整理后的直播源列表（去重、过滤、名称标准化后）

【运行流程】
1. 读取订阅源（优先从assets/special/urls.txt，其次用默认链接）
2. 拉取内容并解析（M3U格式自动转换为"频道名,链接"）
3. 过滤无效行（排除含#genre#、不符合格式、在黑名单中的内容）
4. 应用名称映射（根据assets/special/rename.txt统一名称）
5. 去重后保存结果到assets/special/special_output_live.txt
"""

import urllib.request
import os
from urllib.parse import urlparse


# 读取文本文件到列表（保留旧脚本逻辑）
def read_txt_to_array(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"读取{file_name}出错：{e}")
        return []


# 自动创建黑名单文件（路径：assets/special/ExcludeList.txt）
if not os.path.exists('ExcludeList.txt'):
    with open('ExcludeList.txt', 'w', encoding='utf-8') as f:
        pass  # 不存在则创建空文件
    print("ExcludeList.txt不存在，已在assets/special/目录创建空文件")
excudelist_lines = read_txt_to_array('ExcludeList.txt')  # 加载黑名单


# 转换M3U格式为"频道名,链接"（完全复用旧脚本逻辑）
def convert_m3u_to_txt(content):
    lines = []
    channel_name = ""
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith("#EXTINF"):
            channel_name = line.split(",")[-1]  # 提取#EXTINF后的频道名
        elif line.startswith(("http", "rtmp")):
            lines.append(f"{channel_name},{line}")  # 拼接为标准格式
    return "\n".join(lines)


# 加载名称映射规则（路径：assets/special/rename.txt）
def load_name_mapping():
    name_mapping = {}
    for line in read_txt_to_array("rename.txt"):
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if len(parts) >= 2:
            name_mapping[parts[0]] = parts[1:]  # 目标名: [待替换名列表]
    print(f"从assets/special/rename.txt加载名称映射规则：共 {len(name_mapping)} 组")
    return name_mapping


# 处理单个订阅源URL（保留旧脚本逻辑）
all_lines = []  # 存储所有有效直播源
def process_url(url):
    try:
        # 模拟浏览器请求头，避免被拦截
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as res:  # 10秒超时
            content = res.read().decode('utf-8', errors='ignore')  # 忽略编码错误
        
        # 若为M3U格式，先转换为标准文本格式
        if content.startswith("#EXTM3U"):
            content = convert_m3u_to_txt(content)
        
        # 过滤并收集有效直播源（旧脚本核心过滤逻辑）
        for line in content.split('\n'):
            line = line.strip()
            if "#genre#" not in line and "," in line and "://" in line and line not in excudelist_lines:
                all_lines.append(line)
        print(f"处理完成：{url}（累计{len(all_lines)}条）")
    except Exception as e:
        print(f"处理URL出错：{url} - {e}")


# 主函数（整合所有流程）
def main():
    print("=== 直播源自动整理工具启动 ===")
    
    # 1. 获取订阅源列表（优先从assets/special/urls.txt，否则用默认链接）
    subscribe_urls = read_txt_to_array("urls.txt")
    if not subscribe_urls:
        print("assets/special/urls.txt为空，使用默认订阅源")
        subscribe_urls = [
            "https://ua.fongmi.eu.org/box.php?url=http://sinopacifichk.com/tv/live",
            "https://ua.fongmi.eu.org/box.php?url=https://tv.iill.top/m3u.father",
        ]
    
    # 2. 处理所有订阅源
    for url in subscribe_urls:
        if url.startswith("http"):
            process_url(url)
    
    # 3. 应用名称映射（根据assets/special/rename.txt）
    name_mapping = load_name_mapping()
    processed_lines = []
    for line in all_lines:
        if ',' in line:
            original_name, link = line.split(',', 1)
            # 检查是否需要替换名称
            for target_name, replace_list in name_mapping.items():
                if original_name in replace_list:
                    processed_lines.append(f"{target_name},{link}")
                    break
            else:
                processed_lines.append(line)  # 不匹配则保留原名
        else:
            processed_lines.append(line)  # 纯链接直接保留
    
    # 4. 去重并保存结果到assets/special/special_output_live.txt
    unique_lines = list(set(processed_lines))  # 自动去重
    output_file = "special_output_live.txt"  # 输出文件名修改
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_lines))
        print(f"\n=== 处理完成 ===")
        print(f"有效直播源数量：{len(unique_lines)}")
        print(f"结果已保存到：assets/special/special_output_live.txt")  # 路径同步修改
    except Exception as e:
        print(f"保存文件出错：{e}")
        exit(1)


if __name__ == "__main__":
    main()
