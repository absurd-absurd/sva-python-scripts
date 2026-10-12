"""Agent side of the bridge. Sends JavaScript to the open Photoshop.

Usage:
    python send.py "app.version"
    python send.py -f script.jsx
    type script.jsx | python send.py -

ps_listener.py must be running first.
"""
import json
import socket
import sys

HOST = "127.0.0.1"
PORT = 7008


def send(script, timeout=300):
    with socket.create_connection((HOST, PORT), timeout=timeout) as sock:
        sock.sendall(script.encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)  # tells the listener the script is complete
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    return json.loads(b"".join(chunks).decode("utf-8"))


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "-":
        script = sys.stdin.read()
    elif args[0] == "-f":
        with open(args[1], encoding="utf-8") as f:
            script = f.read()
    else:
        script = " ".join(args)

    try:
        result = send(script)
    except ConnectionRefusedError:
        sys.exit("Could not reach the bridge on port %d. Is ps_listener.py "
                 "running?" % PORT)

    if result["output"]:
        print(result["output"])
    if not result["ok"]:
        sys.exit("Photoshop error: " + result["error"])


if __name__ == "__main__":
    main()
