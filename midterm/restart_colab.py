"""Restart the app after an updated ZIP upload in the same Colab session.

In a Colab code cell: %run /content/zaendrive_midterm/ZaenDrive/restart_colab.py
The existing API environment and installed packages are reused.
"""

import importlib
import os
import sys
from pathlib import Path

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


def restart_app():
    import gradio as gr

    root = Path(__file__).resolve().parent
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    gr.close_all()
    for name in ("rag", "rental_tools", "scope_guard", "agent", "app"):
        importlib.reload(importlib.import_module(name))

    from agent import RentalAgent, Settings, make_client
    from app import build_app
    from rental_tools import initialize_database

    print("Database rows:", initialize_database())
    settings = Settings.from_env()
    assistant = RentalAgent(make_client(settings), settings)
    demo = build_app(assistant)
    demo.queue().launch(share=True, prevent_thread_lock=True)
    return demo


if __name__ == "__main__":
    demo = restart_app()
