"""Basic example: simple GET request using Conn
"""
from ytcconn import Conn


def main():
    c = Conn()
    status, text, json_data = c.request('GET', 'https://httpbin.org/get')
    print('status:', status)
    print('body snippet:', (text or '')[:200])
    c.close()


if __name__ == '__main__':
    main()
