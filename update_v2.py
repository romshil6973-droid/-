path = "tests/test_browser_history.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

old = "    def test_chrome_ts_zero_is_epoch(self):"
new = "    @pytest.mark.skipif(__import__('sys').platform == 'win32', reason='Windows не поддерживает даты до 1970')\n    def test_chrome_ts_zero_is_epoch(self):"

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("✓ test_browser_history.py исправлен")