# -*- coding: utf-8 -*-
"""
统一的报告/通知本地时间工具。

报告与通知中展示给用户的「生成时间」固定使用 UTC+8（台北/北京），
避免在 UTC 环境（如 GitHub Actions runner）下因 ``datetime.now()`` 取到
系统本地时间而显示成 UTC 时间。
"""

from datetime import datetime, timedelta, timezone

# 报告/通知统一展示时区：UTC+8（台北/北京）
REPORT_TZ = timezone(timedelta(hours=8))


def report_now() -> datetime:
    """返回 UTC+8 时区的当前时间（tz-aware）。"""
    return datetime.now(REPORT_TZ)


def report_now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """返回 UTC+8 当前时间的格式化字符串。"""
    return report_now().strftime(fmt)
