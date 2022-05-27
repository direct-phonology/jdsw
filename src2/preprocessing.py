# preprocessing
import os
import re
import shutil
from tempfile import NamedTemporaryFile

#copy files from source directory to target directory
src_dir = "ECTexts_parsed"
dest_dir = "ECTexts_parsed_preprocessed"
files = os.listdir(src_dir)
shutil.copytree(src_dir, dest_dir)
dest_files = os.listdir(dest_dir)

pattern1 = r'¶'
plist = [r'¶', r'#.*\n', r'\n<.*>\n', r'<.*>', r'\t.*', r'[1-9]', r'\.', r'\)\n\(', r'/']

def main():
    encoding = 'utf-8'
    matched = re.compile(pattern1).search
    for infile in dest_files:
        with open(input_file, encoding=encoding) as input_file:
            with NamedTemporaryFile(mode='w', encoding=encoding,
                                    dir=os.path.dirname(input_file),
                                    delete=False) as outfile:
                for line in input_file:
                    if not matched(line):
                        print(line, end='', file=outfile)
    os.replace(outfile.name, input_file.name)

main()