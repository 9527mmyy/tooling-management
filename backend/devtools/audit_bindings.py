#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bindings-audit —— 前端模板绑定审计（防"漏写 setup return → 静默失效"）

背景：本项目前端是 Vue3 CDN 无构建单文件 SPA，所有 ref/method 必须出现在
      setup() 末尾的 return {} 中才对模板可见。漏写 → 模板里静默失效、浏览器不报错，
      已多次引发按钮无反应/功能失效。本脚本在改完功能后跑一遍，自动核对
      "模板引用的标识符" 是否都已暴露给模板（在 return 中，或在 setup 内定义）。

用法：
    python backend/devtools/audit_bindings.py
    python backend/devtools/audit_bindings.py backend/templates/index.html

退出码：0 = 无漏写；1 = 发现疑似漏写（建议人工复核）。

注意：脚本基于正则启发式，会过滤常见 JS 全局、Vue/$event、v-for 循环变量等噪声，
      最终仍需人工 judgment。报告里的条目若你确认是循环变量/关键字，可忽略。
"""
import re
import sys
import os

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'templates', 'index.html'
)


def extract_return_keys(content: str) -> set:
    """提取 setup() 末尾 return { ... } 暴露的键。"""
    marker = 'leftColEl, detailRightCard'
    i = content.find(marker)
    if i < 0:
        # 退化：取最后一个 return {
        i = len(content)
    start = content.rfind('return {', 0, i)
    end = content.find('};', i)
    block = content[start:end] if start >= 0 and end > start else ''
    keys = set()
    for k in block.split(','):
        k = k.strip()
        if not k:
            continue
        if ' ' in k:  # 形如 "a as b" 取最后一段
            k = k.split()[-1]
        if re.match(r'^[A-Za-z_$][\w$]*$', k):
            keys.add(k)
    return keys


def extract_local_defs(content: str) -> set:
    """提取 setup 内局部定义的函数/变量名。"""
    names = set(re.findall(r'(?:function|async function)\s+([A-Za-z_$][\w$]*)', content))
    names |= set(re.findall(r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=', content))
    return names


def extract_template_region(content: str) -> str:
    """提取 <body> 到 app 脚本之间的模板 HTML。"""
    ca = content.find('const { createApp')
    script_start = content.rfind('<script>', 0, ca) if ca >= 0 else content.find('<script>')
    body = content.find('<body')
    if script_start < 0 or body < 0:
        return content
    return content[body:script_start]


def collect_referenced(html: str) -> set:
    GLOBALS = set(
        'Object Array Math JSON String Number Boolean Date RegExp Error Promise '
        'console window document localStorage sessionStorage setTimeout setInterval '
        'clearTimeout clearInterval parseInt parseFloat isNaN isFinite axios api '
        'ElMessage ElMessageBox Vue ElementPlus alert confirm prompt true false null '
        'undefined typeof void new delete function return'.split()
    )

    def calls_in(expr):
        e = re.sub(r'["\'][^"\']*["\']', ' ', expr)
        # 忽略方法调用（如 arr.find(）、.map(），只取顶层函数调用
        return set(re.findall(r'(?<![.\w$])(\w+)\s*\(', e))

    def refs_in(expr):
        e = re.sub(r'["\'][^"\']*["\']', ' ', expr)
        # 去掉对象字面量键（如 :class="{active: ...}" 里的 active 是 CSS 类名，不是变量）
        e = re.sub(r'\{\s*[A-Za-z_$][\w$]*\s*:', '{', e)
        return set(re.findall(r'(?:^|[^.\w$])([a-z_$][\w$]*)', e))

    called, refd = set(), set()
    for m in re.finditer(r'@[\w.-]+\s*=\s*["\']([^"\']+)["\']', html):
        called |= calls_in(m.group(1))
    for m in re.finditer(r'v-model\s*=\s*["\']([^"\']+)["\']', html):
        refd |= refs_in(m.group(1))
    for m in re.finditer(r'v-(?:if|else-if|show)\s*=\s*["\']([^"\']+)["\']', html):
        refd |= refs_in(m.group(1))
    for m in re.finditer(r'v-for\s*=\s*["\']([^"\']+)["\']', html):
        mm = re.search(r'\bin\s+([A-Za-z_$][\w$]*)', m.group(1))
        if mm:
            refd.add(mm.group(1))
    for m in re.finditer(r':[\w.-]+\s*=\s*["\']([^"\']+)["\']', html):
        called |= calls_in(m.group(1))
        refd |= refs_in(m.group(1))
    for m in re.finditer(r'\{\{([^}]+)\}\}', html):
        called |= calls_in(m.group(1))
        refd |= refs_in(m.group(1))

    all_refs = (called | refd) - GLOBALS
    # 只保留 camelCase、长度>=2 的候选
    return {x for x in all_refs if re.match(r'^[a-z][A-Za-z0-9_]*$', x) and len(x) >= 2}


# v-for / 作用域局部变量噪声过滤集
LOOP_NOISE = {
    'item', 'row', 'col', 'key', 'index', 'i', 'j', 'k', 'scope', 'node', 'val', 'opt',
    'r', 't', 'v', 'd', 's', 'f', 'e', 'g', 'p', 'c', 'o', 'u', 'b', 'n', 'a', 'm', 'x', 'y',
    'it', 'cur', 'el', 'idx', 'li', 'q', 'w', 'h', 'len', 'total', 'size', 'self', 'that',
    'res', 'data', 'err', 'ok', 'fn', 'cb', 'sub',
}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    if not os.path.isfile(path):
        print(f'文件不存在: {path}')
        sys.exit(2)
    content = open(path, encoding='utf-8').read()

    return_keys = extract_return_keys(content)
    local_defs = extract_local_defs(content)
    html = extract_template_region(content)
    referenced = collect_referenced(html)

    missing = sorted(c for c in referenced if c not in return_keys and c not in LOOP_NOISE)
    # 进一步剔除明显是 CSS 属性名 / HTML 关键字的误报
    CSS_NOISE = {'abs', 'click', 'color', 'field', 'if', 'position', 'att', 'width', 'height',
                 'top', 'left', 'right', 'bottom', 'margin', 'padding', 'border', 'display',
                 'flex', 'grid', 'src', 'href', 'alt', 'title', 'type', 'name', 'value', 'checked'}
    real = [c for c in missing if c not in CSS_NOISE]

    print(f'return 暴露键数 : {len(return_keys)}')
    print(f'模板引用标识符 : {len(referenced)}')
    print('-' * 60)
    if not real:
        print('✅ 未发现疑似漏写（模板引用均已暴露或属循环变量/关键字）。')
        sys.exit(0)
    print(f'⚠️ 疑似漏写（{len(real)} 项，建议人工复核）：')
    for c in real:
        state = 'defined-locally-but-NOT-in-return' if c in local_defs else 'UNDEFINED!!'
        print(f'  {c:32s} [{state}]')
    print('-' * 60)
    print('提示：若某项是 v-for 循环变量或 HTML 属性，可忽略；否则需补进 setup return {}。')
    sys.exit(1)


if __name__ == '__main__':
    main()
