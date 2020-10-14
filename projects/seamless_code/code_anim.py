import html
from html.parser import HTMLParser

from manimlib.utils.config_ops import digest_config

from manimlib.constants import *
from manimlib.mobject.shape_matchers import SurroundingRectangle, BackgroundRectangle
from manimlib.mobject.svg.text_mobject import Paragraph
from manimlib.mobject.types.vectorized_mobject import VGroup
from manimlib.mobject.types.vectorized_mobject import VMobject

import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

'''
1) Code is VGroup() with three things
    1.1) Code[0] is Code.background_mobject
        which can be a 
            1.1.1) Rectangle() if background == "rectangle" 
            1.1.2) VGroup() of Rectangle() and Dot() for three buttons if background == "window" 
    1.2) Code[1] is Code.line_numbers Which is a Paragraph() object, this mean you can use 
                Code.line_numbers[0] or Code[1][0] to access first line number 
    1.3) Code[2] is Code.code
        1.3.1) Which is a Paragraph() with color highlighted, this mean you can use 
            Code.code[1] or Code[2][1] 
                line number 1
            Code.code[1][0] or Code.code[1][0] 
                first character of line number 1
            Code.code[1][0:5] or Code.code[1][0:5] 
                first five characters of line number 1
'''

class Code(VGroup):
    CONFIG = {
        "tab_width": 3,
        "line_spacing": 0.1,
        "scale_factor": 0.5,
        "font": 'Ubuntu Mono',
        'stroke_width': 0,
        'indentation_char': "  ",
        'insert_line_no': False,
        'line_no_from': 1,
        "line_no_buff": 0.4,
        'style': 'vim',
        'language': 'cpp', # TODO: MOVE
        'default_text_color': WHITE,
        'lines_to_highlight': [],
        'highlight_color': GOLD,
        'highlight_opacity': 0.5,
        'highlight_buff': 0.025,
        'highlight_options': {},
        'hilite_divstyles': "border:solid gray;border-width:.1em .1em .1em .8em;padding:.2em .6em;",
        'hilite_defstyles': 'overflow:auto;width:auto;',
    }

    def __init__(self, file_name=None, code_str=None, **kwargs):
        digest_config(self, kwargs)
        if code_str is None and file_name is None:
            raise Exception("Both CodeString and FileName unset")
        if code_str is not None and file_name is not None:
            raise Exception("Both CodeString and FileName set")
        
        self.file_name = file_name
        self.code_str = code_str if code_str else open(file_name, "r").read()
        
        self.style = self.style.lower()
        self.html_string = self.hilite_me()

        self.code = self.gen_colored_lines()
        self.background = self.highlight_lines()

        objs = [*self.code, *self.background]
        if self.insert_line_no:
            objs = [self.gen_line_numbers().next_to(self.code, direction=LEFT, buff=self.line_no_buff)] + objs
        VGroup.__init__(self, *objs, **kwargs)

    def gen_line_numbers(self):
        return Paragraph(*[str(self.line_no_from + line_no) for line_no in range(self.code_json.__len__())],
                    line_spacing=self.line_spacing,
                    alignment="right",
                    font=self.font,
                    stroke_width=self.stroke_width).scale(self.scale_factor)

    def gen_colored_lines(self):
        self.gen_code_json()

        lines_text = ["".join(self.code_json[line_no][word_index]["text"] for word_index in range(self.code_json[line_no].__len__()))
                                for line_no in range(self.code_json.__len__())]

        code = Paragraph(*lines_text,
                        line_spacing=self.line_spacing,
                        tab_width=self.tab_width,
                        alignment="left",
                        font=self.font,
                        stroke_width=self.stroke_width).scale(self.scale_factor)

        for line_no in range(code.__len__()):
            cur_index = 0
            for word_index in range(self.code_json[line_no].__len__()):
                cur_length = self.code_json[line_no][word_index]["text"].__len__()
                code[line_no][cur_index:cur_index + cur_length].set_color(self.code_json[line_no][word_index]["color"])
                code[line_no][cur_index:cur_index + cur_length].weight = self.code_json[line_no][word_index]["font-weight"].upper()
                cur_index += cur_length

        return code

    def highlight_lines(self):
        return [
            SurroundingRectangle(
                self.code[line_no],
                buff=self.highlight_buff,
                color=self.highlight_color,
                fill_color=self.highlight_color,
                stroke_width=0,
                fill_opacity=(self.highlight_opacity if line_no + 1 in self.lines_to_highlight else 0.2)
            )
           for line_no in range(self.code.__len__())
        ]

    def hilite_me(self):
        return highlight(
                    self.code_str,
                    get_lexer_by_name(self.language, **self.highlight_options), 
                    HtmlFormatter(
                            style=self.style,
                            linenos=False,
                            noclasses=True,
                            cssclass='',
                            cssstyles=self.hilite_divstyles + self.hilite_defstyles,
                            prestyles='margin: 0'))

    def gen_code_json(self):
        class CodeHTMLParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.code_json = [[]]
                self.default_format = {"color" : "#ffffff", "font-weight" : "normal"}
                self.cur_format = self.default_format.copy()
                self.html_ctr = 0

            def handle_starttag(self, tag, attrs):
                if tag in ['div', 'pre']:
                    return
                self.html_ctr += 1
                assert(self.html_ctr == 1), "Too many counters"
                assert(tag == 'span'), "Unexpected Tag {}".format(tag)
                for key, val in attrs:
                    assert(key == 'style'), "Unexpected Key {}".format(key)
                    attr_data = val.split(';')
                    assert(1 <= len(attr_data) <= 2), "Wrong number of args"
                    for data in attr_data:
                        assert(len(data.split(':')) == 2), "Wrong format"
                        data_key, data_val = data.split(':')[0].strip(), data.split(':')[1].strip()
                        self.cur_format[data_key] = data_val

            def handle_data(self, data):
                lines = data.splitlines()
                for i in range(len(lines)):
                    if i > 0:
                        self.code_json.append([])
                    new_info = self.cur_format.copy()
                    new_info["text"] = lines[i]
                    self.code_json[-1].append(new_info)

            def handle_endtag(self, tag):
                if tag in ['div', 'pre']:
                    return
                self.html_ctr -= 1
                self.cur_format = self.default_format.copy()

            def handle_startendtag(self, tag, attrs):
                raise Exception("Unexpected StartEndTag {}".format(tag))
            def handle_entityref(self, name):
                raise Exception("Unexpected EntityRef {}".format(name))
            def handle_charref(self, name):
                raise Exception("Unexpected CharRef {}".format(name))
            def handle_comment(self, data):
                raise Exception("Unexpected Comment {}".format(data))
            def handle_decl(self, decl):
                raise Exception("Unexpected Decl {}".format(decl))
            def handle_pi(self, data):
                raise Exception("Unexpected PI {}".format(data))
            def unknown_decl(self, data):
                raise Exception("Unexpected UnknownDecl {}".format(data))

        html_parser = CodeHTMLParser()
        html_parser.feed(self.html_string)
        self.code_json = html_parser.code_json
        print("CODE JSON:", self.code_json)
        html_parser.close()


from manimlib.animation.creation import Write, ShowCreation
from manimlib.scene.scene import Scene

"""
dict_keys(['default', 'emacs', 'friendly', 'colorful', 'autumn', 'murphy', 'manni', 'monokai', 'perldoc',
'pastie', 'borland', 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode', 'igor',
'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu', 'arduino', 'rainbow_dash', 'abap',
'solarized-dark', 'solarized-light', 'sas', 'stata', 'stata-light', 'stata-dark', 'inkpot'])
"""

class CodeAnim(Scene):
    def construct(self):
        arr = []
        print_line_numbers=True
        code_py = Code('LaTeXExperiment/code_0.py', language='python', style='rainbow_dash', highlight_color=YELLOW, lines_to_highlight=arr, insert_line_no=print_line_numbers).shift(UP)
        self.add(code_py)
        self.wait(3.)
        print(code_py.html_string)
        code_cpp = Code('LaTeXExperiment/code_0.cc', language='cpp', style='rainbow_dash', highlight_color=YELLOW, lines_to_highlight=arr, insert_line_no=print_line_numbers).shift(DOWN)
        self.add(code_cpp)
        self.wait(3.)
