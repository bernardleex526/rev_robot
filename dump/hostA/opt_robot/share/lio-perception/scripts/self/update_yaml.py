from ruamel.yaml import YAML
import sys

# 检查参数个数
if len(sys.argv) < 3:
    print("Usage: python3 update_yaml.py <source_file_name> <target_file_name>")
    sys.exit(1)

# 接收文件名作为参数
src_filename = sys.argv[1]
tar_filename = sys.argv[2]

print(f"Processing file: {src_filename} {tar_filename}")


yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(sequence=4, offset=2)

def deep_update(target, src):
    for key, value in src.items():
        if key not in target.keys():
            continue
        if isinstance(value, dict):
            node = target.setdefault(key, {})
            deep_update(node, value)
        else:
            target[key] = value

def update_yaml(file_src_path, file_tar_path):
    with open(file_src_path) as fa:
        data_src = yaml.load(fa)
    
    with open(file_tar_path) as fb:
        data_tar = yaml.load(fb)

    # 使用递归函数更新数据
    deep_update(data_tar, data_src)

    with open(file_tar_path, 'w') as fb:
        yaml.dump(data_tar, fb)

update_yaml(src_filename, tar_filename)
