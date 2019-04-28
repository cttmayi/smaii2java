import re


lines = [
    '.field private static final COLUMN_INDEX_FIRST:I = 0x0',
    '.field COLUMN_INDEX_FIRST:I',
    '.field private static final COLUMN_INDEX_FIRST:I',
    ]
for line in lines:
    P = '\.field ((\w+ +)*)(\w+):(\w+)( += +([\dx]+))*'
    m = re.match(P, line)
    if m:
        print(line)
        print("\t:", m.groups())