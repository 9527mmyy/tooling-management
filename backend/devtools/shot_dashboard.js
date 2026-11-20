// 开发用：登录后截取首页概览 / 台账页，用于 UI 回归目视检查
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' }).catch(() =>
    chromium.launch({ channel: 'chrome' })
  );
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'networkidle' });

  // 登录
  const inputs = page.locator('.login-box input');
  await inputs.nth(0).fill('admin');
  await inputs.nth(1).fill('admin123');
  await page.locator('.login-box button').first().click();
  await page.waitForSelector('.stat-cards', { timeout: 10000 });
  await page.waitForTimeout(1800);
  await page.screenshot({ path: 'devtools/_shot_dashboard.png' });

  // 台账页
  await page.locator('.menu-item', { hasText: '工装台账' }).first().click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'devtools/_shot_tools.png' });

  await browser.close();
  console.log('shots ok');
})().catch(e => { console.error(e.message); process.exit(1); });
