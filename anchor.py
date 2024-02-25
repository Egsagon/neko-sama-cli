'''
    Anchor - Simple ANSI wrapper & CLI parts
    
    See https://github.com/Egsagon/anchor
'''

import os
import re
import time
import threading
from typing import Literal, Callable

__author__ = 'Egsagon'
__version__ = '0.1'
__license__ = 'MIT'
__copyright__ = 'Egsagon, 2024'

__all__ = [
    'COLOR', 'BORDER', 'MAX_WIDTH', 'FONT_COLOR',
    'BORDER_TYPE', 'BORDER_COLOR', 'banner', 'entry',
    'separator', 'select_large',
]

class COLOR:
    _OFFSET = 90
    NORMAL  = 0
    
    GREY    = _OFFSET + 0
    RED     = _OFFSET + 1
    GREEN   = _OFFSET + 2
    YELLOW  = _OFFSET + 3
    BLUE    = _OFFSET + 4
    MAGENTA = _OFFSET + 5
    CYAN    = _OFFSET + 6
    WHITE   = _OFFSET + 7
    
    def C256(code: int, mode: Literal['fg', 'bg'] = 'fg') -> str:
        '''
        Get ANSI color code from 256 color terminals.
        '''
        
        return f'\x1b[{38 if mode == "fg" else 48};5;{code}m'
    
    def get(name: str) -> int:
        '''
        Get a color by name.
        '''
        
        return COLOR.__dict__.get(name.upper())

class BORDER:
    CLASSIC = '-|++++'
    NORMAL  = '─│┌┐└┘'
    HEAVY   = '━┃┏┓┗┛'
    DOUBLE  = '═║╔╗╚╝'
    DOUBLE1 = '═│╒╕╘╛'
    DOUBLE2 = '─║╓╖╙╜'
    ROUNDED = '─│╭╮╰╯'
    BLOCK   = '██████'
    
class VALIDATOR:
    
    def exists(string: str):
        return string
    
    def is_int(string: str):
        return int(string)
    
    def is_bool(string: str):
        return string in '01'

# --- Default configuration --- #
MAX_WIDTH    = 100              #
FONT_COLOR   = COLOR.NORMAL     #
BORDER_TYPE  = BORDER.NORMAL    #
BORDER_COLOR = COLOR.GREY       #
#  ---------------------------- #

_justify = Literal['left', 'right', 'center']

_justifier = {
    'left'  : str.ljust,
    'right' : str.rjust,
    'center': str.center
}

_re_ansi   = re.compile(r'\x1b\[(.+?)m'       )
_re_italic = re.compile(r'(\*)(.+?)(\*)'      )
_re_bold   = re.compile(r'(\*\*)(.+?)(\*\*)'  )
_re_color  = re.compile(r'\$([A-Z\d]+)\((.+?)\)')

def _ansi(code: int | str = 0) -> str:
    
    if '\x1b' in str(code):
        return code
    
    return f'\x1b[{code}m'

def width() -> int:
    '''
    Get the max allowed terminal width.
    '''
    
    return min(MAX_WIDTH, os.get_terminal_size().columns)

def clear() -> None:
    '''
    Clear the console.
    '''
    
    print('\x1b[2j')

def _wrap(text: str, width: int) -> list[str]:
    '''
    Wrap a text line.
    '''
    
    if not text:
        return ['']
    
    res = ['']
    
    for word in text.split():
        
        if len(word) > width - 1:
            word = word[:width - 2] + '-'
        
        if len(res[-1]) + len(word) + 1 < width:
            res[-1] += word + ' '
        
        else:
            res.append(word + ' ')
    
    return [l for l in res if l]

def _header(title: str = None, justify: _justify = 'left') -> None:
    '''
    Print a header.
    '''
    
    title = f' {title.strip()} ' if title else ''
    line = _justifier[justify](title, width() - 2, BORDER_TYPE[0])
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[2]
          + line
          + BORDER_TYPE[3]
          + _ansi())

def _footer() -> None:
    '''
    Print a footer.
    '''
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[4]
          + BORDER_TYPE[0] * (width() - 2)
          + BORDER_TYPE[5]
          + _ansi())

