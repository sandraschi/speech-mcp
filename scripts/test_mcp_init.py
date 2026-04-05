import subprocess
import json
import time


def test_mcp():
    cmd = [
        "uv",
        "--directory",
        "D:/Dev/repos/speech-mcp",
        "run",
        "python",
        "-m",
        "speech_mcp.server",
    ]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    print("Sending initialize...")
    process.stdin.write(json.dumps(init_msg) + "\n")
    process.stdin.flush()

    print("Waiting for response...")
    try:
        # Wait for any output
        line = process.stdout.readline()
        if line:
            print(f"Received: {line}")
            return True
        else:
            print("No response received.")
            # Check stderr
            err = process.stderr.read()
            if err:
                print(f"Stderr: {err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()
    return False


if __name__ == "__main__":
    test_mcp()
