# Deadlock Changelog Bot

## Installation

1. Install `uv`
2. Clone the repository
3. Run `uv run main.py`

### Server (systemd)

If you want to run this as a service,
you need to symlink the `deadlock-changelog-bot.service` file to `/etc/systemd/system/` and
then run `systemctl enable deadlock-changelog-bot.service` and `systemctl start deadlock-changelog-bot.service`:

```bash
sudo ln -s /path/to/deadlock-changelog-bot/deadlock-changelog-bot.service /etc/systemd/system/
sudo systemctl enable deadlock-changelog-bot.service
sudo systemctl start deadlock-changelog-bot.service
```

To see the logs, you can use `journalctl -u deadlock-changelog-bot.service`.
To stop the service,
you can use `systemctl stop deadlock-changelog-bot.service`
and to disable it `systemctl disable deadlock-changelog-bot.service`.