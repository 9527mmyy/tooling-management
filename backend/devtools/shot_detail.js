// 开发用：登录 → 工装台账 → 打开第一条工装的详情页 → 截取顶部标题栏与状态徽标
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

  // 工装台账
  await page.locator('.menu-item', { hasText: '工装台账' }).first().click();
  await page.waitForSelector('.el-table__row', { timeout: 10000 });
  await page.waitForTimeout(800);

  // 点第一条工装（默认"详情"操作或行点击）
  const firstRow = page.locator('.el-table__row').first();
  const hasViewBtn = await firstRow.locator('button:has-text("详情"), a:has-text("详情")').count();
  if (hasViewBtn) {
    await firstRow.locator('button:has-text("详情"), a:has-text("详情")').first().click();
  } else {
    await firstRow.click();
  }

  // 等待详情页
  await page.waitForSelector('.tool-status-pill', { timeout: 10000 });
  await page.waitForTimeout(1200);

  // 截全屏 + 仅顶部标题栏
  await page.screenshot({ path: 'devtools/_shot_detail_full.png' });
  await page.locator('div').filter({ has: page.locator('.tool-status-pill') }).first()
    .screenshot({ path: 'devtools/_shot_detail_header.png' }).catch(async () => {
      // fallback: 截 viewport 顶部 200px
      await page.screenshot({ path: 'devtools/_shot_detail_header.png', clip: { x: 0, y: 0, width: 1440, height: 220 } });
    });

  await browser.close();
  console.log('shots ok');
})().catch(e => { console.error(e.message); process.exit(1); });