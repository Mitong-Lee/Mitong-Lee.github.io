import os
import uuid
import re

folder = os.path.dirname(os.path.abspath(__file__))

# 支持的图片格式
extensions = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".tif", ".tiff", ".bmp", ".heic"
}

# 自然排序
def natural_key(text):
    parts = re.split(r"(\d+)", text)
    return [
        (0, int(part)) if part.isdigit() else (1, part.lower())
        for part in parts
    ]

# 获取图片，跳过 cover
files = [
    f for f in os.listdir(folder)
    if os.path.isfile(os.path.join(folder, f))
    and os.path.splitext(f)[1].lower() in extensions
    and "cover" not in f.lower()
]

# 区分已经编号和未编号的图片
numbered_files = []
unnumbered_files = []

for f in files:
    name, ext = os.path.splitext(f)

    # 只识别纯数字文件名，例如 01.jpg、05.png
    match = re.fullmatch(r"\d+", name)

    if match:
        numbered_files.append((int(name), f))
    else:
        unnumbered_files.append(f)

# 找出当前最大编号
max_number = max(
    (number for number, _ in numbered_files),
    default=0
)

# 未编号文件自然排序
unnumbered_files.sort(key=natural_key)

# 下一个编号
start_number = max_number + 1

print(f"当前最大编号：{max_number:02d}")
print("即将处理的图片：")

for i, f in enumerate(unnumbered_files, start=start_number):
    print(f"{i:02d} -> {f}")

if not unnumbered_files:
    print("\n没有需要重命名的图片。")
    exit()

# 第一步：全部改为唯一临时名称
temp_files = []

for f in unnumbered_files:
    ext = os.path.splitext(f)[1]

    temp_name = "__temp_" + uuid.uuid4().hex + ext

    old_path = os.path.join(folder, f)
    temp_path = os.path.join(folder, temp_name)

    os.rename(old_path, temp_path)
    temp_files.append((temp_path, ext))

# 第二步：从最大编号 + 1 开始重命名
for i, (temp_path, ext) in enumerate(temp_files, start=start_number):
    new_name = f"{i:02d}{ext}"
    new_path = os.path.join(folder, new_name)

    if os.path.exists(new_path):
        raise FileExistsError(f"目标文件已存在：{new_name}")

    os.rename(temp_path, new_path)

print(f"\n完成！共重命名 {len(unnumbered_files)} 张图片。")
print(f"编号范围：{start_number:02d}–{start_number + len(unnumbered_files) - 1:02d}")