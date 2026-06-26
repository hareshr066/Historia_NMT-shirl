import time

def test_import(module_name):
    t0 = time.time()
    try:
        print(f"Importing {module_name}...", end=" ", flush=True)
        __import__(module_name)
        print(f"Success! (took {time.time() - t0:.2f} seconds)", flush=True)
    except Exception as e:
        print(f"FAILED: {e}", flush=True)

test_import("numpy")
test_import("pandas")
test_import("scipy")
test_import("sklearn")
test_import("huggingface_hub")
test_import("transformers")
test_import("sentence_transformers")
