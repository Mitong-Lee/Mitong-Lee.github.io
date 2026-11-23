
import os
import uuid

folder = os.path.dirname(os.path.abspath(__file__))

# 支持的图片格式
extensions = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".tif", ".tiff", ".bmp", ".heic"
}

# 获取图片，跳过 cover
files = [
    f for f in os.listdir(folder)
    if os.path.isfile(os.path.join(folder, f))
    and os.path.splitext(f)[1].lower() in extensions
    and "cover" not in f.lower()
]

# 按文件名自然排序
files.sort(key=str.lower)

print("即将处理的图片：")
for i, f in enumerate(files, 1):
    print(f"{i:02d} -> {f}")

# 第一步：全部改为唯一临时名称
temp_files = []

for f in files:
    ext = os.path.splitext(f)[1]
    temp_name = "__temp_" + uuid.uuid4().hex + ext

    old_path = os.path.join(folder, f)
    temp_path = os.path.join(folder, temp_name)

    os.rename(old_path, temp_path)
    temp_files.append((temp_path, ext))

# 第二步：从 01 开始编号
for i, (temp_path, ext) in enumerate(temp_files, start=1):
    new_name = f"{i:02d}{ext}"
    new_path = os.path.join(folder, new_name)

    os.rename(temp_path, new_path)

print(f"\n完成！共重命名 {len(files)} 张图片。")
print("第一张图片：01")
