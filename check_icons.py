
from qfluentwidgets import FluentIcon
for attr in dir(FluentIcon):
    if not attr.startswith("__"):
        print(attr)
