import asyncio
import calendar
import re
from datetime import date
from pathlib import Path

from connectors.base import BaseConnector, Receipt

DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads" / "notion"


class NotionConnector(BaseConnector):
    """Notion 設定画面から月次請求書をダウンロードする"""

    async def login(self) -> None:
        print("[Notion] ログイン中...")
        await self.page.goto("https://www.notion.so/login")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill('input[name="email"]', self.config["email"])
        await self.page.click('button:has-text("Continue"), button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")

        # パスワードログインの場合
        password_input = self.page.locator('input[name="password"], input[type="password"]')
        if await password_input.count() > 0:
            await password_input.fill(self.config["password"])
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")
        else:
            # メールリンク認証 or 2FA
            print("[Notion] メール認証または2FAが必要です。ブラウザで認証を完了してください（最大2分）")
            await self.page.wait_for_url("**/notion.so/**", timeout=120_000)

        print("[Notion] ログイン完了")

    async def download_receipts(self, year: int, month: int) -> list[Receipt]:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[Notion] {year}年{month}月の請求書を確認中...")

        await self.page.goto("https://www.notion.so/my-integrations")
        await self.page.wait_for_load_state("networkidle")
        await self.page.goto("https://www.notion.so/profile/billing")
        await self.page.wait_for_load_state("networkidle")

        receipts: list[Receipt] = []

        month_label = f"{year}/{month:02d}"
        row = self.page.locator(
            f'tr:has-text("{month_label}"), '
            f'tr:has-text("{year}年{month}月"), '
            f'[data-date*="{year}-{month:02d}"]'
        )

        if await row.count() == 0:
            print(f"[Notion] {year}年{month}月の請求書が見つかりません")
            return receipts

        pdf_btn = row.first.locator(
            'a[href*="invoice"], a:has-text("Download"), a:has-text("PDF"), button:has-text("領収書")'
        )
        if await pdf_btn.count() == 0:
            print(f"[Notion] ダウンロードリンクが見つかりません")
            return receipts

        out_path = DOWNLOAD_DIR / f"notion_{year}{month:02d}.pdf"
        async with self.page.expect_download() as dl_info:
            await pdf_btn.first.click()
        download = await dl_info.value
        await download.save_as(out_path)

        amount = await self._parse_row_amount(row.first)
        last_day = calendar.monthrange(year, month)[1]
        receipts.append(
            Receipt(
                vendor="Notion",
                date=date(year, month, last_day),
                amount=amount,
                file_path=out_path,
            )
        )
        print(f"[Notion] ダウンロード完了: {out_path.name} (¥{amount:,})")
        await asyncio.sleep(1)
        return receipts

    async def _parse_row_amount(self, row) -> int:
        try:
            text = await row.inner_text()
            nums = re.findall(r"[\d,]+", text)
            if nums:
                return int(nums[-1].replace(",", ""))
        except Exception:
            pass
        return 0
