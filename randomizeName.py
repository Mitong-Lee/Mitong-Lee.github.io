import os
import uuid
import secrets
import string

# 当前脚本所在文件夹
folder = os.path.dirname(os.path.abspath(__file__))

# 支持的图片格式
extensions = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".tif", ".tiff", ".bmp", ".heic"
}

# 随机字母长度
NAME_LENGTH = 8

# 随机字母池：小写英文字母
letters = string.ascii_lowercase

# 获取图片，跳过 cover
files = [
    f for f in os.listdir(folder)
    if os.path.isfile(os.path.join(folder, f))
    and os.path.splitext(f)[1].lower() in extensions
    and "cover" not in f.lower()
]

print("即将重命名的图片：")

for f in files:
    print(f"  {f}")

if not files:
    print("\n没有需要重命名的图片。")
    raise SystemExit

# 第一步：全部改为唯一临时名称
temp_files = []

for f in files:
    ext = os.path.splitext(f)[1]

    temp_name = "__temp_" + uuid.uuid4().hex + ext

    old_path = os.path.join(folder, f)
    temp_path = os.path.join(folder, temp_name)

    os.rename(old_path, temp_path)
    temp_files.append((temp_path, ext))

# 第二步：生成随机英文字母名称
used_names = set()

print("\n重命名结果：")

for temp_path, ext in temp_files:

    # 生成不重复的随机文件名
    while True:
        random_name = "".join(
            secrets.choice(letters)
            for _ in range(NAME_LENGTH)
        )

        new_name = random_name + ext
        new_path = os.path.join(folder, new_name)

        if new_name.lower() not in used_names and not os.path.exists(new_path):
            break

    used_names.add(new_name.lower())

    os.rename(temp_path, new_path)

    print(f"  {os.path.basename(temp_path)} -> {new_name}")

print(f"\n完成！共重命名 {len(files)} 张图片。")