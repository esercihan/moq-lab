"""Real Streamlit HTTP startup in the Python interpreter running this test."""
import os
from pathlib import Path
import socket
import subprocess
import sys
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import urlopen


def test_real_streamlit_server_starts_and_serves_health_and_page():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    root = Path(__file__).parents[1]
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS='false')
    proc = subprocess.Popen([sys.executable,'-m','streamlit','run','app.py',
        '--server.headless','true','--server.address','127.0.0.1','--server.port',str(port)],
        cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        deadline = monotonic()+15
        while True:
            try:
                with urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                    assert response.status == 200 and response.read() == b'ok'
                break
            except (URLError, TimeoutError):
                if proc.poll() is not None or monotonic() > deadline:
                    raise AssertionError('Streamlit startup failed')
                sleep(.1)
        with urlopen(f'http://127.0.0.1:{port}/',timeout=2) as response:
            assert response.status == 200 and b'<html' in response.read().lower()
    finally:
        proc.terminate()
        try: output,_ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            output,_ = proc.communicate(timeout=5)
        assert 'Traceback' not in output, output
