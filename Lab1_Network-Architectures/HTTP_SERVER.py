import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import threading

notes = {}
next_note_id = 1
notes_lock = threading.Lock()

HOST="10.8.0.2"
PORT=8080

class URLHandler (BaseHTTPRequestHandler ):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        elif path == "/echo":
            msg = query.get("msg", [""])[0]
            self.send_json(200, {"msg": msg})

        elif path.startswith("/notes/"):
            parts = path.split("/")

            if (
                len(parts) != 3
                or parts[1] != "notes"
                or not parts[2].isascii()
                or not parts[2].isdigit()
            ):
                self.send_json(404, {"error": "Not found"})
                return

            note_id = int(parts[2])

            with notes_lock:
                text = notes.get(note_id)

            if text is None:
                self.send_json(404, {"error": "Not found"})
            else:
                self.send_json(200, {"id": note_id, "text": text})

        else:
            self.send_json(404, {"error": "Not found"})
    
    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.split("/")

        if (
            len(parts) != 3
            or parts[1] != "notes"
            or not parts[2].isascii()
            or not parts[2].isdigit()
        ):
            self.send_json(404, {"error": "Not found"})
            return

        note_id = int(parts[2])

        with notes_lock:
            removed_text = notes.pop(note_id, None)

        if removed_text is None:
            self.send_json(404, {"error": "Not found"})
        else:
            self.send_response(204)
            self.end_headers()
    
    def do_PUT(self):
        path = urlparse(self.path).path

        if path == "/notes":
            allowed_methods = "POST"
        elif path.startswith("/notes/"):
            allowed_methods = "GET, DELETE"
        else:
            self.send_json(404, {"error": "Not found"})
            return

        self.send_json(
            405,
            {"error": "Method not allowed"},
            {"Allow": allowed_methods},
        )
                
    def send_json(self, status, data, extra_headers=None):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")

        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global next_note_id

        path = urlparse(self.path).path
        if path != "/notes":
            self.send_json(404, {"error": "Not found"})
            return

        content_type = self.headers.get("Content-Type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            self.send_json(415, {"error": "Content-Type must be application/json"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0:
                raise ValueError
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "Malformed JSON"})
            return

        if not isinstance(data, dict) or not isinstance(data.get("text"), str):
            self.send_json(400, {"error": "text must be a string"})
            return

        with notes_lock:
            note_id = next_note_id
            next_note_id += 1
            notes[note_id] = data["text"]

        self.send_json(201, {"id": note_id})
    
if __name__ == "__main__":
    
    server = ThreadingHTTPServer((HOST, PORT), URLHandler)
    print(f"Listening on http://{HOST}:{PORT}")
    server.serve_forever()
