# coding : utf-8
# This file is copied into the package directory by the packaging helper.

import queue
import socket
import traceback
import threading
import json
from typing import Tuple, Union, Optional
from requests import Response
import cloudscraper
import time

from loguru import logger

from method import Method

_GLOBAL_PROXY_QUEUE = None

_GLOBAL_PROXY_THREAD = None
_GLOBAL_PROXY_STOP_EVENT = None


def set_global_proxy_queue(q):
	global _GLOBAL_PROXY_QUEUE
	_GLOBAL_PROXY_QUEUE = q


def _queue_contains_proxy(q, proxy_str):
	try:
		with q.mutex:
			for item in list(q.queue):
				if not item:
					continue
				try:
					if item[0] == proxy_str:
						return True
				except Exception:
					if item == proxy_str:
						return True
	except Exception:
		return False
	return False


def start_proxy_fetcher(source_url, interval=1, ttl=30, maxsize=0):
	global _GLOBAL_PROXY_QUEUE, _GLOBAL_PROXY_THREAD, _GLOBAL_PROXY_STOP_EVENT
	if _GLOBAL_PROXY_THREAD is not None and _GLOBAL_PROXY_THREAD.is_alive():
		return
	
	if _GLOBAL_PROXY_QUEUE is None:
		_GLOBAL_PROXY_QUEUE = queue.Queue(maxsize=maxsize)
	
	_GLOBAL_PROXY_STOP_EVENT = threading.Event()
	
	def _fetch_loop():
		conn = Conn(proxy=None, trust_env=False)
		while not _GLOBAL_PROXY_STOP_EVENT.is_set():
			try:
				# if queue already has items, wait a bit
				try:
					if _GLOBAL_PROXY_QUEUE.qsize() > 0:
						time.sleep(interval)
						continue
				except Exception:
					pass
				
				res = None
				try:
					res = conn.request('GET', source_url, timeout=10, raw=True, proxy=False)
				except Exception:
					res = None
				
				if res is None:
					time.sleep(interval)
					continue
				
				try:
					status = getattr(res, 'status_code', None)
					if status == 200:
						data = res.text
						if 'data' in data:
							try:
								parsed = json.loads(data)
							except Exception:
								parsed = None
							if parsed:
								for i in parsed.get('data', []):
									try:
										p = f"{i['ip']}:{i['port']}"
									except Exception:
										continue
									if not _queue_contains_proxy(_GLOBAL_PROXY_QUEUE, p):
										_GLOBAL_PROXY_QUEUE.put((p, int(time.time()) + ttl))
						else:
							for line in data.split('\r\n'):
								line = line.strip()
								if not line:
									continue
								if not _queue_contains_proxy(_GLOBAL_PROXY_QUEUE, line):
									_GLOBAL_PROXY_QUEUE.put((line, int(time.time()) + ttl))
				finally:
					try:
						res.close()
					except Exception:
						pass
				
				time.sleep(interval)
			except Exception:
				try:
					time.sleep(interval)
				except Exception:
					pass
	
	_GLOBAL_PROXY_THREAD = threading.Thread(target=_fetch_loop, daemon=True)
	_GLOBAL_PROXY_THREAD.start()


def stop_proxy_fetcher():
	"""Stop the background proxy fetcher if it's running."""
	global _GLOBAL_PROXY_THREAD, _GLOBAL_PROXY_STOP_EVENT
	if _GLOBAL_PROXY_STOP_EVENT is not None:
		_GLOBAL_PROXY_STOP_EVENT.set()
	if _GLOBAL_PROXY_THREAD is not None:
		try:
			_GLOBAL_PROXY_THREAD.join(timeout=2)
		except Exception:
			pass
	_GLOBAL_PROXY_THREAD = None
	_GLOBAL_PROXY_STOP_EVENT = None


