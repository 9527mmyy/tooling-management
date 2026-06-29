const fs = require('fs');
const vm = require('vm');

const makeMockEl = () => ({
    innerHTML: '',
    textContent: '',
    nodeType: 1,
    tagName: 'DIV',
    firstChild: null,
    childNodes: [],
    style: {},
    appendChild() {},
    removeChild() {},
    setAttribute() {},
    getAttribute() { return null; },
    hasAttribute() { return false; },
    removeAttribute() {},
    cloneNode() { return makeMockEl(); },
    content: { appendChild() {}, childNodes: [], insertBefore() {}, firstChild: null },
    insertBefore() {},
    addEventListener() {},
    removeEventListener() {},
    remove() {},
});

(async () => {
    const url = 'https://unpkg.com/vue@3.5.38/dist/vue.global.prod.js';
    const r = await fetch(url);
    const vueSrc = await r.text();
    const augmented = vueSrc + '\n;window.Vue = Vue;';

    const document = {
        createElement: () => makeMockEl(),
        createElementNS: () => makeMockEl(),
        createTextNode: () => ({}),
        createDocumentFragment: () => makeMockEl(),
        createComment: () => ({}),
        querySelector: () => null,
        body: makeMockEl(),
        documentElement: makeMockEl(),
        activeElement: null,
    };
    const ctx = vm.createContext({ window: {}, self: {}, globalThis: {}, document, requestAnimationFrame: (fn) => setTimeout(fn, 0), setTimeout, clearTimeout, Promise, WeakSet, WeakMap, Symbol, Map, Set });
    vm.runInContext(augmented, ctx);
    const Vue = ctx.window.Vue;

    const html = fs.readFileSync('D:/tooling-management/backend/templates/index.html', 'utf-8');
    const m = html.match(/<div id="app">([\s\S]*?)<\/div>\s*<script>/);
    const template = m[1];

    // 二分查找：哪段有问题
    function tryCompile(t) {
        try {
            Vue.compile(t);
            return { ok: true };
        } catch (e) {
            return { ok: false, err: e.message };
        }
    }

    // 简化测试：找包含 `]` 的表达式
    const lines = template.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        // 跳过纯 script 内容
        if (line.match(/=>|function\s*\(|const\s+\w+\s*=/)) continue;
        // 看是否含 `]:`(模板属性结束符)
        if (line.match(/\][^=>]*$/)) {
            // 提取 attribute 内容
            const m2 = line.match(/="([^"]*)"/g);
            if (m2) {
                for (const attr of m2) {
                    const val = attr.slice(2, -1);
                    if (val.includes('=>') || val.includes('[') || val.includes('?') || val.includes('.')) {
                        const test = `<div ${attr}></div>`;
                        const r = tryCompile(test);
                        if (!r.ok) {
                            console.log(`Line ${i+1}: ${attr.slice(0,80)}`);
                            console.log(`  ERROR: ${r.err}`);
                        }
                    }
                }
            }
        }
    }
})();
