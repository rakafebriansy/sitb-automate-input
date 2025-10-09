import os
import subprocess

DISTRICT = 'mulyorejo'

BASE_DIR = "src/app"
MAIN_FILE = "main.py"

target_dir = os.path.join(BASE_DIR, DISTRICT) if DISTRICT else None
main_file = os.path.join(target_dir, MAIN_FILE) if target_dir else None

if not DISTRICT:
    print("[x] The DISTRICT constant is not set.")
elif not os.path.isdir(target_dir):
    print(f"[x] The folder '{target_dir}' was not found inside {BASE_DIR}/.")
elif not os.path.isfile(main_file):
    print(f"[x] The file main.py was not found in the folder '{target_dir}'.")
else:
    import sys
    env = os.environ.copy()
    subprocess.run([sys.executable, main_file], env=env, cwd=os.getcwd())