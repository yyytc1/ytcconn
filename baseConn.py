# coding : utf-8
# @Time : 2025/8/26 21:40 
# @Author : Adolph
# @File : baseConn.py
# @Software : PyCharm
"""Compatibility wrapper: expose package API at top-level module for
backwards compatibility with scripts that import `baseConn` directly.

This file delegates symbol access to the installed package `ytcconn`.
"""

from importlib import import_module

_pkg = import_module('ytcconn')

# Re-export common names
Conn = _pkg.Conn
start_proxy_fetcher = _pkg.start_proxy_fetcher
stop_proxy_fetcher = _pkg.stop_proxy_fetcher
set_global_proxy_queue = _pkg.set_global_proxy_queue

__all__ = ['Conn', 'start_proxy_fetcher', 'stop_proxy_fetcher', 'set_global_proxy_queue']

	