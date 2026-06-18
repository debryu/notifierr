# experiment-notifier

Telegram notifications for ML experiments. Works with SLURM and direct Python runs. Zero changes to existing scripts.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed on the machine
- A Telegram bot token (from [@BotFather](https://t.me/BotFather)) and your chat ID (from [@userinfobot](https://t.me/userinfobot))

## Setup (one time per machine)

```bash
git clone https://github.com/<you>/experiment-notifier.git ~/experiment-notifier
cd ~/experiment-notifier
bash setup.sh
```

Follow the printed instructions to add `notify-exp` to your `PATH`, then:

```bash
cp .env.example ~/.notifier.env
# Edit ~/.notifier.env — add your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
notify-exp test   # should send you a Telegram message
```

## Usage

### CLI wrapper — zero changes to existing scripts

```bash
# Direct run
notify-exp run python train.py --lr 0.001

# With a custom label in the notification
notify-exp run --name "ResNet ablation" python train.py
```

### SLURM job

```bash
#!/bin/bash
#SBATCH --job-name=resnet_train

notify-exp run python train.py --config cfg.yaml
```

The notification automatically includes the SLURM job ID and name when running inside a SLURM job.

### Python decorator / context manager

Add to your existing project:

```bash
uv add git+https://github.com/<you>/experiment-notifier
```

Then in your script:

```python
from notifier import notify_on_complete, notify

# Decorator (uses function name as label)
@notify_on_complete
def main():
    train()

# Decorator with custom label
@notify_on_complete("ResNet-50 training")
def main():
    train()

# Context manager
with notify("data preprocessing"):
    preprocess()
```

### Send a custom message

```bash
notify-exp send "Preprocessing done, starting training..."
```

## Notification format

```
✅ Experiment SUCCESS

Job: train.py
Host: gpu-node-01
Duration: 2h 15m 32s
SLURM ID: 12345        ← only when running in SLURM
```

Failed jobs show ❌ instead of ✅.

## Credentials

The tool looks for credentials in this order:

1. `$NOTIFIER_ENV_FILE` — explicit path override
2. `~/.notifier.env` — global config (recommended)
3. `./.env` — current directory fallback

```
# ~/.notifier.env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Deploy to a new machine

```bash
git clone https://github.com/<you>/experiment-notifier.git ~/experiment-notifier
cd ~/experiment-notifier && bash setup.sh
# Add PATH line to ~/.bashrc as instructed
cp .env.example ~/.notifier.env && nano ~/.notifier.env
notify-exp test
```
