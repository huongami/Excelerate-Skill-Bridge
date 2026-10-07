"""A very small Chrome DevTools Protocol client (standard library only), to drive a real browser in tests.

It starts Chrome (or Edge) in headless mode with its own temporary profile, opens one page, and lets a test
navigate, run JavaScript, wait for a condition, set a file in a file input, and take a screenshot.
Console errors, uncaught exceptions and CSP violations are collected, so that a test can assert there are none.
"""
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from typing import Any, Dict, List, Optional

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]


def find_browser() -> Optional[str]:
    return os.environ.get("JINDER_BROWSER") or next((p for p in CANDIDATES if os.path.exists(p)), None)


class WebSocket:
    """A client for RFC 6455 text messages. Enough for the DevTools protocol."""

    def __init__(self, url: str):
        assert url.startswith("ws://")
        host_port, _, path = url[5:].partition("/")
        host, _, port = host_port.partition(":")
        self.sock = socket.create_connection((host, int(port)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("The browser closed the connection")
            head += chunk
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise ConnectionError(head.decode(errors="replace"))
        self._buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise ConnectionError("The browser closed the connection")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def send(self, text: str) -> None:
        data = text.encode()
        header = bytearray([0x81])
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + masked)

    def recv(self, timeout: float = 30) -> Optional[str]:
        self.sock.settimeout(timeout)
        message = b""
        while True:
            b1, b2 = self._read(2)
            opcode = b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            if opcode == 0x8:
                return None
            if opcode == 0x9:  # ping
                self.sock.sendall(bytes([0x8A, 0x80]) + os.urandom(4))
                continue
            message += payload
            if b1 & 0x80:
                return message.decode("utf-8", errors="replace")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class Browser:
    def __init__(self, width: int = 1280, height: int = 900, port: int = 0):
        exe = find_browser()
        if not exe:
            raise RuntimeError("No Chrome or Edge was found. Set JINDER_BROWSER to the browser program.")
        self.profile = tempfile.mkdtemp(prefix="jinder-browser-")
        if not port:  # a free port, so that a browser that is still closing never gets in the way
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
        self.port = port
        self.proc = subprocess.Popen(
            [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", f"--remote-debugging-port={port}",
             f"--user-data-dir={self.profile}", f"--window-size={width},{height}", "--hide-scrollbars", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.events: List[Dict[str, Any]] = []
        self.problems: List[str] = []
        self._id = 0
        deadline = time.time() + 30
        target = None
        while time.time() < deadline and not target:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2) as r:
                    pages = [t for t in json.load(r) if t.get("type") == "page"]
                    target = pages[0] if pages else None
            except OSError:
                time.sleep(0.3)
        if not target:
            self.close()
            raise RuntimeError("The browser did not start")
        self.ws = WebSocket(target["webSocketDebuggerUrl"])
        for domain in ("Page", "Runtime", "Log", "DOM", "Network"):
            self.call(f"{domain}.enable")
        self.call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})

    # ----- protocol -----
    def call(self, method: str, params: Optional[dict] = None, timeout: float = 30) -> dict:
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self.ws.recv(max(0.1, deadline - time.time()))
            if raw is None:
                raise ConnectionError("The browser closed the page")
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            self._event(msg)
        raise TimeoutError(method)

    def _event(self, msg: dict) -> None:
        m = msg.get("method")
        if not m:
            return
        p = msg.get("params", {})
        if m == "Runtime.exceptionThrown":
            d = p["exceptionDetails"]
            self.problems.append("exception: " + (d.get("exception", {}).get("description") or d.get("text", "")))
        elif m == "Runtime.consoleAPICalled" and p.get("type") in ("error", "assert"):
            self.problems.append("console." + p["type"] + ": " + " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", [])))
        elif m == "Log.entryAdded" and p["entry"].get("level") == "error":
            e = p["entry"]
            self.problems.append(f"log: {e.get('text')} {e.get('url', '')}")
        self.events.append(msg)

    def pump(self, seconds: float = 0.2) -> None:
        end = time.time() + seconds
        while time.time() < end:
            try:
                raw = self.ws.recv(max(0.05, end - time.time()))
            except (socket.timeout, TimeoutError):
                return
            if raw is None:
                return
            self._event(json.loads(raw))

    # ----- helpers for tests -----
    def goto(self, url: str) -> None:
        self.call("Page.navigate", {"url": url})
        self.wait_for("document.readyState === 'complete'")
        self.pump(0.3)

    def eval(self, expression: str, await_promise: bool = True) -> Any:
        res = self.call("Runtime.evaluate", {"expression": expression, "awaitPromise": await_promise, "returnByValue": True, "timeout": 25000}, timeout=30)
        if "exceptionDetails" in res:
            d = res["exceptionDetails"]
            raise RuntimeError("JS error: " + (d.get("exception", {}).get("description") or d.get("text", "")))
        return res["result"].get("value")

    def wait_for(self, condition: str, timeout: float = 15) -> None:
        end = time.time() + timeout
        last = None
        while time.time() < end:
            try:
                if self.eval(f"Boolean({condition})", await_promise=False):
                    return
            except RuntimeError as exc:
                last = exc
            self.pump(0.15)
        raise TimeoutError(f"Timed out waiting for: {condition} ({last})")

    def text(self, selector: str = "body") -> str:
        return self.eval(f"(document.querySelector({json.dumps(selector)}) || {{}}).innerText || ''", await_promise=False)

    def click(self, selector: str) -> None:
        self.wait_for(f"document.querySelector({json.dumps(selector)})")
        self.eval(f"document.querySelector({json.dumps(selector)}).click()", await_promise=False)
        self.pump(0.2)

    def click_text(self, tag: str, text: str) -> None:
        self.wait_for(f"[...document.querySelectorAll({json.dumps(tag)})].some(e => e.innerText.trim() === {json.dumps(text)} && !e.disabled)")
        self.eval(f"[...document.querySelectorAll({json.dumps(tag)})].find(e => e.innerText.trim() === {json.dumps(text)} && !e.disabled).click()", await_promise=False)
        self.pump(0.2)

    def fill(self, selector: str, value: str) -> None:
        self.wait_for(f"document.querySelector({json.dumps(selector)})")
        self.eval(f"""(() => {{ const el = document.querySelector({json.dumps(selector)}); el.focus();
          const set = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value').set; set.call(el, {json.dumps(value)});
          el.dispatchEvent(new Event('input', {{bubbles: true}})); el.dispatchEvent(new Event('change', {{bubbles: true}})); }})()""", await_promise=False)

    def set_file(self, selector: str, path: str) -> None:
        doc = self.call("DOM.getDocument", {"depth": 0})
        node = self.call("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": selector})
        self.call("DOM.setFileInputFiles", {"files": [path], "nodeId": node["nodeId"]})
        self.pump(0.3)

    def screenshot(self, path: str, full: bool = False) -> None:
        params = {"format": "png"}
        if full:
            size = self.eval("({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})", await_promise=False)
            params.update({"captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": size["w"], "height": size["h"], "scale": 1}})
        data = self.call("Page.captureScreenshot", params, timeout=60)["data"]
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))

    def take_problems(self) -> List[str]:
        self.pump(0.3)
        out, self.problems = self.problems, []
        return out

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)
