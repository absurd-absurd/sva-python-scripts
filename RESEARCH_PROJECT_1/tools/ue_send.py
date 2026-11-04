"""Send a Python file (or a one-liner with -c) to a running Unreal editor via remote execution."""
import sys, time
sys.path.append(r"C:\Program Files\Epic Games\UE_5.5\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution as rex

args = sys.argv[1:]
if args[0] == "-c":
    code, mode = args[1], rex.MODE_EXEC_STATEMENT
else:
    # run each file in its own fresh namespace: leftovers from earlier scripts (references to
    # assets/actors that were since deleted) in the shared __main__ crashed Unreal twice
    path = args[0].replace("\\", "/")
    code = "exec(compile(open(%r, encoding='utf-8').read(), %r, 'exec'), {'__name__': '__main__', '__file__': %r})" % (path, path, path)
    mode = rex.MODE_EXEC_FILE if False else rex.MODE_EXEC_STATEMENT

r = rex.RemoteExecution()
r.start()
try:
    for _ in range(50):
        if r.remote_nodes:
            break
        time.sleep(0.2)
    else:
        print("NO UNREAL FOUND"); sys.exit(2)
    r.open_command_connection(r.remote_nodes[0]["node_id"])
    res = r.run_command(code, unattended=True, exec_mode=mode)
    for o in res.get("output", []):
        print(o["output"].rstrip())
    print("OK" if res["success"] else "FAILED: " + str(res.get("result")))
finally:
    r.stop()
