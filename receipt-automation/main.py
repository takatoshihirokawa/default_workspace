#!/usr/bin/env python3
"""
領収書自動収集 & AppSiderアップロードスクリプト

使い方:
  python main.py --year 2026 --month 4
  python main.py --year 2026 --month 4 --dry-run
  python main.py --year 2026 --month 4 --services aws slack
"""

import argparse
import asyncio
import os
import sys
from datetime import date

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from appsider import AppSiderUploader
from connectors.aws import AWSConnector
from connectors.google_cloud import GoogleCloudConnector
from connectors.notion import NotionConnector
from connectors.slack import SlackConnector

load_dotenv()

ALL_SERVICES = ["aws", "gcp", "slack", "notion"]

CONNECTOR_MAP = {
    "aws": (
        AWSConnector,
        {
            "email": os.getenv("AWS_EMAIL", ""),
            "password": os.getenv("AWS_PASSWORD", ""),
        },
    ),
    "gcp": (
        GoogleCloudConnector,
        {
            "email": os.getenv("GCP_EMAIL", ""),
            "password": os.getenv("GCP_PASSWORD", ""),
        },
    ),
    "slack": (
        SlackConnector,
        {
            "email": os.getenv("SLACK_EMAIL", ""),
            "password": os.getenv("SLACK_PASSWORD", ""),
            "workspace": os.getenv("SLACK_WORKSPACE", ""),
        },
    ),
    "notion": (
        NotionConnector,
        {
            "email": os.getenv("NOTION_EMAIL", ""),
            "password": os.getenv("NOTION_PASSWORD", ""),
        },
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(description="領収書自動収集 & AppSiderアップロード")
    parser.add_argument("--year", type=int, default=date.today().year, help="対象年 (デフォルト: 今年)")
    parser.add_argument("--month", type=int, default=date.today().month - 1 or 12, help="対象月 (デフォルト: 先月)")
    parser.add_argument("--services", nargs="+", choices=ALL_SERVICES, default=ALL_SERVICES, help="収集するサービス")
    parser.add_argument("--dry-run", action="store_true", help="AppSiderへのアップロードをスキップして確認のみ")
    parser.add_argument("--headed", action="store_true", help="ブラウザを表示して実行（デフォルト: ヘッドレス）")
    return parser.parse_args()


async def run(args):
    print(f"\n{'='*50}")
    print(f"  領収書自動収集 {args.year}年{args.month}月")
    if args.dry_run:
        print("  [DRY-RUN モード] AppSiderへのアップロードはスキップします")
    print(f"{'='*50}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not args.headed,
            downloads_path=str(__import__("pathlib").Path(__file__).parent / "downloads"),
        )
        context = await browser.new_context(accept_downloads=True)

        all_receipts = []
        errors = []

        # --- 各サービスから領収書収集 ---
        for service in args.services:
            connector_cls, config = CONNECTOR_MAP[service]

            # 認証情報が未設定のサービスはスキップ
            if not config.get("email"):
                print(f"[{service.upper()}] 認証情報が .env に設定されていないためスキップ")
                continue

            page = await context.new_page()
            connector = connector_cls(page, config)
            try:
                await connector.login()
                receipts = await connector.download_receipts(args.year, args.month)
                all_receipts.extend(receipts)
            except Exception as e:
                print(f"[{service.upper()}] エラー: {e}")
                errors.append((service, str(e)))
            finally:
                await page.close()

        # --- AppSiderへアップロード ---
        if all_receipts:
            print(f"\n{'='*50}")
            print(f"  AppSiderへのアップロード ({len(all_receipts)} 件)")
            print(f"{'='*50}\n")

            appsider_page = await context.new_page()
            uploader = AppSiderUploader(appsider_page)

            if not args.dry_run:
                await uploader.login()

            success = 0
            failed = 0
            for receipt in all_receipts:
                ok = await uploader.upload_receipt(receipt, dry_run=args.dry_run)
                if ok:
                    success += 1
                else:
                    failed += 1
                    errors.append((receipt.vendor, "アップロード失敗"))

            await appsider_page.close()
        else:
            print("\n収集できた領収書がありませんでした。")
            success = 0
            failed = 0

        await context.close()
        await browser.close()

    # --- サマリー ---
    print(f"\n{'='*50}")
    print(f"  完了サマリー")
    print(f"{'='*50}")
    print(f"  収集件数 : {len(all_receipts)}")
    for r in all_receipts:
        print(f"    - {r.vendor:12s} {r.date}  ¥{r.amount:>10,}  {r.file_path.name}")

    if not args.dry_run:
        print(f"  アップロード成功: {success} 件")
        print(f"  アップロード失敗: {failed} 件")

    if errors:
        print(f"\n  エラー一覧:")
        for svc, msg in errors:
            print(f"    [{svc}] {msg}")

    print()
    return 1 if errors else 0


def main():
    args = parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