def banner(text: str | list[str],
           justify: _justify = 'center',
           title: str = None,
           justify_title: _justify = 'left',
           wrap_lines: bool = True) -> None:
    '''
    Write a banner.
    '''
    
    lines = text
    if isinstance(text, str):
        lines = text.split('\n')
        
    _header(title, justify_title)
    
    for glob in lines:
        
        if wrap_lines:
            wrapped_glob = _wrap(glob, width() - 4)
        
        else:
            # if len(glob) > width() - 4:
            #     wrapped_glob = [glob[:width() - 7] + '...']
            # else:
            wrapped_glob = [glob]
        
        for line in wrapped_glob:
            
            formated = _re_bold.sub(_ansi(1) + '\g<2>' + _ansi(22), f' {line} ')
            formated = _re_italic.sub(_ansi(3) + '\g<2>' + _ansi(23), formated)
            formated = _re_color.sub('\x1b[{\g<1>}m\g<2>\x1b[0m', formated).format(**COLOR.__dict__)
            
            ansi_length = sum(map(lambda m: len(m) + 3, _re_ansi.findall(formated)))
            
            body = _justifier[justify](formated, width() - 2 + ansi_length)
            
            print(_ansi(BORDER_COLOR)
                + BORDER_TYPE[1]
                + _ansi(FONT_COLOR)
                + body
                + _ansi(BORDER_COLOR)
                + BORDER_TYPE[1]
                + _ansi())
        
    _footer()

def _input(col: int,
           error_prompt: str,
           validator: Callable[[str], bool] = None) -> str:
    '''
    Wrapped input.
    '''
    
    while 1:
        try:
            res = input(f'\x1b[2A\x1b[{ col }C')
            if validator:
                assert validator(res)
            print()
            return res
        
        except KeyboardInterrupt:
            print('\n')
            exit()
        
        except:
            print(f'\x1b[1A\x1b[2K' + error_prompt + '\x1b[1B')

def entry(prompt: str,
          error_prompt: str = None,
          validator: Callable[[str], bool] = VALIDATOR.exists) -> str:
    '''
    Write an entry field.
    '''

    if error_prompt is None:
        error_prompt = '!'
    
    if len(prompt) > len(error_prompt):
        error_prompt = error_prompt.center(len(prompt), ' ')
    
    else:
        prompt = prompt.center(len(error_prompt), ' ')
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[2]
          + BORDER_TYPE[0] * (len(prompt) + 2)
          + BORDER_TYPE[3])
    
    print(BORDER_TYPE[1]
        + _ansi(FONT_COLOR)
        + f' {prompt} '
        + _ansi(BORDER_COLOR)
        + BORDER_TYPE[1]
        + _ansi())
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[4]
          + BORDER_TYPE[0] * (len(prompt) + 2)
          + BORDER_TYPE[5]
          + _ansi())
    
    return _input(len(prompt) + 5,
                  (_ansi(BORDER_COLOR)
                   + BORDER_TYPE[1]
                   + _ansi(COLOR.RED)
                   + f' {error_prompt} '
                   + _ansi(BORDER_COLOR)
                   + BORDER_TYPE[1]
                   + _ansi()),
                  validator)

def separator(title: str = None,
              justify: _justify = 'left') -> None:
    '''
    Print a separator.
    '''
    
    body = _justifier[justify](f' {title} ' or '', width(), BORDER_TYPE[0])
    
    print(_ansi(BORDER_COLOR) + body + _ansi())

