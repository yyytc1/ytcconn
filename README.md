# ytcconn

ytcconn 是一个轻量级的 HTTP 连接与代理管理工具，提供简洁的 Conn 类用于发起请求、切换代理，以及一个可在后台定期抓取代理源并入队的代理抓取器。

以下文档以中文说明如何安装、导入与常见用法，并给出若干可直接复制粘贴的调用示例（包含 PowerShell 命令与 Python 代码示例）。

## 一、安装

推荐在虚拟环境中安装依赖：

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果你从 PyPI 安装（假设已发布为 `ytcconn`）：

```powershell
pip install ytcconn
```

如果你已经将代码发布到 GitHub（例如：https://github.com/yyytc1/ytcconn ），可以直接通过 pip 从 GitHub 安装：

```powershell
# 从主分支安装最新代码
pip install git+https://github.com/yyytc1/ytcconn.git

# 或者指定标签/commit：
pip install git+https://github.com/yyytc1/ytcconn.git@main
```

## 二、快速开始（最小示例）

```python
from ytcconn import Conn, start_proxy_fetcher

# 启动一个后台代理抓取器，定期从给定 URL 获取代理列表并保存到内部队列
start_proxy_fetcher('http://your-proxy-source.example/api/list')

# 创建连接对象并发起简单 GET 请求
c = Conn()
status, text, json_data = c.request('GET', 'https://httpbin.org/get')
print(status)
print(text[:200])

# 关闭连接
c.close()
```

## 三、主要 API 说明

- Conn(proxy=None, log_enable=True, log_trace=True, trust_env=False, proxy_source=None)
  - proxy: 代理地址字符串，形如 `host:port` 或 `username:password@host:port`。如果传入，将用于 requests 的 proxies。
  - trust_env: 是否读取系统代理环境变量（HTTP(S)_PROXY），默认为 False。
  - proxy_source: 如果指定，会在内部自动调用 `start_proxy_fetcher(proxy_source)` 启动后台抓取器。

- request(method, url, *args, timeout=(3,5), return_res=False, raw=False, proxy=True, **kwargs)
  - method: 字符串或 `Method`（例如 `'GET'` 或 `Method.GET`）。
  - raw: 如果为 True，直接返回底层 `requests.Response`（或 cloudscraper 的 Response），不会自动关闭响应；否则函数会尽量解析并在返回前关闭响应。
  - return_res: 当 raw=False 且 return_res=True 时，会把解析后的 status/text/json 与原始 response 一同返回 `(status_code, text, json, res)`。
  - proxy: 是否使用当前设置的代理（True/False）。

- get_proxy(sk5_queue=None)
  - 从全局或传入的队列中弹出一个有效代理（会做简单的连通性检测），返回形如 `host:port` 的字符串，找不到时返回 None。

- change_proxy()
  - 从代理队列中取一个可用代理并应用到当前 Conn 的 `proxies` 中。

- set_headers(key, value) / pop_headers(key)
  - 设置/删除默认请求头。

- close()
  - 关闭底层连接并删除属性。

- start_proxy_fetcher(source_url, interval=1, ttl=30, maxsize=0)
  - 启动一个后台线程，从 `source_url` 拉取代理数据并放入内部全局队列。支持返回 JSON（包含 data 列表）或每行一个代理的纯文本格式。

- stop_proxy_fetcher()
  - 停止后台代理抓取线程。

- set_global_proxy_queue(q)
  - 将自定义的队列设置为全局使用（可传入 `queue.Queue()`）。

## 四、调用示例（进阶）

1) 使用远程代理源并自动切换代理：

```python
from ytcconn import Conn, start_proxy_fetcher, stop_proxy_fetcher
from ytcconn.method import Method

# 启动抓取器（从远程接口读取代理列表）
start_proxy_fetcher('http://your-proxy-source.example/api/list', interval=5, ttl=60)

c = Conn()
# 自动更换代理（主动从全局队列里取）
c.change_proxy()

status, text, json_data = c.request(Method.GET, 'https://httpbin.org/ip')
print('status=', status)
print('body=', text)

# 停止抓取器并关闭连接
stop_proxy_fetcher()
c.close()
```

2) 使用自定义队列（例如：你自己填充的代理列表）：

```python
import queue
from ytcconn import Conn, set_global_proxy_queue

q = queue.Queue()
q.put(('127.0.0.1:8080', 9999999999))  # (proxy, expire_timestamp)
set_global_proxy_queue(q)

c = Conn()
c.change_proxy()
print(c.conn.proxies)
```

3) raw 模式：直接获取底层 Response（需要手动关闭）

```python
from ytcconn import Conn

c = Conn()
res = c.request('GET', 'https://httpbin.org/get', raw=True)
if res is not None:
    print(res.status_code)
    print(res.text[:200])
    res.close()
c.close()
```

### 示例脚本

仓库包含 `examples/` 目录，内含若干可直接运行的示例脚本：

- `examples/example_basic.py`：最小 GET 请求示例
- `examples/example_proxy_fetch.py`：演示如何启动后台代理抓取器并尝试使用代理
- `examples/example_raw.py`：raw 模式示例，直接处理底层 Response

在 PowerShell 中运行示例（假设虚拟环境已激活并在项目根目录）：

```powershell
python examples\example_basic.py
python examples\example_proxy_fetch.py
python examples\example_raw.py
```

## 五、注意事项与常见问题

- cloudscraper: 本项目使用 `cloudscraper` 创建请求对象以提高对某些站点的兼容性，请参考 `requirements.txt` 中列出的依赖。
- 代理格式：抓取到的代理可能包含不同分隔符（`:`、`/`、`|`），`get_proxy` 会尝试处理常见格式。
- 后台抓取器会将每个代理与一个过期时间（ttl）一起放入队列，`get_proxy` 会跳过已过期的记录。
- raw=True 时会返回原始 Response，请在使用完后手动 `close()`，否则可能造成连接泄漏。

## 六、快速测试（PowerShell）

复制下面命令在 PowerShell 中运行（假设你已激活虚拟环境并在项目根目录）：

```powershell
python -c "from ytcconn import Conn; c=Conn(); s,t,j=c.request('GET','https://httpbin.org/get'); print(s); c.close()"
```

## 七、许可证

请参见项目根目录中的 `LICENSE`。

---

如果需要，我可以把示例拆成独立的示例脚本文件或补充单元测试来验证常见调用。欢迎告诉我你更希望的示例场景（例如某个代理源的响应格式）。
# ytcconn

A lightweight connection and proxy manager.

Quick usage:

```python
from ytcconn import Conn, start_proxy_fetcher

# Start background proxy fetcher from a URL
start_proxy_fetcher('http://your-proxy-source.example/api/list')

c = Conn()
# Use c.get_proxy() or c.change_proxy()
```
