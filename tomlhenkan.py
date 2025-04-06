with open("your-creds.json", "r") as f:
    raw = f.read()

# 改行を \\n に変換してクリップボードにコピーできる形式で出力
print(raw.replace("\n", "\\n"))