class Conn:
	def __init__(self, proxy=None, log_enable=True, log_trace=True, log_depth=2, trust_env=False, proxy_source=None):
		"""
		:param proxy: 代理地址，格式为 username:password@host:port 或 host:port
		:param token: Bearer Token，可选
		"""
		self.proxy = proxy
		self.log_enable = log_enable
		self.log_trace = log_trace
		self.log_depth = log_depth
		self.working = True
		self.trust_env = trust_env
		if proxy_source:
			start_proxy_fetcher(proxy_source)
		self.init_conn()
	
	def init_conn(self):
		self.conn = cloudscraper.create_scraper(
			browser={
				'browser': 'chrome',
				'platform': 'windows',
				'mobile': False
			}
		)
		self.conn.trust_env = self.trust_env
		
		# 设置代理
		if self.proxy:
			self.conn.proxies = {
				"http": f"http://{self.proxy}",
				"https": f"http://{self.proxy}"
			}
	
	def set_headers(self, key, value):
		if self.conn.headers is None:
			self.conn.headers = {}
		self.conn.headers[key] = value
	
	def pop_headers(self, key):
		if isinstance(self.conn.headers, dict):
			if key in self.conn.headers:
				self.conn.headers.pop(key)
	
	def request(
		self,
		method: Union[Method.POST, Method.GET, str],
		url: str,
		*args,
		timeout=(3, 5),
		return_res=False,
		raw=True,
		proxy=True,
		**kwargs
	) -> Union[
		Optional[Response],
		Tuple[Optional[int], Optional[str], Optional[dict]],
		Tuple[Optional[int], Optional[str], Optional[dict], Optional[Response]]
	]:
		status_code, t, j, res = None, None, None, None
		try:
			# 强制短连接，减少连接占用
			h = kwargs.get('headers', {})
			h['Connection'] = 'close'
			kwargs['headers'] = h
			
			if raw:
				try:
					if proxy and self.proxy:
						kwargs['proxies'] = self.proxy
					else:
						kwargs['proxies'] = None
					res = self.conn.request(method, url=url, timeout=timeout, *args, **kwargs)
				except:
					res = None
				return res
			
			# 非 raw 模式：解析 status/text/json，并确保关闭 res
			try:
				if proxy and self.proxy:
					kwargs['proxies'] = self.proxy
				else:
					kwargs['proxies'] = None
				res = self.conn.request(method, url=url, timeout=timeout, *args, **kwargs)
			except:
				res = None
			
			if res is None:
				if return_res:
					return status_code, t, j, res
				return status_code, t, j
			
			status_code = getattr(res, 'status_code', None)
			try:
				t = res.text
			except:
				t = None
			try:
				j = res.json()
			except:
				j = None
			
			if return_res:
				return status_code, t, j, res
			return status_code, t, j
		finally:
			# 非 raw 模式下，无论是否 return_res，都在返回前尝试关闭 res（与原 request_ 保持一致）
			try:
				if res is not None:
					res.close()
			except:
				pass
	
	def close(self):
		try:
			self.conn.close()
		except:
			pass
		try:
			del self.conn
		except:
			pass
	
	def log(self, message):
		if self.working and self.log_enable:
			if self.log_depth > 1:
				logger.opt(depth=self.log_depth).info(message)
			else:
				logger.info(f'{message}')
	
	def y_sleep(self, times):
		for i in range(times):
			try:
				if not self.working:
					break
				time.sleep(1)
			except:
				pass
	
	def tcp_alive(self, ip, port, timeout=2):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.settimeout(timeout)
				return s.connect_ex((ip, port)) == 0
		except:
			if self.log_trace:
				self.log(traceback.format_exc())
	
	def get_proxy(self, sk5_queue=None):
		q = sk5_queue if sk5_queue is not None else _GLOBAL_PROXY_QUEUE
		if q is None:
			return None
		
		while self.working:
			try:
				sk5, end_time = q.get(timeout=1)
			except queue.Empty:
				continue
			try:
				if int(time.time()) >= end_time:
					continue
			except Exception:
				continue
			
			if sk5 in ['None', None, '']:
				continue
			
			if '|' in sk5:
				base_str = '|'
			elif '/' in sk5:
				base_str = '/'
			else:
				base_str = ':'
			
			parts = sk5.replace('\n', '').split(base_str)
			if len(parts) < 2:
				continue
			host = parts[0]
			try:
				port = int(parts[1])
			except Exception:
				continue
			
			if not self.tcp_alive(host, port):
				continue
			return f'{host}:{port}'
	
	def change_proxy(self):
		proxy = self.get_proxy()
		if not proxy:
			return
		self.conn.proxies = {
			"http": f"http://{proxy}",
			"https": f"http://{proxy}"
		}
