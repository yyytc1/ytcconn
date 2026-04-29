"""Example: start the background proxy fetcher and perform a request using a proxy from the queue

This example expects you have a reachable proxy-source URL or you have set a global queue manually.
"""
import time
from ytcconn import Conn, start_proxy_fetcher, stop_proxy_fetcher


def main():
    # replace with a real proxy source URL if available
    source_url = 'http://your-proxy-source.example/api/list'
    start_proxy_fetcher(source_url, interval=5, ttl=60)

    c = Conn()
    # give the fetcher a moment to populate queue (for demo only)
    time.sleep(2)
    c.change_proxy()

    status, text, json_data = c.request('GET', 'https://httpbin.org/ip')
    print('status:', status)
    print('body:', text)

    stop_proxy_fetcher()
    c.close()


if __name__ == '__main__':
    main()
