import pyperclip

def get_clipboard() -> str|None:
   try:
      return pyperclip.paste()
   except Exception:
      return None

# print(get_clipboard())