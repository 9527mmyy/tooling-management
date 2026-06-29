const fs = require('fs');
const path = require('path');

const html = fs.readFileSync('D:/tooling-management/backend/templates/index.html', 'utf-8');
const match = html.match(/<div id="app">([\s\S]*?)<\/div>\s*<script>/);
if (!match) { console.log('NO MATCH'); process.exit(1); }
const template = match[1];

console.log('Template length:', template.length);

// 加载 Vue full build
const vueSrc = fs.readFileSync('D:/tooling-management/backend/static/libs/vue.global.prod.js', 'utf-8');
if (!vueSrc) {
    // 从 CDN 加载
    console.log('No local vue.global.prod.js, downloading from CDN...');
    process.exit(0);
}
