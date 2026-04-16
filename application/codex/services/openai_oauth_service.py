import base64
import hashlib
import html
import json
import secrets
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from wsgiref.simple_server import WSGIServer, make_server


class OpenAiOauthService:
    AUTH_URL = "https://auth.openai.com/oauth/authorize"
    TOKEN_URL = "https://auth.openai.com/oauth/token"
    CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
    REDIRECT_URI = "http://localhost:1455/auth/callback"
    SCOPES = "openid profile email offline_access"

    def __init__(self, auth_file: Path | None = None):
        self._auth_file = auth_file or (Path.home() / ".codex" / "auth.json")
        self._lock = threading.Lock()
        self._server: WSGIServer | None = None
        self._server_thread: threading.Thread | None = None
        self._state = {
            "status": "disconnected",
            "message": "",
            "pkce_verifier": "",
            "state": "",
        }

    def get_status(self) -> dict:
        data = self._read_auth_file()
        if data.get("tokens", {}).get("access_token"):
            return {"status": "connected", "message": "Already logged in"}
        return {"status": self._state["status"], "message": self._state["message"]}

    def get_access_token(self) -> str | None:
        return self._read_auth_file().get("tokens", {}).get("access_token")

    def start_auth_flow(self) -> dict:
        if self.get_access_token():
            return {"status": "connected", "message": "Already logged in"}
        verifier = self._generate_verifier()
        challenge = self._build_challenge(verifier)
        state = secrets.token_hex(16)
        self._state.update(
            {
                "status": "pending",
                "message": "Waiting for user login...",
                "pkce_verifier": verifier,
                "state": state,
            }
        )
        self._ensure_server()
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": self.CLIENT_ID,
                "redirect_uri": self.REDIRECT_URI,
                "scope": self.SCOPES,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": state,
            }
        )
        return {"status": "pending", "url": f"{self.AUTH_URL}?{query}"}

    def logout(self) -> dict:
        if self._auth_file.exists():
            self._auth_file.unlink()
        self._state.update(
            {
                "status": "disconnected",
                "message": "Logged out",
                "pkce_verifier": "",
                "state": "",
            }
        )
        return self.get_status()

    def _read_auth_file(self) -> dict:
        if not self._auth_file.exists():
            return {}
        try:
            return json.loads(self._auth_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_auth_file(self, payload: dict) -> None:
        self._auth_file.parent.mkdir(parents=True, exist_ok=True)
        self._auth_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _generate_verifier() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

    @staticmethod
    def _build_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    def _ensure_server(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()

    def _run_server(self) -> None:
        def app(environ, start_response):
            if environ.get("PATH_INFO") != "/auth/callback":
                start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
                return [b"Not Found"]

            query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
            code = query.get("code", [None])[0]
            state = query.get("state", [None])[0]
            error = query.get("error", [None])[0]

            try:
                if error:
                    raise RuntimeError(error)
                if not code or state != self._state["state"]:
                    raise RuntimeError("Invalid OAuth callback state")

                tokens = self._exchange_code(code)
                self._write_auth_file({"tokens": tokens})
                self._state.update({"status": "connected", "message": "Login successful"})
                body = self._build_callback_page("connected", "OpenAI OAuth login successful.")
                status = "200 OK"
            except Exception as exc:  # pragma: no cover
                self._state.update({"status": "error", "message": str(exc)})
                body = self._build_callback_page("error", f"OpenAI OAuth login failed: {exc}")
                status = "500 Internal Server Error"

            start_response(status, [("Content-Type", "text/html; charset=utf-8")])
            return [body.encode("utf-8")]

        with make_server("127.0.0.1", 1455, app) as server:
            self._server = server
            server.serve_forever()

    def _exchange_code(self, code: str) -> dict:
        data = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "client_id": self.CLIENT_ID,
                "code": code,
                "redirect_uri": self.REDIRECT_URI,
                "code_verifier": self._state["pkce_verifier"],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _build_callback_page(status: str, message: str) -> str:
        escaped_message = html.escape(message)
        payload = json.dumps(
            {
                "type": "openai-oauth-complete",
                "status": status,
                "message": message,
            },
            ensure_ascii=False,
        ).replace("</", "<\\/")
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OpenAI OAuth</title>
    <style>
      body {{
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #0f172a;
        color: #e2e8f0;
        display: grid;
        place-items: center;
        min-height: 100vh;
      }}
      main {{
        width: min(92vw, 420px);
        padding: 24px;
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.92);
        box-shadow: 0 18px 48px rgba(15, 23, 42, 0.25);
      }}
      h1 {{
        margin: 0 0 12px;
        font-size: 20px;
      }}
      p {{
        margin: 0;
        line-height: 1.6;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>OpenAI OAuth</h1>
      <p>{escaped_message}</p>
    </main>
    <script>
      const payload = {payload};
      if (window.opener && !window.opener.closed) {{
        window.opener.postMessage(payload, "*");
      }}
      setTimeout(() => window.close(), 200);
    </script>
  </body>
</html>"""
