#!/bin/bash
# Dataset should be format as 
# Center ID + Center Name
#   Subject ID + Subject Name
#           ...
#           Dicoms

# 获取输入参数
SOURCE_DIR="/PATH/TO/DICOMS/DATASET"
TARGET_DIR="/PATH/TO/SAVE"

# 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录 '$SOURCE_DIR' 不存在"
    exit 1
fi

# 创建目标目录（如果不存在）
mkdir -p "$TARGET_DIR"

# 设置日志文件
LOG_FILE="$TARGET_DIR/dcm2niix_$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}")
exec 2> >(tee -a "${LOG_FILE}" >&2)

echo "日志将记录在: $LOG_FILE"

# 遍历源目录中的所有子目录

for dir in "$SOURCE_DIR"/*; do
    echo "处理目录: $dir"
    base_name=$(basename "$dir")
    hp_id=$(echo "$base_name" | cut -d'+' -f1)
    hp_name=$(echo "$base_name" | cut -d'+' -f2-)
    for subdir in "$dir"/*; do
        echo "处理患者目录: $subdir"
        if [ -d "$subdir" ]; then
            subdir_name=$(basename "$subdir")
            target_subdir="$TARGET_DIR/$hp_id+$hp_name/$subdir_name"
            subbase_name=$(basename "$dir")
            pid=$(echo "$subbase_name" | cut -d'+' -f1)
            pname=$(echo "$subbase_name" | cut -d'+' -f2-)
            mkdir -p "$target_subdir"
            echo "创建目标目录: $target_subdir"
            echo "处理目录: $subdir"
            dcm2niix -f "%s+%p+%t" -i y -d 9 -p n -z y -ba n -o "$target_subdir" "$subdir"
            fi
        fi
    done
done


echo "转换完成！"