"""Entry point for the Ong & Co 4 La Discord bot.

Feature modules are imported once so their commands/events register on the
shared Discord bot instance from core.py.
"""
import os
from .core import bot, keep_alive

# Import modules for command/event registration.
from . import admin
from . import shop
from . import reminders
from . import leaderboard
from . import study
from . import discipline
from . import rooms
from . import admin_tools
from . import events

def main():
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Thiếu biến môi trường DISCORD_TOKEN.")
    bot.run(token)

if __name__ == "__main__":
    main()
