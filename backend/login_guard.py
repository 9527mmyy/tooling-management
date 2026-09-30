"""登录失败限流（防密码爆破）
模块：login_guard

背景（2026-09-30 安全审计）：
  登录接口原无任何失败限制 —— 实测连续 12 次错误密码，无 429、无锁定、无延迟。
  而登录账号是**工号**（可枚举），来源又开放给公司内网 + Tailnet，
  因此存在离线可跑的密码爆破面。

设计取舍：
  · 键 =（账号, 来源 IP）。**不按账号单独计数** —— 否则攻击者用别人的工号
    反复失败就能把该账号锁死，把限流变成拒绝服务工具。
  · 阈值 5 次 / 窗口 5 分钟；触发后锁 15 分钟。窗口内不成功即持续累计。
  · 纯内存、进程内有效，服务重启即清空。本应用由 nssm 以**单进程**托管
    （见 AppParameters=app.py），不存在多 worker 计数不一致问题。
  · 失败响应沿用本模块既有的 jsonify({'code': 4xx, 'msg': ...}) 形态
    （HTTP 200 + code!=0），**前端零改动** —— 避免"改了鉴权必须前后端同时上线"的联动风险。
  · 不解析 X-Forwarded-For：本机无反向代理，解析它等于给攻击者一个
    伪造 IP 绕过限流的入口。

⚠️ 本文件与「成本估算系统」的 backend/login_guard.py 是**同源副本**，
   两个系统各自独立部署、无共享包，故有意各存一份。改动请两边同步。
"""
import threading
import time

MAX_FAILURES = 5          # 同一（账号, IP）窗口内允许的失败次数
FAILURE_WINDOW = 300      # 失败计数窗口（秒）
LOCKOUT_SECONDS = 900     # 触发后的锁定时长（秒）
MAX_TRACKED = 5000        # 状态表上限，超出时清理已过期项，防内存无限增长

_lock = threading.Lock()
_state = {}               # key -> [失败次数, 窗口起点ts, 锁定到期ts(0=未锁)]


def _key(account):
    """限流键：账号（大小写归一）+ 来源 IP。"""
    from flask import request
    return f'{(account or "").strip().lower()}|{request.remote_addr or "-"}'


def locked_seconds(account):
    """已被锁定则返回剩余秒数，否则 0。"""
    now = time.time()
    with _lock:
        st = _state.get(_key(account))
        if st and st[2] > now:
            return int(st[2] - now) + 1
        return 0


def remaining_attempts(account):
    """当前窗口内还剩几次可试。未计数/窗口已过期 → MAX_FAILURES；已锁定 → 0。"""
    now = time.time()
    with _lock:
        st = _state.get(_key(account))
        if st is None:
            return MAX_FAILURES
        if st[2] > now:                        # 已锁定
            return 0
        if now - st[1] > FAILURE_WINDOW:       # 窗口过期，重新开始
            return MAX_FAILURES
        return max(0, MAX_FAILURES - st[0])


def register_failure(account):
    """登记一次登录失败。返回 (是否已触发锁定, 剩余可试次数)。"""
    now = time.time()
    k = _key(account)
    with _lock:
        st = _state.get(k)
        # 窗口过期、或上次锁定已到期 → 重新计数
        if st is None or now - st[1] > FAILURE_WINDOW or (st[2] and st[2] <= now):
            st = [0, now, 0.0]
        st[0] += 1
        triggered = st[0] >= MAX_FAILURES
        st[2] = now + LOCKOUT_SECONDS if triggered else 0.0
        _state[k] = st

        if len(_state) > MAX_TRACKED:
            for kk in [x for x, v in _state.items()
                       if v[2] <= now and now - v[1] > FAILURE_WINDOW]:
                _state.pop(kk, None)

        return triggered, max(0, MAX_FAILURES - st[0])


def clear(account):
    """登录成功后清零该键，避免历史失败影响后续登录。"""
    with _lock:
        _state.pop(_key(account), None)


def lockout_message(seconds):
    """统一的锁定提示文案。"""
    minutes = max(1, (seconds + 59) // 60)
    return f'登录失败次数过多，请 {minutes} 分钟后再试'
