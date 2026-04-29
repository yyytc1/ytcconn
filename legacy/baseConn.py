"""Backup of original root-level baseConn.py"""

# The original root-level `baseConn.py` was a compatibility wrapper.
from importlib import import_module

_pkg = import_module('ytcconn')

# Re-export common names
Conn = _pkg.Conn
start_proxy_fetcher = _pkg.start_proxy_fetcher
stop_proxy_fetcher = _pkg.stop_proxy_fetcher
set_global_proxy_queue = _pkg.set_global_proxy_queue

__all__ = ['Conn', 'start_proxy_fetcher', 'stop_proxy_fetcher', 'set_global_proxy_queue']
