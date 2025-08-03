from pyrlint import RToken, RTokenType, RTokenizer
import os
import enum
import csv
from collections import namedtuple
from typing import Callable
from dataclasses import dataclass
import re


__all__ = ['WAKYError', 
           'WAKYCheckError', 
           'WAKYFileNotFoundError', 
           'CheckerTriggerScope', 
           'clean_rmd', 
           'CheckerContext', 
           'DS2_Checker_ysn_seed',
           'DS3_Checker_invalid_char',
           'DS3_Checker_contains_comments',
           'DS3_Checker_contains_comments_rmd',
           'DS5_Checker_same_contains_r',
           'WAKYReminderSheetCheckError',
           'WAKYReminderSheetCheckInfo',
           'ReminderSheetChecker',
           ]

class WAKYError(Exception):
    pass


class WAKYCheckError(WAKYError):
    WAKYCheckArgs = namedtuple("WAKYCheckArgs", 'desc row col offset length')
    args: WAKYCheckArgs

    def __init__(self, desc: str, row: int = -1, col: int = -1, offset: int = -1, length: int = 0, token: RToken | None = None):
        if token is None:
            super().__init__(desc, row, col, offset, length)
        else:
            super().__init__(desc, token.row, token.col, token.offset, len(token))

    def __str__(self):
        args = WAKYCheckError.WAKYCheckArgs(*self.args)
        if args.row != -1 and args.col != -1:
            position_str = f'[Ln {args.row+1}, Col {args.col+1}] '
        elif args.row != -1:
            position_str = f'[Ln {args.row+1}] '
        else:
            position_str = ''
        return f'{position_str}{self.__class__.__name__}: {args.desc}'

    @property
    def start(self) -> int:
        return self.args[3]

    @property
    def end(self) -> int:
        return self.args[3] + self.args[4]

    @property
    def is_colorable(self) -> bool:
        args = WAKYCheckError.WAKYCheckArgs(*self.args)
        return args.offset != -1 and args.length > 0


class WAKYFileNotFoundError(WAKYError):
    def __init__(self, fn):
        super().__init__(f'File not found: "{os.path.basename(fn)}"')

    def __str__(self):
        return f'{self.__class__.__name__}: {self.args[0]}'


