import sys
from parse_person import parse_person

files = [
    "2016-11-19-cascade-tuholske-phd-student.md",
    "2016-11-20-marc-mayes-postdoctoral-fellow-nature-conservancy-naturenet-fellow.md"  # NOQA
]

if len(sys.argv) > 1:
    filename = sys.argv[1]  # File name to parse
else:
    for file in files:
        if input("Parse {file}?".format(file=file)):
            parse_person(file)
