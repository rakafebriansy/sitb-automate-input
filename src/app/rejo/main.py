import subprocess
import sys
import os

scripts = [
    "src/app/rejo/1/main.py",
    "src/app/rejo/2/main.py",
    "src/app/rejo/3/main.py",
    "src/app/rejo/4/main.py",
    "src/app/rejo/5/main.py",
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
