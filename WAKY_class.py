import os
from typing import Callable


class WAKYError(Exception):
    pass


class WAKYCheckError(WAKYError):
    def __init__(self, lineno, col, desc_str: str):
        super().__init__(f'[line={lineno}, col={col}] {desc_str}')


class WAKYFileNotFoundError(WAKYError):
    def __init__(self, fn):
        super().__init__(f'File not found: "{os.path.basename(fn)}"')


class CheckerContext:
    def __init__(self, file_name: str, ysn: int, encoding='utf8'):
        if not os.path.exists(file_name):
            raise WAKYFileNotFoundError(file_name)
        self.fp = open(file_name, 'r', encoding=encoding)
        self.ysn = ysn
        self.lineno = 1
        self.colno = 1
        self.line = ''
        self.ch = ''
        self.functions = []
        self.content = []

    def close(self):
        self.fp.close()

    def read_rmd(self, file_name:str, encoding = 'utf8'):
        if not os.path.exists(file_name):
            raise WAKYFileNotFoundError(file_name)
        self.rmd = clean_rmd(file_name, encoding=encoding)

    def check(self,
              char_checkers: "list[Callable[[CheckerContext], None]]" = None,
              line_checkers: "list[Callable[[CheckerContext], None]]" = None,
              content_checkers: "List[callale[[CheckerContext], None]]" = None,
              ) -> list[WAKYError]:
        errors = []
        if content_checkers is None:
            content_checkers = []
        if char_checkers is None:
            char_checkers = []
        if line_checkers is None:
            line_checkers = []

        self.line = ''
        self.content = []
        while self.fp.readable():
            self.ch = self.fp.read(1)
            if len(self.ch) == 0:
                break

            for char_checker in char_checkers:
                try:
                    char_checker(self)
                except WAKYError as e:
                    errors.append(e)
                    continue

            if self.ch == '\n':
                for line_checker in line_checkers:
                    try:
                        line_checker(self)
                    except WAKYError as e:
                        errors.append(e)
                        continue
                self.content.append(self.line)
                self.line = ''
                self.lineno += 1
                self.colno = 0
            else:
                self.line += self.ch
            self.colno += 1
        for content_checker in content_checkers:
            try:
                content_checker(self)
            except WAKYError as e:
                errors.append(e)
                continue
        return errors

def DS2_Checker_ysn_seed(cc:CheckerContext):
    if f'set.seed({cc.ysn})' not in cc.content:
        raise WAKYCheckError(len(cc.content), 1, f'set.seed({cc.ysn}) not in your R script')

def DS3_Checker_invalid_char(cc: CheckerContext):
    ch_code = ord(cc.ch)
    if ch_code not in [9, 10, 13] + list(range(0x20, 0x7f)):
        raise WAKYCheckError(cc.lineno, cc.colno, f'Invalid char "{cc.ch}"')

def DS3_Checker_contains_comments(cc: CheckerContext):
    COMMENT_PATTERNS = ['#', '<!--']
    for pat in COMMENT_PATTERNS:
        if pat in cc.line:
            raise WAKYCheckError(cc.lineno, cc.line.find(
                pat) + 1, f'Should not contains comment "{pat}".')
        
def DS5_Checker_same_contains(cc:CheckerContext):
    for lineno, line in enumerate(cc.content):
        if line != cc.rmd[lineno]:
            col = 1
            for ch in cc.line:
                if ch == cc.rmd[cc.lineno - 1][col]:
                    col += 1
                else:
                    break
            raise WAKYCheckError(lineno + 1, col, f'R script is different from R markdown code.')
    if len(cc.content) > len(cc.rmd):
        raise WAKYCheckError(len(cc.rmd), 1, f'R script has more line(s) than R markdown code.')
    elif len(cc.content) < len(cc.rmd):
        raise WAKYCheckError(len(cc.content), 1, f'R script has less line(s) than R markdown code.')
    # if cc.lineno > len(cc.rmd):
    #     raise WAKYCheckError(cc.lineno, 1, f'R script has more line(s) than R markdown code.')
    # elif cc.line != cc.rmd[cc.lineno - 1]:
    #     col = 1
    #     for ch in cc.line:
    #         if ch == cc.rmd[cc.lineno - 1][col]:
    #             col += 1
    #         else:
    #             break
    #     raise WAKYCheckError(cc.lineno, col, f'R script is different from R markdown code.')

def clean_rmd(filename, encoding = 'utf-8'):
    content = []
    code_start = False
    with open(filename, 'r',encoding = encoding) as f:
        reader = f.readlines()
        for line in reader:
            if '```{r' in line:
                ind = 0
                for ch in line:
                    if ch == '`':
                        break
                    ind += 1
                code_start = True
            elif code_start & ('```' not in line):
                content.append(line[ind:-1])
            elif '```' in line:
                code_start = False
    return content[1:]

cc = CheckerContext('test_2.R', 20151114)
cc.read_rmd('test_rmd_2.txt')
for e in cc.check(char_checkers=[DSx_Checker_invalid_char], line_checkers=[DSx_Checker_contains_comments], content_checkers=[DS2_Checker_ysn_seed, DS4_Checker_same_contains]):
    print(e.__class__.__name__, e.args[0])
