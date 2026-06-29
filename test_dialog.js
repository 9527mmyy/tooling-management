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

    const tests = [
        '<el-dialog v-model="x" :title="(a ? \'编辑\' : \'新增\') + \' \' + (names[tab] || \'\')" width="400px"></el-dialog>',
        '<el-dialog v-model="x" :title="a ? \'编辑\' : (\'新增\' + names[tab])" width="400px"></el-dialog>',
        '<el-dialog v-model="x" :title="a ? \'编辑\' : \'新增\' + names[tab]" width="400px"></el-dialog>',
        '<div :title="(a ? \'编辑\' : \'新增\') + names[tab]"></div>',
        '<div>{{ names[tab] }}</div>',
    ];

    for (let i = 0; i < tests.length; i++) {
        try {
            const r = Vue.compile(tests[i]);
            console.log(`Test ${i+1}: errors=${r.errors ? r.errors.length : 0}`);
            if (r.errors) r.errors.forEach(e => console.log('  -', e.message));
        } catch (e) {
            console.log(`Test ${i+1} THROW: ${e.message}`);
        }
    }
})();