class CheckerTriggerScope(enum.IntEnum):
    NONE = 0            # Checker will never be called, default
    # File based
    FILE_PATH = 10      # Full path, check cc.file_path
    CHAR = 11           # Character, check cc.character
    LINE = 12           # Line, check cc.line
    CONTENT = 13        # Full string content, check cc.content
    # Parser based
    TOKEN = 20
    EXPRESSION = 21     # NotImplemented
    STATEMENT = 22      # NotImplemented

    def __call__(self, callable_obj: "CheckerContext.CheckerFunctionType|type"):
        def make_wrapper(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            setattr(wrapper, 'scope', self)
            return wrapper

        if isinstance(callable_obj, type) and hasattr(callable_obj, '__call__'):
            callable_obj.__call__ = make_wrapper(callable_obj.__call__)
            setattr(callable_obj, 'scope', self)
            return callable_obj
        else:  # regard as function
            return make_wrapper(callable_obj)


def clean_rmd(filename, encoding='utf-8'):
    content = []
    code_start = False
    with open(filename, 'r', encoding=encoding) as f:
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


class CheckerContext:
    CheckerFunctionType = Callable[["CheckerContext"], None]
    """Check function raises WAKYCheckError."""

    def __init__(self, file_path: str, ysn: int, checkers: "list[CheckerFunctionType]", encoding='utf8'):
        self.encoding = encoding
        if not os.path.exists(file_path):
            raise WAKYFileNotFoundError(file_path)
        self.file_path: str = file_path
        self.content: str = ''
        # TODO: Currently read full content instead of buffer
        with open(file_path, 'r', encoding=encoding) as fi:
            self.content = fi.read()

        self.ysn: int = ysn

        self._checkers: dict[
            CheckerTriggerScope,
            list[CheckerContext.CheckerFunctionType]
        ] = dict()
        for checker in checkers:
            self._checkers.setdefault(getattr(checker, 'scope', CheckerTriggerScope.NONE),
                                      list()).append(checker)

        self.lineno = 0
        self.colno = 0
        self.ch_pos = 0
        self.character = ''
        self.line = ''
        self.errors: list[WAKYCheckError] = []
        self.token: RToken = None
        self._file_based_check()
        self._parser_based_check()

    def _run_checkers(self, scope: CheckerTriggerScope):
        checkers = self._checkers.get(scope, [])
        if len(checkers) == 0:
            return
        for checker in checkers:
            try:
                checker(self)
            except WAKYError as e:
                self.errors.append(e)
                continue

    def _file_based_check(self):
        self.lineno = 0
        self.colno = 0
        self.ch_pos = 0
        self.character = ''
        self.line = ''
        self._run_checkers(CheckerTriggerScope.FILE_PATH)
        for self.ch_pos, self.character in enumerate(self.content):
            self._run_checkers(CheckerTriggerScope.CHAR)
            if self.character == '\n':
                self._run_checkers(CheckerTriggerScope.LINE)
                self.line = ''
                self.lineno += 1
                self.colno = -1
            else:
                self.line += self.character
            self.colno += 1
        self._run_checkers(CheckerTriggerScope.CONTENT)

    def _parser_based_check(self):
        rt = RTokenizer(self.content)
        while True:
            self.token = rt.next_token()
            if not self.token:
                break
            self._run_checkers(CheckerTriggerScope.TOKEN)

    @property
    def error_marked_content(self):
        COLOR_RESET = f'\033[0m'
        COLOR_LEVELS = {
            WAKYCheckError: [
                f'\033[0m',         # Reset
                f'\033[48;5;52m',   # Loop un-commented
                # f'\033[48;5;88m',
                f'\033[48;5;1m',
                # f'\033[48;5;124m',
                # f'\033[48;5;160m',
                # f'\033[48;5;196m'
            ],
            WAKYReminderSheetCheckInfo: [
                f'\033[0m',
                f'\033[44m',
            ],
            WAKYReminderSheetCheckError: [
                f'\033[0m',
                f'\033[43m',
            ],
        }
        errors: list[WAKYCheckError] = sorted([e for e in self.errors if e.is_colorable],
                                              key=lambda e: e.args[3])

        colored_str = ''
        raw_str = self.content
        error_stack: list[WAKYCheckError] = [WAKYCheckError(
            'MockError', offset=0, length=len(raw_str))]
        pos = 0

        for err in errors:
            while err.start > error_stack[-1].end:
                color_set = COLOR_LEVELS.get(error_stack[-1].__class__, None)
                color = COLOR_RESET if color_set is None else (
                    color_set[0 if len(error_stack) == 1 else (
                        ((len(error_stack) - 2) % (len(color_set) - 1)) + 1)]
                )
                colored_str += color
                last_err = error_stack.pop()
                colored_str += raw_str[pos:last_err.end]
                pos = last_err.end

            color_set = COLOR_LEVELS.get(error_stack[-1].__class__, None)
            color = COLOR_RESET if color_set is None else (
                color_set[0 if len(error_stack) == 1 else (
                    (len(error_stack) - 1) % (len(COLOR_LEVELS) - 1))]
            )
            colored_str += color
            colored_str += raw_str[pos:err.start]
            pos = err.start
            error_stack.append(err)
        colored_str += COLOR_RESET
        return colored_str

    def read_rmd(self, file_name: str, encoding='utf8'):
        if not os.path.exists(file_name):
            raise WAKYFileNotFoundError(file_name)
        self.rmd = clean_rmd(file_name, encoding=encoding)


@CheckerTriggerScope.CONTENT
def DS2_Checker_ysn_seed(cc: CheckerContext):
    if (f'set.seed({cc.ysn})' not in cc.content) and (f'set.seed(ysn)' not in cc.content):
        raise WAKYCheckError(f'set.seed({cc.ysn}) not in your R script')


@CheckerTriggerScope.CHAR
def DS3_Checker_invalid_char(cc: CheckerContext):
    ch_code = ord(cc.character)
    if ch_code not in [9, 10, 13] + list(range(0x20, 0x7f)):
        raise WAKYCheckError(f'Invalid char "{cc.character}"',
                             cc.lineno, cc.colno, cc.ch_pos, 1)


@CheckerTriggerScope.TOKEN
def DS3_Checker_contains_comments(cc: CheckerContext):
    if cc.token.type == RTokenType.COMMENT:
        raise WAKYCheckError(f'Should not contains comment', token=cc.token)

@CheckerTriggerScope.LINE
def DS3_Checker_contains_comments_rmd(cc: CheckerContext):
    COMMENT_PATTERNS = ['#', '<!--']
    for pat in COMMENT_PATTERNS:
        if pat in cc.line:
            raise WAKYCheckError( f'Should not contains comment "{pat}".', cc.lineno, cc.line.find(
                pat) + 1)


@CheckerTriggerScope.CONTENT
class DS5_Checker_same_contains_r:
    def __init__(self, rmd_file_path: str):
        self.rmd = clean_rmd(rmd_file_path)

    def __call__(self, cc: CheckerContext):
        r_content = cc.content.split('\n')
        for lineno, line in enumerate(r_content):
            if line != self.rmd[lineno]:
                col = 1
                for ch in cc.line:
                    if ch == self.rmd[cc.lineno][col]:
                        col += 1
                    else:
                        break
                raise WAKYCheckError(
                    f'R script is different from R markdown code. (R lines = {lineno+1})', lineno, col - 1)
        if len(r_content) > len(self.rmd):
            raise WAKYCheckError(
                f'R script has more line(s) than R markdown code.')
        elif len(r_content) < len(self.rmd):
            raise WAKYCheckError(
                f'R script has less line(s) than R markdown code.')
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


class WAKYReminderSheetCheckError(WAKYCheckError):
    pass


class WAKYReminderSheetCheckInfo(WAKYCheckError):
    pass


@CheckerTriggerScope.TOKEN
class ReminderSheetChecker:
    @dataclass
    class FunctionInfo:
        source: str
        command: str
        description: str
        example: str = ''
        explain: str = ''

    def __init__(self, reminder_csv_file: str):
        self.valid_functions: dict[str,
                                   "ReminderSheetChecker.FunctionInfo"] = {}
        with open(reminder_csv_file, 'r', encoding='utf8') as fi:
            fi.readline()  # Remove header
            for line_items in csv.reader(fi):
                func = ReminderSheetChecker.FunctionInfo(
                    *map(str.strip, line_items))
                if func.command.endswith('()'):
                    self.valid_functions[func.command[:-2]] = func
        self.last_id_token: RToken = None

    def __call__(self, cc: CheckerContext):
        if cc.token.is_whitespace and not cc.token.is_whitespace_with_newline:
            return
        elif cc.token.is_id:
            self.last_id_token = cc.token
        elif cc.token.type == RTokenType.LPAREN and self.last_id_token is not None:
            func_name = self.last_id_token.content
            if func_name in self.valid_functions:
                raise WAKYReminderSheetCheckInfo(
                    f'Valid function', token=self.last_id_token)
            else:
                raise WAKYReminderSheetCheckError(
                    f'Function is not in reminder sheet "{func_name}"', token=self.last_id_token)
        else:
            self.last_id_token = None


def main_exec():
    file_name = {}
    current_dir = os.path.dirname(__file__)
    for fn in os.listdir(current_dir):
        if m:=re.match(r'a(\d)_(\d+)_1.R', fn):
            file_name['r'] = fn
            ysn = int(m[2])
        elif re.match(r'a(\d)_(\d+)_2.Rmd', fn):
            file_name['rmd'] = fn

    if len(file_name) == 0:
        print('Can not find all the files, please put .rmd and .R in the same directory.')    
        return
    elif len(file_name) == 1:
        reply = input('Miss one file. Do you want to check one file only?(Y/n)')
        if reply.lower() != 'y' and reply != '':
            return
    r_file = file_name.get('r', None)
    rmd_file = file_name.get('rmd', None)
    if r_file is not None:
        checkers = [
            DS2_Checker_ysn_seed,
            DS3_Checker_invalid_char,
            DS3_Checker_contains_comments,
            ReminderSheetChecker('better_reminder.csv'),
        ]
        if rmd_file is not None:
            checkers.append(DS5_Checker_same_contains_r(os.path.join(current_dir, rmd_file)))
        cc = CheckerContext(os.path.join(current_dir, r_file), ysn, checkers=checkers)
        print(cc.error_marked_content)
        with open(f'checker_{cc.ysn}.r.log', 'w', encoding=cc.encoding) as fo:
            for err in cc.errors:
                if isinstance(err, (WAKYReminderSheetCheckInfo,)):
                    # skip highlight info from logging
                    continue
                print(err, file=fo)
    if rmd_file is not None:
        cc = CheckerContext(os.path.join(current_dir, rmd_file), ysn, checkers=[
            DS2_Checker_ysn_seed,
            DS3_Checker_invalid_char,
            DS3_Checker_contains_comments_rmd,
        ])
        # print(cc.error_marked_content)
        with open(f'checker_{cc.ysn}.rmd.log', 'w', encoding=cc.encoding) as fo:
            for err in cc.errors:
                if isinstance(err, (WAKYReminderSheetCheckInfo,)):
                    # skip highlight info from logging
                    continue


if __name__ == '__main__':
    main_exec()
