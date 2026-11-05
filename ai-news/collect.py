#!/usr/bin/env python3
"""AIニュース朝刊：対象期間の記事候補を、日付付きで機械的に集める。

使い方:
  python3 ai-news/collect.py                 # 今日（日本時間）を配信日として集める
  python3 ai-news/collect.py --date 2026-11-03   # 配信日を指定（試し実行用）

出力: 対象期間（日本時間）に公開された候補を、情報源ごとに Markdown で標準出力へ。
      最後に、取得に失敗した情報源の一覧を出す（その分は手で確認する）。
外部ライブラリは使わない（標準ライブラリのみ）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

JST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (compatible; ai-news-digest/1.0)"
TIMEOUT = 25

# (表示名, フィードURL, 分類)。分類は選ぶときの参考
FEEDS = [
    ("OpenAI", "https://openai.com/news/rss.xml", "LLM"),
    ("Google AI ブログ", "https://blog.google/technology/ai/rss/", "LLM"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml", "LLM"),
    ("Google 開発者ブログ", "https://developers.googleblog.com/feeds/posts/default", "LLM"),
    ("MCP 公式ブログ", "https://blog.modelcontextprotocol.io/index.xml", "MCP・エージェント"),
    ("GitHub ブログ", "https://github.blog/feed/", "MCP・エージェント"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml", "コミュニティ"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/", "コミュニティ"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", "メディア"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "メディア"),
    ("Ars Technica AI", "https://arstechnica.com/ai/feed/", "メディア"),
    ("ITmedia AI+", "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml", "日本"),
    # AIツールの新機能（更新情報）。新機能は漏らさず載せるため
    ("Gemini（Google）", "https://blog.google/products/gemini/rss/", "新機能"),
    ("Google Labs（NotebookLM など）", "https://blog.google/technology/google-labs/rss/", "新機能"),
    ("GitHub の更新情報（Copilot など）", "https://github.blog/changelog/feed/", "新機能"),
    ("Cursor の更新情報", "https://cursor.com/changelog/rss.xml", "新機能"),
]

# Hacker News で拾う語（ポイントの高いものだけ）
HN_QUERIES = ["Claude", "Anthropic", "OpenAI", "GPT", "Gemini", "LLM", "MCP", "AI agent", "Llama", "Mistral", "DeepSeek", "Qwen", "Sora", "Veo", "Midjourney"]
HN_MIN_POINTS = 40

# npm のリリース時刻（Claude Code など、変更履歴に日付が無いもの）
NPM_PACKAGES = [("Claude Code", "@anthropic-ai/claude-code")]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
        return res.read()


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        d = None
    if d is None:
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def strip_tags(s: str | None, limit: int = 200) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] + ("…" if len(s) > limit else "")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_feed(url: str):
    root = ET.fromstring(fetch(url))
    items = []
    for el in root.iter():
        name = local(el.tag)
        if name not in ("item", "entry"):
            continue
        rec = {"title": "", "link": "", "date": None, "summary": ""}
        for child in el:
            c = local(child.tag)
            if c == "title":
                rec["title"] = strip_tags(child.text, 300)
            elif c == "link":
                href = child.get("href")
                if href and (child.get("rel") in (None, "alternate")):
                    rec["link"] = href
                elif child.text and not rec["link"]:
                    rec["link"] = child.text.strip()
            elif c in ("pubDate", "published", "updated", "date") and rec["date"] is None:
                rec["date"] = parse_date(child.text)
            elif c in ("description", "summary", "content") and not rec["summary"]:
                rec["summary"] = strip_tags(child.text)
        items.append(rec)
    return items


def window(delivery: datetime):
    """配信日 → 対象期間（日本時間）。月曜は金〜日、火〜金は前日。土日は None"""
    wd = delivery.weekday()  # 月=0
    if wd >= 5:
        return None
    start_day = delivery - timedelta(days=3 if wd == 0 else 1)
    start = start_day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = delivery.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="配信日 YYYY-MM-DD（日本時間）。省略すると今日")
    args = ap.parse_args()
    if args.date:
        delivery = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=JST)
    else:
        delivery = datetime.now(JST)
    w = window(delivery)
    if not w:
        print("土日は配信しません")
        return 0
    start, end = w
    print(f"# 記事候補  配信日 {delivery:%Y-%m-%d}  対象 {start:%m/%d %H:%M}〜{end - timedelta(minutes=1):%m/%d %H:%M}（日本時間）\n")

    failed = []
    seen = set()

    def in_window(d):
        return d is not None and start <= d.astimezone(JST) < end

    for name, url, kind in FEEDS:
        try:
            items = [i for i in read_feed(url) if in_window(i["date"])]
        except Exception as e:  # noqa: BLE001 失敗は最後にまとめて出す
            failed.append(f"{name}（{url}）: {e.__class__.__name__}")
            continue
        if not items:
            continue
        print(f"## {name}［{kind}］")
        for i in sorted(items, key=lambda x: x["date"]):
            if i["link"] in seen:
                continue
            seen.add(i["link"])
            print(f"- {i['date'].astimezone(JST):%m/%d %H:%M} {i['title']}\n  {i['link']}")
            if i["summary"]:
                print(f"  > {i['summary']}")
        print()

    # Hacker News
    hn = {}
    for q in HN_QUERIES:
        params = {
            "query": q,
            "tags": "story",
            "numericFilters": f"created_at_i>={int(start.timestamp())},created_at_i<{int(end.timestamp())},points>={HN_MIN_POINTS}",
            "hitsPerPage": "30",
        }
        try:
            data = json.loads(fetch("https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(params)))
        except Exception as e:  # noqa: BLE001
            failed.append(f"Hacker News（{q}）: {e.__class__.__name__}")
            continue
        for h in data.get("hits", []):
            hn[h["objectID"]] = h
    if hn:
        print("## Hacker News［コミュニティ］（ポイント順）")
        for h in sorted(hn.values(), key=lambda x: -(x.get("points") or 0))[:25]:
            d = datetime.fromtimestamp(h["created_at_i"], JST)
            link = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
            print(f"- {d:%m/%d %H:%M} [{h.get('points')}pt / {h.get('num_comments')}件] {h.get('title')}\n  {link}\n  HN: https://news.ycombinator.com/item?id={h['objectID']}")
        print()

    # npm のリリース
    for name, pkg in NPM_PACKAGES:
        try:
            data = json.loads(fetch("https://registry.npmjs.org/" + urllib.parse.quote(pkg, safe="@")))
        except Exception as e:  # noqa: BLE001
            failed.append(f"npm {pkg}: {e.__class__.__name__}")
            continue
        versions = [(v, parse_date(t)) for v, t in data.get("time", {}).items() if v not in ("created", "modified")]
        hits = [(v, d) for v, d in versions if in_window(d)]
        if hits:
            print(f"## {name} のリリース（npm）")
            for v, d in sorted(hits, key=lambda x: x[1]):
                print(f"- {d.astimezone(JST):%m/%d %H:%M} v{v}")
            print("  変更内容は https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md の該当バージョンを読む\n")

    print("## 手で確認する情報源（フィードが無い・日付が取れないもの）")
    print("ai-news/SOURCES.md の「必ず確認」のうち、上に出ていないもの（Anthropic ニュース、Claude ブログ、リリースノート、Mistral、xAI、Cursor、Midjourney、Runway、ElevenLabs など）を WebFetch で開いて確認する。")
    if failed:
        print("\n## 取得に失敗した情報源（WebFetch や Web 検索で補う）")
        for f in failed:
            print(f"- {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
