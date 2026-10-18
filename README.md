# Simple Telegram Music Bot

Send a song name or YouTube link, get the audio back. Built with python-telegram-bot + yt-dlp.

## 1. Get a token
Open @BotFather in Telegram -> /newbot -> copy the token.

## 2. Run on Termux
```bash
pkg update && pkg upgrade -y
pkg install python git -y
cd music-bot
pip install -r requirements.txt
export BOT_TOKEN="123456:ABC-your-token"
python bot.py
```
Keep it alive in the background:
```bash
pkg install tmux -y
tmux new -s bot          # run the bot inside, detach with Ctrl+B then D
termux-wake-lock         # stops Android from sleeping Termux
```

## 3. Deploy on Render
1. Push this folder to a GitHub repo (bot.py, requirements.txt, render.yaml at the root).
2. Render dashboard -> New -> Blueprint -> pick the repo.
3. When asked, paste BOT_TOKEN. Deploy.
4. Free web services sleep after ~15 min without HTTP traffic. Ping the
   service URL every 10 min with UptimeRobot (or use a paid Background Worker).

## Notes
- Audio is sent as m4a, so no ffmpeg is needed.
- YouTube often blocks datacenter IPs (Render). If downloads fail there,
  keep `yt-dlp` updated, or run the bot from Termux / a home connection.
- Telegram bots can upload files up to 50 MB.
- Only download content you have the right to.
