#!/usr/bin/env python3
"""AIニュースの速報：最新の候補を集めて Nochon に送る（1時間おきに cron-job.org が GitHub Actions を起動して動く）。

Nochon（/api/agent/ai-news-breaking）が、新しい記事だけを選び、Claude で速報にするものを判断して、
ボット「AI News」として Slack の #ai_news に流す。ここでは候補を集めて送るだけ。

使い方:
  NOCHON_AGENT_TOKEN=... python3 ai-news/breaking.py           # 送る（8〜22時の間だけ動く）
  python3 ai-news/breaking.py --dry-run                         # 送らずに候補を表示
  NOCHON_AGENT_TOKEN=... python3 ai-news/breaking.py --force    # 時間帯に関係なく送る（動作確認用）
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import FEEDS, JST, fetch, read_feed  # noqa: E402

ENDPOINT = "https://personal-notes-khaki.vercel.app/api/agent/ai-news-breaking"
LOOKBACK = timedelta(hours=26)  # 送る範囲。新しいかどうかの最終判断は Nochon 側（90分以内・記録にないもの）
QUIET_START, QUIET_END = 22, 8  # 22:00〜翌8:00は流さない（その間の分は翌朝の配信に回る）
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def feed_candidates(now: datetime) -> list[dict]:
    out = []
    for name, url, _kind in FEEDS:
        try:
            items = read_feed(url)
        except Exception as e:  # noqa: BLE001 1つ失敗しても続ける
            print(f"skip {name}: {e.__class__.__name__}", file=sys.stderr)
            continue
        for i in items:
            d = i.get("date")
            if d is None or not i.get("link") or now - d > LOOKBACK or d - now > timedelta(minutes=10):
                continue
            out.append({
                "source": name,
                "title": i["title"],
                "url": i["link"],
                "summary": i.get("summary", ""),
                "published_at": d.astimezone(timezone.utc).isoformat(),
            })
    return out


def anthropic_news(now: datetime) -> list[dict]:
    """Anthropic のニュース一覧（フィードが無く、日付しか分からない）"""
    try:
        html = fetch("https://www.anthropic.com/news").decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"skip Anthropic: {e.__class__.__name__}", file=sys.stderr)
        return []
    today = now.astimezone(JST).date()
    out, seen = [], set()
    for m in re.finditer(r'href="(/news/[a-z0-9\-]+)"', html):
        path = m.group(1)
        if path in seen or path in ("/news/announcements", "/news/features", "/news/product", "/news/policy"):
            continue
        seg = html[m.start(): m.start() + 2000]
        dm = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}), (\d{4})", seg)
        if not dm:
            continue
        date = datetime(int(dm.group(3)), MONTHS[dm.group(1)], int(dm.group(2))).date()
        if (today - date).days > 1:
            continue
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg)).strip()
        seen.add(path)
        out.append({
            "source": "Anthropic 公式ニュース",
            "title": text[:120],
            "url": "https://www.anthropic.com" + path,
            "summary": text[:400],
            "date": date.isoformat(),
        })
    return out


def claude_code_releases(now: datetime) -> list[dict]:
    """Claude Code の新しい版（npm の公開時刻と、変更履歴の該当部分）"""
    try:
        data = json.loads(fetch("https://registry.npmjs.org/@anthropic-ai%2fclaude-code"))
        changelog = fetch("https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md").decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"skip Claude Code: {e.__class__.__name__}", file=sys.stderr)
        return []
    out = []
    for ver, t in data.get("time", {}).items():
        if ver in ("created", "modified"):
            continue
        d = datetime.fromisoformat(t.replace("Z", "+00:00"))
        if now - d > LOOKBACK:
            continue
        m = re.search(rf"^## {re.escape(ver)}\s*$(.*?)(?=^## |\Z)", changelog, re.M | re.S)
        notes = re.sub(r"\s+", " ", m.group(1)).strip()[:500] if m else ""
        out.append({
            "source": "Claude Code（npm・変更履歴）",
            "title": f"Claude Code v{ver}",
            "url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md",
            "summary": notes,
            "published_at": d.isoformat(),
        })
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    now = datetime.now(timezone.utc)
    hour = now.astimezone(JST).hour
    if not force and not dry and (hour >= QUIET_START or hour < QUIET_END):
        print(f"{hour}時台は流さない時間帯のため終了")
        return 0

    candidates = feed_candidates(now) + anthropic_news(now) + claude_code_releases(now)
    if dry:
        print(json.dumps(candidates, ensure_ascii=False, indent=1))
        print(f"候補 {len(candidates)} 件", file=sys.stderr)
        return 0

    token = os.environ.get("NOCHON_AGENT_TOKEN", "")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"candidates": candidates}, ensure_ascii=False).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=150) as res:
        print(res.read().decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
