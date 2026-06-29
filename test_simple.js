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
    console.log('Vue loaded, compile type:', typeof Vue.compile);

    // 测试 1: 简单模板
    let r1 = Vue.compile('<div>{{ msg }}</div>');
    console.log('Test 1 simple: errors=', r1.errors ? r1.errors.length : 0);

    // 测试 2: arrow function in :formatter
    try {
        let r2 = Vue.compile('<el-table><el-table-column :formatter="(row) => row.role"></el-table-column></el-table>');
        console.log('Test 2 arrow formatter: errors=', r2.errors ? r2.errors.length : 0);
        if (r2.errors) r2.errors.forEach(e => console.log('  -', e.message));
    } catch (e) {
        console.log('Test 2 THROW:', e.message);
    }

    // 测试 3: @current-change with arrow function
    try {
        let r3 = Vue.compile('<el-pagination @current-change="(p) => { x = p }"></el-pagination>');
        console.log('Test 3 arrow @event: errors=', r3.errors ? r3.errors.length : 0);
        if (r3.errors) r3.errors.forEach(e => console.log('  -', e.message));
    } catch (e) {
        console.log('Test 3 THROW:', e.message);
    }

    // 测试 4: function call with index
    try {
        let r4 = Vue.compile('<div>{{ x.split("/")[1] }}</div>');
        console.log('Test 4 split[index]: errors=', r4.errors ? r4.errors.length : 0);
        if (r4.errors) r4.errors.forEach(e => console.log('  -', e.message));
    } catch (e) {
        console.log('Test 4 THROW:', e.message);
    }

    // 测试 5: class binding with method call
    try {
        let r5 = Vue.compile('<div :class="{active: x.startsWith(\'a\')}"></div>');
        console.log('Test 5 startsWith in class: errors=', r5.errors ? r5.errors.length : 0);
        if (r5.errors) r5.errors.forEach(e => console.log('  -', e.message));
    } catch (e) {
        console.log('Test 5 THROW:', e.message);
    }
})();
