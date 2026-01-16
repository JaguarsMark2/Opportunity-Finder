"""Gunicorn configuration for production deployment."""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Process naming
proc_name = "opportunity-finder"

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# SSL (if using SSL directly with gunicorn)
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"

# Process management
daemon = False
pidfile = "/var/run/gunicorn/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# Server mechanics
sendfile = True
reuse_port = True
chdir = "/app"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Gunicorn server...")

def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Spawning workers")

def on_exit(server):
    """Called just before exiting."""
    print("Gunicorn server is shutting down...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forked child, re-executing.")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker {worker.pid} exited with status {worker.status}")
