import asyncio
import calendar
import re
from datetime import date
from pathlib import Path

from connectors.base import BaseConnector, Receipt

DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads" / "slack"


class SlackConnector(BaseConnector):
    """Slack 管理画面から月次請求書をダウンロードする"""

    async def login(self) -> None:
        print("[Slack] ログイン中...")
        workspace = self.config.get("workspace", "")
        if workspace:
            await self.page.goto(f"https://{workspace}.slack.com/sign_in_with_password")
        else:
            await self.page.goto("https://slack.com/signin")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill('input[name="email"], #email', self.config["email"])
        await self.page.fill('input[name="password"], #password', self.config["password"])
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")

        # 2FAが必要な場合
        if await self.page.locator('[data-qa="two_factor_input"]').count() > 0:
            print("[Slack] 2段階認証が必要です。ブラウザで認証を完了してください（最大2分）")
            await self.page.wait_for_url("**/client/**", timeout=120_000)

        print("[Slack] ログイン完了")

    async def download_receipts(self, year: int, month: int) -> list[Receipt]:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[Slack] {year}年{month}月の請求書を確認中...")

        workspace = self.config.get("workspace", "")
        if workspace:
            billing_url = f"https://{workspace}.slack.com/admin/billing"
        else:
            billing_url = "https://slack.com/admin/billing"

        await self.page.goto(billing_url)
        await self.page.wait_for_load_state("networkidle")

        receipts: list[Receipt] = []

        # 請求履歴テーブルを探す
        month_label = f"{year}/{month:02d}"
        row = self.page.locator(
            f'tr:has-text("{month_label}"), '
            f'tr:has-text("{year}年{month}月"), '
            f'tr:has-text("{month:02d}/{year}")'
        )

        if await row.count() == 0:
            print(f"[Slack] {year}年{month}月の請求書が見つかりません")
            return receipts

        pdf_btn = row.first.locator(
            'a[href*="invoice"], a:has-text("PDF"), a:has-text("Download"), button:has-text("領収書")'
        )
        if await pdf_btn.count() == 0:
            print(f"[Slack] ダウンロードリンクが見つかりません")
            return receipts

        out_path = DOWNLOAD_DIR / f"slack_{year}{month:02d}.pdf"
        async with self.page.expect_download() as dl_info:
            await pdf_btn.first.click()
        download = await dl_info.value
        await download.save_as(out_path)

        amount = await self._parse_row_amount(row.first)
        last_day = calendar.monthrange(year, month)[1]
        receipts.append(
            Receipt(
                vendor="Slack",
                date=date(year, month, last_day),
                amount=amount,
                file_path=out_path,
            )
        )
        print(f"[Slack] ダウンロード完了: {out_path.name} (¥{amount:,})")
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
