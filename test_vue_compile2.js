const fs = require('fs');

// 加载 Vue 3 full build（用 eval 方式注入到 vm）
const vueSrc = fs.readFileSync('D:/tooling-management/backend/static/libs/vue.min.js', 'utf-8');
const ctx = { module: { exports: {} }, exports: {} };
const fn = new Function('module', 'exports', 'window', 'document', 'self', 'globalThis', vueSrc + '\nreturn window.Vue || module.exports || self.Vue || globalThis.Vue;');
const Vue = fn(ctx.module, ctx.exports, {}, {}, {}, {});
console.log('Vue loaded:', !!Vue, 'createApp:', !!Vue.createApp, 'compile:', !!Vue.compile);

// 提取模板
const html = fs.readFileSync('D:/tooling-management/backend/templates/index.html', 'utf-8');
const m = html.match(/<div id="app">([\s\S]*?)<\/div>\s*<script>/);
if (!m) { console.log('NO TEMPLATE MATCH'); process.exit(1); }
const template = m[1];

// 尝试编译
try {
    const r = Vue.compile(template);
    console.log('OK - compiled successfully');
    console.log('Has errors:', r.errors && r.errors.length);
    if (r.errors && r.errors.length) console.log('Errors:', r.errors);
} catch (e) {
    console.log('COMPILE ERROR:', e.message);
    console.log(e.stack);
}
