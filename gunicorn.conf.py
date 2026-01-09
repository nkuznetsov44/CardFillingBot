import multiprocessing
import os

bind = "0.0.0.0:5000"
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

preload_app = True
max_requests = 1000
max_requests_jitter = 50

forwarded_allow_ips = "*"
proxy_allow_ips = "*"
