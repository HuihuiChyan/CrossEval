#!/bin/bash
#SBATCH -N 1 # 指定node的数量
#SBATCH --gres=gpu:1 # 需要使用多少GPU
#SBATCH -o evaluate.log # 把输出结果STDOUT保存在哪一个文件
#SBATCH -w wxhd11
# srun -N 1 -G 1 -w wxhd11 \
export CUDA_VISIBLE_DEVICES=3
python -u evaluate_selfeval.py \
    --model-name-or-path "./models/autoj-13b" \
    --model-type "auto-j" \
    --data-type "mt-bench" \
    --class-type "generation" \
    --data-path ./data/