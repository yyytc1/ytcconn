"""Compatibility wrapper for the Method enum/class.

Delegates to the package implementation so existing imports like
`from method import Method` continue to work.
"""

from importlib import import_module

_pkg = import_module('ytcconn')

Method = _pkg.Method

__all__ = ['Method']
