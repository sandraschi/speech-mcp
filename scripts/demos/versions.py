try:
    import google.genai as g

    print("google-genai:", g.__version__)
except ImportError:
    print("google-genai: Not installed")

try:
    import hume

    print("hume:", hume.__version__)
except ImportError:
    print("hume: Not installed")

try:
    import fastmcp

    print("fastmcp:", fastmcp.__version__)
except ImportError:
    print("fastmcp: Not installed")

try:
    import prefab_ui

    print("prefab_ui:", prefab_ui.__version__)
except ImportError:
    print("prefab_ui: Not installed")
