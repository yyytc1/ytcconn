"""Example: raw mode to obtain the underlying Response object
"""
from ytcconn import Conn


def main():
    c = Conn()
    res = c.request('GET', 'https://httpbin.org/get', raw=True)
    if res is not None:
        try:
            print('status_code:', res.status_code)
            print('text snippet:', res.text[:200])
        finally:
            try:
                res.close()
            except Exception:
                pass
    c.close()


if __name__ == '__main__':
    main()
