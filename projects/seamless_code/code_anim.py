from html.parser import HTMLParser
from manimlib.utils.config_ops import digest_config

import manimlib.constants as consts
from manimlib.mobject.shape_matchers import SurroundingRectangle
from manimlib.mobject.svg.text_mobject import Paragraph, TextWithFixHeight
from manimlib.mobject.types.vectorized_mobject import VGroup
from manimlib.mobject.svg.svg_mobject import VMobjectFromSVGPathstring

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

class Code(VGroup):
    CONFIG = {
        "tab_width": 2,
        "font": 'Ubuntu Mono',
        'indentation_char': "  ",
        'show_line_numbers': False,
        'line_no_from': 1,
        "line_no_buff": 0.4,
        'style': 'vim',
        'language': 'cpp', # TODO: MOVE
        'default_text_color': consts.WHITE,
        'lines_to_highlight': [],
        'highlight_color': consts.GOLD,
        'highlight_opacity': 0.5,
        'highlight_buff': 0.025,
        'highlight_options': {},
    }

    def __init__(self, file_name=None, code_str=None, **kwargs):
        digest_config(self, kwargs)
        if code_str is None and file_name is None:
            raise Exception("Both CodeString and FileName unset")
        if code_str is not None and file_name is not None:
            raise Exception("Both CodeString and FileName set")
        
        self.file_name = file_name
        self.code_str = (code_str if code_str else open(file_name, "r").read()).replace('\t', ' '*self.tab_width)
        
        self.code = self.get_code()
        self.background = self.highlight_lines()

        objs = [*self.code, *self.background]
        if self.show_line_numbers:
            objs = [self.gen_line_numbers().next_to(self.code, direction=consts.LEFT, buff=self.line_no_buff)] + objs
        VGroup.__init__(self, *objs, **kwargs)

    def gen_line_numbers(self):
        return Paragraph(*[str(self.line_no_from + line_no) for line_no in range(self.style_data.__len__())], alignment="right", font=self.font)

    def get_code(self):
        self.style_data = self.gen_style_data()

        lines_text = ["".join(self.style_data[line_no][word_index]["text"] for word_index in range(self.style_data[line_no].__len__()))
                                for line_no in range(self.style_data.__len__())]

        code = Paragraph(*lines_text, alignment="left", font=self.font)

        for line_no in range(code.__len__()):
            for char_index in range(self.style_data[line_no].__len__()):
                code[line_no][char_index].set_color(self.style_data[line_no][char_index]["color"])
                code[line_no][char_index].weight = self.style_data[line_no][char_index]["font-weight"].upper()
                print(self.style_data[line_no][char_index]["font-weight"].upper())

        return code

    def highlight_lines(self):
        return [
            SurroundingRectangle(
                self.code[line_no],
                buff=self.highlight_buff,
                color=self.highlight_color,
                fill_color=self.highlight_color,
                fill_opacity=(self.highlight_opacity if line_no + 1 in self.lines_to_highlight else 0.),
                stroke_width=0
            ) for line_no in range(self.code.__len__())] 

    def gen_style_data(self):
        class CodeHTMLParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.style_data = [[]]
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
                        assert(data_key in ["color", "font-weight"]), "Unexpected DataKey"
                        self.cur_format[data_key] = data_val

            def handle_data(self, data):
                lines = data.splitlines()
                for i in range(len(lines)):
                    if i > 0:
                        self.style_data.append([])
                    new_info = self.cur_format.copy()
                    for c in lines[i]:
                        new_info["text"] = c
                        self.style_data[-1].append(new_info.copy())

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

        self.html_string = highlight(
                self.code_str,
                get_lexer_by_name(self.language, **self.highlight_options), 
                HtmlFormatter(style=self.style.lower(), noclasses=True))

        html_parser = CodeHTMLParser()
        html_parser.feed(self.html_string)
        html_parser.close()
        print("STYLE DATA:", html_parser.style_data)
        self.style_data = html_parser.style_data
        return self.style_data


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
