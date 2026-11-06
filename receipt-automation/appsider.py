import asyncio
import os
from pathlib import Path

from playwright.async_api import Page

from connectors.base import Receipt

APPSIDER_URL = os.getenv("APPSIDER_URL", "https://app.appsider.jp")
APPSIDER_EMAIL = os.getenv("APPSIDER_EMAIL", "")
APPSIDER_PASSWORD = os.getenv("APPSIDER_PASSWORD", "")


class AppSiderUploader:
    def __init__(self, page: Page):
        self.page = page

    async def login(self) -> None:
        print("[AppSider] ログイン中...")
        await self.page.goto(APPSIDER_URL)
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill('input[type="email"], input[name="email"]', APPSIDER_EMAIL)
        await self.page.fill('input[type="password"], input[name="password"]', APPSIDER_PASSWORD)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        print("[AppSider] ログイン完了")

    async def upload_receipt(self, receipt: Receipt, dry_run: bool = False) -> bool:
        print(f"[AppSider] {receipt.vendor} {receipt.date} ¥{receipt.amount:,} の領収書をアップロード中...")

        if dry_run:
            print(f"  [dry-run] スキップ: {receipt.file_path.name}")
            return True

        try:
            await self._navigate_to_payments(receipt)
            await self._attach_file(receipt)
            print(f"  ✓ アップロード成功: {receipt.file_path.name}")
            return True
        except Exception as e:
            print(f"  ✗ アップロード失敗: {e}")
            return False

    async def _navigate_to_payments(self, receipt: Receipt) -> None:
        # 決済一覧ページへ遷移（AppSiderの実際のURLに合わせて調整）
        payments_url = f"{APPSIDER_URL}/payments"
        if self.page.url != payments_url:
            await self.page.goto(payments_url)
            await self.page.wait_for_load_state("networkidle")

        # 年月でフィルタリング（月次フィルターが存在する場合）
        year = receipt.date.year
        month = receipt.date.month
        try:
            # 日付フィルター（AppSiderのUI要素に合わせて調整）
            month_filter = self.page.locator(
                f'[data-year="{year}"][data-month="{month}"], '
                f'select[name="month"] option[value="{year}-{month:02d}"]'
            )
            if await month_filter.count() > 0:
                await month_filter.first.click()
                await self.page.wait_for_load_state("networkidle")
        except Exception:
            pass  # フィルターが見つからない場合はそのまま続行

    async def _attach_file(self, receipt: Receipt) -> None:
        # vendor名または金額でテーブル行を特定する
        vendor_aliases = {
            "AWS": ["Amazon Web Services", "AWS", "amazon web services"],
            "GCP": ["Google Cloud", "Google", "GCP"],
            "Slack": ["Slack"],
            "Notion": ["Notion"],
        }
        search_terms = vendor_aliases.get(receipt.vendor, [receipt.vendor])

        row = None
        for term in search_terms:
            candidates = self.page.locator(f'tr:has-text("{term}")')
            if await candidates.count() > 0:
                # 同じvendorが複数行ある場合、金額で絞り込む
                count = await candidates.count()
                for i in range(count):
                    candidate = candidates.nth(i)
                    text = await candidate.inner_text()
                    amount_str = f"{receipt.amount:,}".replace(",", "")
                    if amount_str in text.replace(",", ""):
                        row = candidate
                        break
                if row is None:
                    row = candidates.first
                break

        if row is None:
            raise ValueError(
                f"AppSiderで該当行が見つかりません: {receipt.vendor} ¥{receipt.amount:,} ({receipt.date})"
            )

        # 「領収書添付」ボタンをクリック
        attach_btn = row.locator(
            'button:has-text("領収書"), button:has-text("添付"), [aria-label*="領収書"], [title*="領収書"]'
        )
        if await attach_btn.count() == 0:
            # 行を選択して詳細を開く場合
            await row.click()
            await self.page.wait_for_load_state("networkidle")
            attach_btn = self.page.locator(
                'button:has-text("領収書"), button:has-text("添付"), [aria-label*="領収書"]'
            )

        await attach_btn.first.click()

        # ファイル入力にセット
        file_input = self.page.locator('input[type="file"]')
        await file_input.wait_for(state="attached", timeout=5000)
        await file_input.set_input_files(str(receipt.file_path))

        # アップロード確定ボタン（存在する場合）
        confirm_btn = self.page.locator(
            'button:has-text("アップロード"), button:has-text("保存"), button:has-text("確定"), button[type="submit"]'
        )
        if await confirm_btn.count() > 0:
            await confirm_btn.first.click()
            await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
