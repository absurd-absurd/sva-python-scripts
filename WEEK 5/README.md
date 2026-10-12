# Photoshop bridge

A bridge that lets an AI agent (Claude Code) make Photoshop do things while
Photoshop is open.

## Which app, and which way

- **App:** Adobe Photoshop (built and tested on Photoshop 2026, Windows 11)
- **Way:** a **port**

Photoshop doesn't have a command port you can switch on like Maya does, so the
bridge supplies one. There are two small Python scripts:

| File | What it does |
| --- | --- |
| `ps_listener.py` | Listens on port `7008` on your own computer. Any JavaScript that arrives is run inside the open Photoshop, and the result (or the error) is sent back. |
| `send.py` | What the agent runs. It sends a script to the port and prints what Photoshop answered. |

```
agent  ->  send.py  ->  port 7008  ->  ps_listener.py  ->  Photoshop
```

The listener only accepts connections from the same computer (`127.0.0.1`).

## How to run it

You need Windows, Photoshop, and Python 3.

1. Get the code and install the one thing it depends on:

   ```
   git clone https://github.com/absurd-absurd/sva-python-scripts
   cd "sva-python-scripts/WEEK 5"
   pip install -r requirements.txt
   ```

2. Open Photoshop.

3. In a terminal, start the listener and leave it running:

   ```
   python ps_listener.py
   ```

   It should say `Photoshop bridge listening on 127.0.0.1:7008`.

   If you have more than one Photoshop installed and it talks to the wrong
   one, close that one and name the version you want: `200` for Photoshop
   2026, `190` for 2025, `180` for 2024.

   ```
   python ps_listener.py 200
   ```

4. In a second terminal, check that it works:

   ```
   python send.py "app.version"
   ```

   It should print your Photoshop version number.

5. Open your agent in this folder and tell it:

   > Photoshop is open and `ps_listener.py` is running. You can make Photoshop
   > do things by sending it JavaScript with `python send.py`. Read the README.

   Then ask for what you want in plain words.

To stop the bridge, press `Ctrl+C` in the listener's terminal.

### For the agent

- Photoshop scripts are ExtendScript (old-style JavaScript: `var`, no `let`,
  no arrow functions).
- Short scripts: `python send.py "app.documents.length"`.
- Longer scripts: write them to a `.jsx` file and run `python send.py -f file.jsx`.
- The value of the script's last line is what gets printed back, so end a
  script with something worth reading.
- If Photoshop raises an error, `send.py` prints it and exits with code 1.

## What I asked for

**My exact words:**

> in photoshop make a 1920x1080 poster with a sunset gradient and my name, fayth elisa navarro,  in big white text

**What happened:**

The agent wrote a Photoshop script (`poster.jsx`) and sent it through the
bridge with `python send.py -f poster.jsx`. In the open Photoshop, a new
1920x1080 document called "Sunset Poster" appeared with:

- a gradient fill layer going from deep purple at the top, through pink and
  orange, to a golden glow at the bottom
- a text layer reading "FAYTH ELISA NAVARRO" in bold white Arial, centered and
  scaled to fill most of the width (the agent chose capitals on its own)

Photoshop answered back through the bridge:

```
Made 'Sunset Poster' 1920x1080, layers: 3, font: Arial-BoldMT, text spans x 134-1786, y 486-594
```

The agent then checked its own work by sending a second script that exported a
copy of the poster and looking at it. The first try at that export failed with
"the application is busy" because Photoshop was still finishing up; it waited a
few seconds, sent it again, and it worked. The result:

![The poster Photoshop made](poster.png)

## Recording

(https://youtu.be/O9jJtVn3Lms)