def select_large(options: list[str],
                 prompt: str = 'Select an option >',
                 error_prompt: str = None,
                 justify: _justify = 'left',
                 title: str = None,
                 justify_title: _justify = 'left',
                 wrap_lines: bool = True) -> int:
    '''
    Select a list.
    '''
    
    if error_prompt is None:
        error_prompt = '!'
    
    if len(prompt) > len(error_prompt):
        error_prompt = error_prompt.center(len(prompt), ' ')
    
    else:
        prompt = prompt.center(len(error_prompt), ' ')
    
    index_space = len(str(len(options)))
    
    banner(
        text = [f'{i + 1: >{index_space}}. {opt}' for i, opt in enumerate(options)],
        justify = justify,
        title = title,
        justify_title = justify_title,
        wrap_lines = wrap_lines
    )
    
    # Erase last line and print prompt
    print('\x1b[1A\x1b[2K'
          + _ansi(BORDER_COLOR)
          + BORDER_TYPE[1]
          + ' ' * (len(prompt) + 2)
          + BORDER_TYPE[2]
          + BORDER_TYPE[0] * (width() - len(prompt) - 5)
          + BORDER_TYPE[5])
    
    print(BORDER_TYPE[1]
        + _ansi(FONT_COLOR)
        + f' {prompt} '
        + _ansi(BORDER_COLOR)
        + BORDER_TYPE[1]
        + _ansi())
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[4]
          + BORDER_TYPE[0] * (len(prompt) + 2)
          + BORDER_TYPE[5]
          + _ansi())
    
    val = lambda i: 0 < int(i) < len(options) + 1
    
    return int(_input(len(prompt) + 5,
                      (_ansi(BORDER_COLOR)
                       + BORDER_TYPE[1]
                       + _ansi(COLOR.RED)
                       + f' {error_prompt} '
                       + _ansi(BORDER_COLOR)
                       + BORDER_TYPE[1]
                       + _ansi()),
                      val)) - 1

def entry_large(text: str | list[str],
                prompt: str = 'Select an option >',
                error_prompt: str = None,
                justify: _justify = 'left',
                title: str = None,
                justify_title: _justify = 'left',
                validator: Callable[[str], bool] = VALIDATOR.exists,
                wrap_lines: bool = True) -> str:
    '''
    An entry box with a prompt attached to it.
    '''
    
    if error_prompt is None:
        error_prompt = '!'
    
    if len(prompt) > len(error_prompt):
        error_prompt = error_prompt.center(len(prompt), ' ')
    
    else:
        prompt = prompt.center(len(error_prompt), ' ')
    
    banner(
        text = text,
        justify = justify,
        title = title,
        justify_title = justify_title,
        wrap_lines = wrap_lines
    )
    
    # Erase last line and print prompt
    print('\x1b[1A\x1b[2K'
          + _ansi(BORDER_COLOR)
          + BORDER_TYPE[1]
          + ' ' * (len(prompt) + 2)
          + BORDER_TYPE[2]
          + BORDER_TYPE[0] * (width() - len(prompt) - 5)
          + BORDER_TYPE[5])
    
    print(BORDER_TYPE[1]
        + _ansi(FONT_COLOR)
        + f' {prompt} '
        + _ansi(BORDER_COLOR)
        + BORDER_TYPE[1]
        + _ansi())
    
    print(_ansi(BORDER_COLOR)
          + BORDER_TYPE[4]
          + BORDER_TYPE[0] * (len(prompt) + 2)
          + BORDER_TYPE[5]
          + _ansi())
    
    err_pompt = (_ansi(BORDER_COLOR)
                 + BORDER_TYPE[1]
                 + _ansi(COLOR.RED)
                 + f' {error_prompt} '
                 + _ansi(BORDER_COLOR)
                 + BORDER_TYPE[1]
                 + _ansi())
    
    return _input(len(prompt) + 5, err_pompt, validator)


class awaiter:
    '''
    An awaiter loader.
    '''
    
    def __init__(self,
                 desc: str = '',
                 chars: str = '/-\\|',
                 speed : int = .5) -> None:
        '''
        Initialise a new awaiter instance.
        '''
        
        self.desc = desc
        self.chars = chars
        self.running = False
        self.speed = speed
        
        self.index = 0
    
    def __enter__(self) -> None:
        '''
        Enter a context manager.
        '''
        
        self.index = 0
        self.running = True
        print('\x1b[25h', end = '')
        thread = threading.Thread(target = self._run)
        thread.start()
    
    def __exit__(self, *args, **kwargs) -> None:
        '''
        Exit a context manager.
        '''
        
        self.running = False
        print('\r\x1b[25l', end = '')
    
    def _run(self) -> None:
        '''
        Run thread instance.
        '''
        
        while self.running:
            
            char = self.chars[self.index % len(self.chars)]
            
            print('\r' + _ansi(FONT_COLOR) + self.desc + ' '
                  + _ansi(BORDER_COLOR) + char + _ansi(),
                  end = '')
            
            self.index += 1
            time.sleep(self.speed)

# EOF