#!/usr/bin/env python3
"""AIニュース朝刊：中身を書いた JSON から Slack のカード（Block Kit）を組み立てて、
ボット「AI News」として #ai_news に投稿する。

使い方:
  python3 ai-news/post_digest.py digest.json            # 投稿する
  python3 ai-news/post_digest.py digest.json --dry-run  # 投稿せず、組み立てた中身を表示

digest.json の形（すべて日本語で書く。Slack の書式：太字は *…*、リンクは <URL|表示名>）:
{
  "date_label": "11/6（木）",            # 配信日
  "target_label": "11/5（水）",          # 対象期間（月曜は「10/31（金）〜11/2（日）」など）
  "counts": "Claude 3 ・ 他社LLM 2 ・ エージェント 3 ・ 生成メディア 1 ・ 業界 1",
  "summary": "ひとことで言うと…（1〜2文）",
  "trends": ["全体の傾向 1", "…"],       # 2〜3点
  "companies": ["Anthropic：…", "…"],   # 動きのあった会社ごとに1行
  "advice": ["今日試すとよいこと", "…"], # 2〜3点
  "feedback": "前回の反応から：…",       # 1行。無ければ省略
  "notice": "⚠️ …",                      # 任意。Nochon に保存できなかった等
  "items": [                             # 今日の10件（番号順）
    {
      "no": 1,
      "area": "Claude・Anthropic",       # 分野：Claude・Anthropic／他社LLM／エージェント・MCP／生成メディア／業界・規制
      "title": "Claude Code に ◯◯ 機能",
      "summary": "何が・いつから・誰が使えるか（2〜3文）",
      "explain": "（新機能のときだけ）つまり何ができるか。具体的な使い道と、何がすごいのか（2〜3文）",
      "relation": ["何が変わるか", "具体的な落とし込み", "今日やるなら"],
      "links": [{"url": "https://…", "label": "原文（Anthropic 公式）"}, {"url": "https://…", "label": "補足（The Verge）"}]
    }
  ],
  "others": [                            # 10件に入らなかった見出し（新機能は必ずここに残す）
    {"title": "…", "note": "一言の説明", "url": "https://…"}
  ]
}

出力: 投稿した ts を JSON で表示する（{"parent_ts": "...", "item_ts": {"1": "...", …}, "others_ts": "..."}）。
入り口が失敗したら、どこまで投稿できたかを表示して終了コード 1 で終わる。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://personal-notes-khaki.vercel.app/api/agent/slack-post"
NUMS = "①②③④⑤"
SECTION_LIMIT = 2900  # Slack の section は 3000 文字まで


def clip(s: str, n: int = SECTION_LIMIT) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": clip(text)}}


def context(text: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": clip(text)}]}


def bullets(lines: list[str]) -> str:
    return "\n".join(f"・{l.strip()}" for l in lines if l and l.strip())


def parent_message(d: dict) -> dict:
    items = d.get("items", [])
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"📰 AIニュース {d['date_label']}"[:150]}},
        context(f"対象：{d['target_label']}　｜　{d.get('counts', '')}".rstrip("　｜ ")),
    ]
    if d.get("summary"):
        blocks.append(section(f"*ひとことで*\n{d['summary']}"))
    blocks.append({"type": "divider"})
    blocks.append(section(f"*今日の{len(items)}件*　（各ニュースはスレッドに）\n" + bullets([i["title"] for i in items])))
    blocks.append({"type": "divider"})
    if d.get("trends"):
        blocks.append(section("*全体の傾向*\n" + bullets(d["trends"])))
    if d.get("companies"):
        blocks.append(section("*各社の動き*\n" + bullets(d["companies"])))
    if d.get("advice"):
        blocks.append(section("*あなたへの示唆*\n" + bullets(d["advice"])))
    tail = [x for x in (d.get("feedback"), d.get("notice")) if x]
    if tail:
        blocks.append(context("\n".join(tail)))
    # text は通知・プレビュー用。📰 で始める（翌朝の読み取りと、質問ボットの見分けに使う）
    return {"text": f"📰 AIニュース {d['date_label']}　今日の{len(items)}件", "blocks": blocks}


def item_message(it: dict) -> dict:
    blocks = [
        context(f"*#{it['no']}*　{it.get('area', '')}"),
        section(f"*{it['title']}*"),
        section(it["summary"]),
    ]
    if it.get("explain"):
        blocks.append(section(f"*🔰 つまり何ができる？*\n{it['explain']}"))
    rel = [r for r in it.get("relation", []) if r and r.strip()]
    if rel:
        lines = [f"{NUMS[k] if k < len(NUMS) else '・'} {r.strip()}" for k, r in enumerate(rel)]
        blocks.append(context("💡 *あなたへの関係*\n" + "\n".join(lines)))
    links = [l for l in it.get("links", []) if l.get("url")]
    if links:
        blocks.append(context("🔗 " + "　／　".join(f"<{l['url']}|{l.get('label') or '原文'}>" for l in links)))
    # text は「#番号 【分野】タイトル」の形にする（翌朝の反応の読み取りと、質問ボットが配信と見分けるのに使う）
    return {"text": f"#{it['no']} 【{it.get('area', 'ニュース')}】{it['title']}", "blocks": blocks}


def others_message(others: list[dict]) -> dict:
    lines = []
    for o in others:
        title = f"<{o['url']}|{o['title']}>" if o.get("url") else o["title"]
        lines.append(f"・{title}" + (f"　— {o['note']}" if o.get("note") else ""))
    blocks = [section("*📋 その他の見出し*\n" + "\n".join(lines))]
    # 長いときは section を分ける（1つ 3000 文字まで）
    if len(blocks[0]["text"]["text"]) >= SECTION_LIMIT:
        blocks, chunk = [], "*📋 その他の見出し*"
        for line in lines:
            if len(chunk) + len(line) + 1 > SECTION_LIMIT:
                blocks.append(section(chunk))
                chunk = ""
            chunk = f"{chunk}\n{line}" if chunk else line
        blocks.append(section(chunk))
    return {"text": f"📋 その他の見出し（{len(others)}件）", "blocks": blocks}


def post(payload: dict, thread_ts: str | None = None) -> str:
    body = dict(payload)
    if thread_ts:
        body["thread_ts"] = thread_ts
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    if not data.get("ok") or not data.get("ts"):
        raise RuntimeError(f"投稿できませんでした: {data}")
    return data["ts"]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    dry = "--dry-run" in sys.argv[2:]
    parent = parent_message(d)
    items = [item_message(it) for it in d.get("items", [])]
    others = others_message(d["others"]) if d.get("others") else None

    if dry:
        print(json.dumps({"parent": parent, "items": items, "others": others}, ensure_ascii=False, indent=1))
        return 0

    done: dict = {"parent_ts": None, "item_ts": {}, "others_ts": None}
    try:
        done["parent_ts"] = post(parent)
        for it, msg in zip(d.get("items", []), items):
            done["item_ts"][str(it["no"])] = post(msg, done["parent_ts"])
        if others:
            done["others_ts"] = post(others, done["parent_ts"])
    except Exception as e:  # noqa: BLE001 どこまで投稿できたかを残して終わる
        print(json.dumps({"error": str(e), **done}, ensure_ascii=False))
        return 1
    print(json.dumps(done, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
