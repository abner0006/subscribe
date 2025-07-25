import os
import datetime  # 用于生成时间戳

def process_file(filename, keep_lines, output_dir):
    """
    处理单个文件：按 #genre# 分组去重 + 强制追加更新标记
    """
    # 1. 读取文件内容
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 2. 按 "#genre#" 分组
    groups = []
    current_group = []
    for line in lines:
        if ",#genre#" in line:
            if current_group:
                groups.append(current_group)
            current_group = [line]
        else:
            current_group.append(line)
    if current_group:
        groups.append(current_group)

    # 3. 组内去重（保留前 N 个重复频道）
    output_lines = []
    for group in groups:
        seen = {}
        for line in group:
            if ",#genre#" in line:
                output_lines.append(line)
                continue
            parts = line.strip().split(",", 1)
            if len(parts) < 2:
                output_lines.append(line)
                continue
            name = parts[0].strip()
            if seen.get(name, 0) < keep_lines:
                output_lines.append(line)
                seen[name] = seen.get(name, 0) + 1

    # 4. 写入输出文件（强制覆盖 + 追加更新标记）
    output_path = os.path.join(output_dir, os.path.basename(filename))
    with open(output_path, "w", encoding="utf-8") as f:
        # 强制追加更新标记（确保文件内容变化）
        f.write(f"# 手动触发更新标记: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.writelines(output_lines)
    print(f"✅ 处理完成: {filename}（强制覆盖更新）")


def main():
    """
    主逻辑：遍历根目录 .txt 文件，处理后强制输出
    """
    keep_lines = int(os.environ.get("KEEP_LINES", "1"))
    input_dir = "."  # 根目录（与 actions/checkout 拉取目录一致）
    output_dir = "output/Simplified"
    os.makedirs(output_dir, exist_ok=True)

    # 遍历处理所有 .txt 文件
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            process_file(
                filename=os.path.join(input_dir, filename),
                keep_lines=keep_lines,
                output_dir=output_dir
            )


if __name__ == "__main__":
    main()
