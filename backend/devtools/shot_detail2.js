// 开发用：登录 → 台账 → 打开第二条工装详情 → 截顶部标题栏（验证厂家行渲染）
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' }).catch(() =>
    chromium.launch({ channel: 'chrome' })
  );
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'networkidle' });

  const inputs = page.locator('.login-box input');
  await inputs.nth(0).fill('admin');
  await inputs.nth(1).fill('admin123');
  await page.locator('.login-box button').first().click();
  await page.waitForSelector('.stat-cards', { timeout: 10000 });

  await page.locator('.menu-item', { hasText: '工装台账' }).first().click();
  await page.waitForSelector('.el-table__row', { timeout: 10000 });
  await page.waitForTimeout(800);

  // 跳到第 2 页找一条有厂家数据的工装（首页前几条往往是测试数据）
  const pager = page.locator('.el-pagination .btn-next');
  if (await pager.count()) {
    await pager.click();
    await page.waitForTimeout(1200);
  }

  // 取当前页第一条非"11111"的工装
  const rows = page.locator('.el-table__row');
  const count = await rows.count();
  let picked = false;
  for (let i = 0; i < count; i++) {
    const text = await rows.nth(i).innerText();
    if (!text.includes('11111') && !text.includes('test')) {
      const btn = rows.nth(i).locator('button:has-text("详情"), a:has-text("详情")');
      if (await btn.count()) await btn.first().click(); else await rows.nth(i).click();
      picked = true; break;
    }
  }
  if (!picked) {
    const btn = rows.first().locator('button:has-text("详情"), a:has-text("详情")');
    if (await btn.count()) await btn.first().click(); else await rows.first().click();
  }

  await page.waitForSelector('.tool-status-pill', { timeout: 10000 });
  await page.waitForTimeout(1200);

  await page.screenshot({ path: 'devtools/_shot_detail2_full.png', clip: { x: 0, y: 0, width: 1440, height: 220 } });

  await browser.close();
  console.log('shots ok');
})().catch(e => { console.error(e.message); process.exit(1); });