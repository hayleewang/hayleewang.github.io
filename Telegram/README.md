# Ten Words. STOP.

A Telegram game for the Daily Nebraskan. Players summarize a news story in 10 words or fewer, ending with STOP (like an old telegram). Everyone votes on the best one, which doubles as headline-writing practice.

Example: `HUSKERS FALL TO IOWA IN LAST-SECOND HEARTBREAKER STOP.`

## Setup (5 minutes)

1. In Telegram, message **@BotFather**, send `/newbot`, and follow the prompts. Copy the token.
2. Run the bot (Python 3, no installs needed):

   ```bash
   cd Telegram
   BOT_TOKEN=your_token_here python3 bot.py
   ```
3. Create a group chat, add your bot, and play. Keep the terminal open while playing.

## How a round works

| Step | Who | Command |
|---|---|---|
| 1. Post a story (headline, summary, or DN link) | anyone in the group | `/newround <story>` |
| 2. Tap the **Submit** button and DM the bot a summary | players | (in DM) |
| 3. Close submissions and show the anonymous ballot | anyone | `/vote` |
| 4. Tap **Vote N** buttons (can't vote for yourself) | players | |
| 5. Reveal winner and authors | anyone | `/results` |
| Season standings | anyone | `/leaderboard` |

Rules: 10 words max. STOP doesn't count and gets added automatically. Resubmitting replaces your entry; votes can be changed until `/results`.

## Files

- `bot.py`: Telegram I/O (standard library only)
- `game.py`: game rules and scoring
- `state.json`: created automatically, stores rounds and scores

## Play the News: turn any Daily Nebraskan story into a game

Paste a dailynebraskan.com story link and get a shareable, Daily Nebraskan-styled Mario-style game built from that story. You run through Lincoln to Memorial Stadium and bonk `?` blocks. Six questions come from the reporting and two are headline-writing challenges (best 10-word headline ending in STOP). Right answers score, wrong ones cost a heart.

```bash
cd Telegram
ANTHROPIC_API_KEY=sk-ant-... python3 server.py
```

Open http://localhost:8000, paste a link, and share the `/play/<id>` link it gives you. `/play/demo` works without a key.

**A new game every day:** `/today` always plays the newest story from the Daily Nebraskan's news RSS feed. The server checks the feed every 30 minutes and builds the new game ahead of time, so readers don't wait. Share `https://your-host/today` and it changes by itself whenever the DN publishes. Without an API key, `/today` falls back to the newest saved game or the demo.

- Claude (model `claude-sonnet-5-5`, change with `CLAUDE_MODEL`) writes the questions from the story text. Each game is saved in `games/`, so the same link never costs twice.
- Only dailynebraskan.com links are accepted, and there's a cap of 30 new games per hour (`MAX_NEW_GAMES_PER_HOUR`) to protect your API bill.
- To let other people use it, the server has to be hosted somewhere public (GitHub Pages can't run it; a small host like Render or Fly.io can). Keep the API key as a secret environment variable there.
- In Telegram: run the bot with `GAME_URL=https://your-hosted-server` and send `/play` for today's game or `/play <story link>` for a specific story.
