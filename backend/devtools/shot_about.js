// 开发用：截取登录页页脚、侧栏版本号、关于对话框，用于元信息 UI 回归
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' }).catch(() =>
    chromium.launch({ channel: 'chrome' })
  );
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'networkidle' });

  // 1. 登录页（含页脚版权）
  await page.waitForTimeout(800);
  await page.locator('.login-box').screenshot({ path: 'devtools/_shot_login.png' });

  // 登录
  const inputs = page.locator('.login-box input');
  await inputs.nth(0).fill('admin');
  await inputs.nth(1).fill('admin123');
  await page.locator('.login-box button').first().click();
  await page.waitForSelector('.stat-cards', { timeout: 10000 });
  await page.waitForTimeout(1500);

  // 2. 侧栏底部（用户区 + 版本号）
  await page.locator('.sidebar').screenshot({ path: 'devtools/_shot_sidebar.png' });

  // 3. 关于对话框
  await page.locator('.sidebar-version').click();
  await page.waitForTimeout(700);
  await page.screenshot({ path: 'devtools/_shot_about.png' });

  await browser.close();
  console.log('shots ok');
})().catch(e => { console.error(e.message); process.exit(1); });
