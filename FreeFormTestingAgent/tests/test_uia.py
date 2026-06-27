import subprocess
import time
import uiautomation as auto

subprocess.Popen("calc.exe")

time.sleep(5)

for c in auto.GetRootControl().GetChildren():
    print(c.Name, c.ControlTypeName)