from pywinauto import Application
import time

app = Application(backend="uia").start("calc.exe")

time.sleep(3)

print("Windows" ,app.windows())