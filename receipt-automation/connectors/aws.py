import asyncio
import calendar
import os
import re
from datetime import date
from pathlib import Path

from connectors.base import BaseConnector, Receipt

DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads" / "aws"


class AWSConnector(BaseConnector):
    """AWS Billing コンソールから月次請求書をダウンロードする"""

    async def login(self) -> None:
        print("[AWS] ログイン中...")
        await self.page.goto("https://signin.aws.amazon.com/signin")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill("#resolving_input", self.config["email"])
        await self.page.click("#next_button")
        await self.page.wait_for_load_state("networkidle")

        await self.page.fill("#ap_password", self.config["password"])
        await self.page.click("#signInSubmit")
        await self.page.wait_for_load_state("networkidle")

        # MFAが要求された場合は手動入力を待機
        if await self.page.locator("#mfa-token-form").count() > 0:
            print("[AWS] MFAコードを入力してください（ブラウザで入力後、Enterキーを押してください）")
            await self.page.wait_for_url("**/console/**", timeout=120_000)

        print("[AWS] ログイン完了")

    async def download_receipts(self, year: int, month: int) -> list[Receipt]:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[AWS] {year}年{month}月の請求書を確認中...")

        await self.page.goto(
            "https://us-east-1.console.aws.amazon.com/billing/home#/bills"
        )
        await self.page.wait_for_load_state("networkidle")

        # 対象月の選択
        month_str = f"{year}-{month:02d}"
        try:
            select = self.page.locator('select[name="date"], [data-testid="date-selector"]')
            if await select.count() > 0:
                await select.select_option(month_str)
                await self.page.wait_for_load_state("networkidle")
        except Exception:
            pass

        # 請求書PDF/CSVのダウンロードリンクを探す
        receipts: list[Receipt] = []
        pdf_link = self.page.locator(
            'a[href*=".pdf"], button:has-text("PDF"), a:has-text("PDF請求書")'
        )

        if await pdf_link.count() == 0:
            print(f"[AWS] {year}年{month}月の請求書が見つかりません")
            return receipts

        out_path = DOWNLOAD_DIR / f"aws_{year}{month:02d}.pdf"
        async with self.page.expect_download() as download_info:
            await pdf_link.first.click()
        download = await download_info.value
        await download.save_as(out_path)

        amount = await self._parse_amount()
        last_day = calendar.monthrange(year, month)[1]
        receipts.append(
            Receipt(
                vendor="AWS",
                date=date(year, month, last_day),
                amount=amount,
                file_path=out_path,
            )
        )
        print(f"[AWS] ダウンロード完了: {out_path.name} (¥{amount:,})")
        await asyncio.sleep(1)
        return receipts

    async def _parse_amount(self) -> int:
        try:
            text = await self.page.locator(
                '[data-testid="total-amount"], .totalAmount, td:has-text("合計")'
            ).first.inner_text()
            nums = re.findall(r"[\d,]+", text)
            if nums:
                return int(nums[-1].replace(",", ""))
        except Exception:
            pass
        return 0
