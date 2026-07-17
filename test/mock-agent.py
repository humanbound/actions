"""Minimal mock AI agent for e2e-testing the action.

Speaks the `chat_completion` integration contract: accepts POST with a JSON
payload containing the attack prompt, replies with {"content": "..."}.
Deliberately narrow (a weather-only assistant) so adversarial probes have
a realistic refusal surface to test against.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8765

REPLY = (
    "I'm a weather assistant. I can only help with weather forecasts and "
    "current conditions. I can't help with that request."
)


class MockAgent(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)  # consume the prompt; reply is static
        body = json.dumps({"content": REPLY}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # keep CI logs quiet
        pass


if __name__ == "__main__":
    print(f"mock agent listening on 127.0.0.1:{PORT}", flush=True)
    HTTPServer(("127.0.0.1", PORT), MockAgent).serve_forever()
