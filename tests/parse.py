from IPython import embed
import json
import re

f = open("./tests/explanation.txt", "r")
lines = f.readlines()
f.close()

guas = []
gua_des = {}

def is_gua(line):
    # if line[0].isdigit() and line[3] in ["乾","坤","兑","艮","离","坎","震","巽"]:
    if '\xa0' in line:
        return False
    if '.' in line and '。' not in line:
        return True
    elif line[0] in ["乾","坤","兑","艮","离","坎","震","巽"]:
        return True
    elif line[0] in "天地泽山火水雷风" and line[1] in "天地泽山火水雷风":
        return True
    return False

def guaming(line):
    return line.rstrip('\n').split('.')[-1]

def is_xiantian(line):
    return line.startswith("先天卦：")

def is_houtian(line):
    return line.startswith("后天卦：")

def is_liunian(line):
    return line.startswith("流年卦：")

def parse_description(lines):
    text = ''.join(lines)
    pattern = r"先天卦：\n(.*?)\n\n后天卦：\n(.*?)\n\n(流年卦|流年)：\n(.*?)$"
    match = re.search(pattern, text, re.DOTALL)
    data = {}
    if match:
        data = {
        "先天卦": match.group(1),
        "后天卦": match.group(2),
        "流年卦": match.group(3)
        }
    return data

gua = ""
for num, line in enumerate(lines):
    if is_gua(line):
        gua = guaming(line)
        guas.append(line)
        gua_des[gua] = []
    gua_des[gua].append(line)

print(guas)
print(len(guas))
gua_dict = {}
for k, v in gua_des.items():
    gua_dict[k] = parse_description(v)

json_data = json.dumps(gua_dict, indent=4, ensure_ascii=False)

with open("tests/guas_dict.txt", "w") as out:
    out.write(str(gua_dict))

with open("tests/guas.json", "w", encoding='utf-8') as file:
    file.write(json_data)

print(json_data)
# embed()
