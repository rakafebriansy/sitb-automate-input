import subprocess
import sys
import os

scripts = [
    "src/app/patumbak_2/1/main.py",
    "src/app/patumbak_2/2/main.py",
    "src/app/patumbak_2/3/main.py",
    "src/app/patumbak_2/4/main.py",
    "src/app/patumbak_2/5/main.py",
]

env = os.environ.copy()
for script in scripts:
    print(f"🚀 Running {script} ...")
    result = subprocess.run([sys.executable, script], env=env, cwd=os.getcwd())
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Error in {script}: {result.stderr}")
        break
    print(f"✅ Finished {script}\n{'-'*50}")
