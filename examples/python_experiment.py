"""
Example: using the notifier decorator/context manager in your own script.

Requires notifier to be installed in the active Python environment:
    uv add git+https://github.com/<you>/experiment-notifier
"""

from notifier import notify, notify_on_complete


# Option A: decorator (name defaults to function name)
@notify_on_complete
def train_simple():
    print("Training...")
    # your training code here


# Option B: decorator with custom name
@notify_on_complete("ResNet-50 ImageNet")
def train_resnet():
    print("Training ResNet...")
    # your training code here


# Option C: context manager (useful for inline blocks)
def run_experiment():
    with notify("data preprocessing"):
        print("Preprocessing...")

    with notify("model training"):
        print("Training...")


if __name__ == "__main__":
    train_resnet()
