#!/bin/bash
#SBATCH --job-name=my_experiment
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:1

# Wrap your command with notify-exp run — it notifies on success or failure.
# notify-exp must be on PATH (added via setup.sh).
notify-exp run python train.py --config configs/resnet.yaml --epochs 100
