// 开发用：验证顶栏全局搜索 - 联想下拉 + 点击直达详情页
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
  await page.waitForTimeout(1200);

  // 顶栏搜索框
  const searchInput = page.locator('.header .el-autocomplete input').first();
  await searchInput.click();
  await searchInput.fill('封堵');
  await page.waitForTimeout(900); // 等防抖 + 联想渲染
  await page.screenshot({ path: 'devtools/_shot_gs_dropdown.png' });

  // 点击第一条联想结果 -> 应直达详情页
  await page.locator('.el-autocomplete-suggestion li').first().click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'devtools/_shot_gs_detail.png' });

  await browser.close();
  console.log('gs shots ok');
})().catch(e => { console.error(e.message); process.exit(1); });
