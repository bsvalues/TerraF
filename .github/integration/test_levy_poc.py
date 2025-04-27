import subprocess
import requests
import time
import pytest

@pytest.fixture(scope="session", autouse=True)
def start_servers():
    # 1) Launch Express server
    srv = subprocess.Popen(["npm","--prefix","server","run","dev"])
    # 2) Launch Python bridge
    br = subprocess.Popen(["pipx","run","streamlit","run","packages/streamlit-bridge/src/levy_app.py","--server.port","8501"])
    time.sleep(5)
    yield
    srv.terminate()
    br.terminate()

def test_levy_endpoint():
    r = requests.get("http://localhost:4000/api/v1/levy?propertyId=123")
    assert r.status_code == 200
    assert "amount" in r.json()

def test_streamlit_poc():
    r = requests.get("http://localhost:8501")
    assert r.status_code == 200
    assert "Levy Calculator POC" in r.text