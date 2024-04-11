#!/bin/bash
#SBATCH -N 1 # 指定node的数量
#SBATCH --gres=gpu:1 # 需要使用多少GPU
#SBATCH -o evaluate.log # 把输出结果STDOUT保存在哪一个文件
#SBATCH -w wxhd11
# srun -N 1 -G 1 -w wxhd11 \
export CUDA_VISIBLE_DEVICES=0
python -u evaluate_logprobs.py \
    --model-name-or-path "./models/llama2-7b-chat" \
    --model-type "judgelm" \
    --data-type "judgelm" \
    --class-type "logprobs-full" \
    --data-path ./data/