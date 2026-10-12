"""Photoshop side of the bridge. Leave this running in its own terminal.

Photoshop has no open port of its own the way Maya does, so this script is
the port. It listens on this machine, and whatever JavaScript arrives gets
handed to the open Photoshop through its scripting interface (the same one
File > Scripts uses). The script's result, or its error, is sent back.

    python ps_listener.py
"""
import json
import socket

import pythoncom
import win32com.client

HOST = "127.0.0.1"  # local only: nothing outside this computer can connect
PORT = 7008


def run_in_photoshop(script):
    """Run JavaScript in Photoshop and return a result dict."""
    try:
        # Connects to the open Photoshop, or starts it if it is closed.
        app = win32com.client.Dispatch("Photoshop.Application")
        result = app.DoJavaScript(script)
        return {"ok": True, "output": "" if result is None else str(result)}
    except pythoncom.com_error as e:
        # Photoshop puts the readable message (with the line number) here.
        detail = e.excepinfo[2] if e.excepinfo and e.excepinfo[2] else str(e)
        return {"ok": False, "output": "", "error": detail}


def handle(conn):
    with conn:
        conn.settimeout(None)
        chunks = []
        while True:
            data = conn.recv(65536)
            if not data:  # sender closed its side: the whole script has arrived
                break
            chunks.append(data)
        result = run_in_photoshop(b"".join(chunks).decode("utf-8"))
        conn.sendall(json.dumps(result).encode("utf-8"))


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    server.settimeout(1)  # wake up every second so Ctrl+C works on Windows
    print("Photoshop bridge listening on %s:%d  (Ctrl+C to stop)" % (HOST, PORT))
    try:
        while True:
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            handle(conn)
    except KeyboardInterrupt:
        print("Photoshop bridge stopped")
    finally:
        server.close()


if __name__ == "__main__":
    main()
