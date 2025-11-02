import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = 1
worker_class = 'eventlet'
timeout = 120
keepalive = 5

accesslog = '-'
errorlog = '-'
loglevel = 'info'

preload_app = False
