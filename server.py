import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")


class ChatHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            try:
                with urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as response:
                    tags = json.load(response)
                models = [item.get("name", "") for item in tags.get("models", [])]
                self.send_json(200, {"connected": True, "model": MODEL, "models": models})
            except (HTTPError, URLError, TimeoutError, OSError) as error:
                self.send_json(503, {"connected": False, "model": MODEL, "error": str(error)})
            return

        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        content = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 1_000_000:
                self.send_json(400, {"error": "Request body must be between 1 byte and 1 MB."})
                return
            data = json.loads(self.rfile.read(size))
            messages = data.get("messages")
            if not isinstance(messages, list) or not messages:
                self.send_json(400, {"error": "A non-empty messages array is required."})
                return

            payload = json.dumps(
                {"model": MODEL, "messages": messages, "stream": False}
            ).encode("utf-8")
            request = Request(
                f"{OLLAMA_URL}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=300) as response:
                result = json.load(response)
            message = result.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                self.send_json(502, {"error": "Ollama returned an unexpected response."})
                return
            self.send_json(200, {"message": message})
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self.send_json(400, {"error": "Request body must contain valid JSON."})
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            self.send_json(502, {"error": f"Ollama returned HTTP {error.code}: {detail}"})
        except (URLError, TimeoutError, OSError) as error:
            self.send_json(502, {"error": f"Could not reach Ollama: {error}"})

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ChatHandler)
    print(f"Chat app running at http://localhost:{port} (model: {MODEL})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
