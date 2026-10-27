import asyncio
import calendar
import os
import re
from datetime import date
from pathlib import Path

from connectors.base import BaseConnector, Receipt

DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads" / "gcp"


class GoogleCloudConnector(BaseConnector):
    """Google Cloud Billing から月次請求書をダウンロードする"""

    async def login(self) -> None:
        print("[GCP] ログイン中...")
        await self.page.goto("https://accounts.google.com/signin")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill('input[type="email"]', self.config["email"])
        await self.page.click("#identifierNext")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill('input[type="password"]', self.config["password"])
        await self.page.click("#passwordNext")
        await self.page.wait_for_load_state("networkidle")

        # 2段階認証が必要な場合
        if "challenge" in self.page.url or "signin/v2/challenge" in self.page.url:
            print("[GCP] 2段階認証が必要です。ブラウザで認証を完了してください（最大2分）")
            await self.page.wait_for_url("**/myaccount.google.com/**", timeout=120_000)

        print("[GCP] ログイン完了")

    async def download_receipts(self, year: int, month: int) -> list[Receipt]:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[GCP] {year}年{month}月の請求書を確認中...")

        billing_url = (
            "https://console.cloud.google.com/billing"
        )
        await self.page.goto(billing_url)
        await self.page.wait_for_load_state("networkidle")

        # 請求書ページへ
        await self.page.goto(f"{billing_url}/invoices")
        await self.page.wait_for_load_state("networkidle")

        receipts: list[Receipt] = []
        month_label = f"{year}/{month:02d}"
        row = self.page.locator(f'tr:has-text("{month_label}"), tr:has-text("{year}年{month}月")')

        if await row.count() == 0:
            print(f"[GCP] {year}年{month}月の請求書が見つかりません")
            return receipts

        pdf_btn = row.first.locator('a[href*=".pdf"], button:has-text("PDF")')
        if await pdf_btn.count() == 0:
            print(f"[GCP] PDF取得リンクが見つかりません")
            return receipts

        out_path = DOWNLOAD_DIR / f"gcp_{year}{month:02d}.pdf"
        async with self.page.expect_download() as dl_info:
            await pdf_btn.first.click()
        download = await dl_info.value
        await download.save_as(out_path)

        amount = await self._parse_row_amount(row.first)
        last_day = calendar.monthrange(year, month)[1]
        receipts.append(
            Receipt(
                vendor="GCP",
                date=date(year, month, last_day),
                amount=amount,
                file_path=out_path,
            )
        )
        print(f"[GCP] ダウンロード完了: {out_path.name} (¥{amount:,})")
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
