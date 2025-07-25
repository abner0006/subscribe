import requests
import os

# --------------------------
# 原来 main.py 里的工具函数
# --------------------------
def read_txt_to_array(file_name):
    """读取文本文件到数组，跳过空行和注释"""
    result = []
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和#开头的注释
                    result.append(line)
        return result
    except FileNotFoundError:
        print(f"⚠️ 未找到 {file_name}")
        return []
    except Exception as e:
        print(f"读取 {file_name} 出错：{e}")
        return []

def traditional_to_simplified(text):
    """简繁转换（依赖 opencc 库，没有的话返回原文本）"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')  # 繁体转简体
        return cc.convert(text)
    except ImportError:
        print("ℹ️ 未安装 opencc，跳过简繁转换")
        return text
    except Exception as e:
        print(f"简繁转换出错：{e}")
        return text

# --------------------------
# 原来 update_live.py 的核心逻辑（修改后保留名称）
# --------------------------
def main():
    print("=== 开始更新直播源 ===")
    # 1. 读取 urls.txt（直接用上面的函数）
    subscribe_urls = read_txt_to_array("urls.txt")
    if not subscribe_urls:
        print("⚠️ urls.txt 为空，无法更新")
        return
    
    # 2. 批量下载订阅源并提取直播源（保留名称+链接）
    all_streams = []
    for url in subscribe_urls:
        print(f"处理订阅源：{url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            content = response.text
            
            # 3. 提取直播源（按“名称,链接”格式拆分）
            for line in content.splitlines():
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 按逗号拆分名称和链接（只拆第一个逗号）
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name, stream_url = parts
                    # 如需简繁转换，可对名称或链接处理
                    # name = traditional_to_simplified(name)
                    # stream_url = traditional_to_simplified(stream_url)
                    all_streams.append(f"{name},{stream_url}")  # 保留名称+链接格式
            print(f"已提取 {len(all_streams)} 个源")
        except Exception as e:
            print(f"下载失败：{e}")
    
    # 4. 去重并保存到 live.txt（保留名称+链接）
    all_streams = list(set(all_streams))  # 去重（按名称+链接整体去重）
    with open("live.txt", "w", encoding="utf-8") as f:
        if not all_streams:
            f.write("# 无有效直播源\n")  # 避免空文件报错
        else:
            f.write("\n".join(all_streams))
    print(f"✅ 已保存 {len(all_streams)} 个直播源到 live.txt（含名称）")
    print("=== 更新完成 ===")

if __name__ == "__main__":
    main()
