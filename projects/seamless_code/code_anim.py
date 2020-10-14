import html

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
        self.html_string = self.hilite_me(self.code_str, self.style, self.highlight_options)

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

        lines_text = [self.tab_spaces[line_no] * '\t' + 
                        "".join(self.code_json[line_no][word_index][0] for word_index in range(self.code_json[line_no].__len__()))
                                for line_no in range(self.code_json.__len__())]

        code = Paragraph(*lines_text,
                        line_spacing=self.line_spacing,
                        tab_width=self.tab_width,
                        alignment="left",
                        font=self.font,
                        stroke_width=self.stroke_width).scale(self.scale_factor)

        for line_no in range(code.__len__()):
            cur_index = self.tab_spaces[line_no]
            for word_index in range(self.code_json[line_no].__len__()):
                cur_length = self.code_json[line_no][word_index][0].__len__()
                code[line_no][cur_index:cur_index + cur_length].set_color(self.code_json[line_no][word_index][1])
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

    def hilite_me(self, code, style, options={}):
        return highlight(self.code_str, get_lexer_by_name(self.language, **self.highlight_options), 
                        HtmlFormatter(
                                style=self.style,
                                linenos=False,
                                noclasses=True,
                                cssclass='',
                                cssstyles=self.hilite_divstyles + self.hilite_defstyles,
                                prestyles='margin: 0'))

    ## AIDS

    def gen_code_json(self):
        for i in range(3, -1, -1):
            self.html_string = self.html_string.replace("</" + " " * i, "</")
        for i in range(10, -1, -1):
            self.html_string = self.html_string.replace("</span>" + " " * i, " " * i + "</span>")
        self.html_string = self.html_string.replace("background-color:", "background:")

        start_point = self.html_string.find("<pre")

        self.html_string = self.html_string[start_point:]
        # print(self.html_string)
        lines = self.html_string.split("\n")
        lines = lines[0:lines.__len__() - 2]
        start_point = lines[0].find(">")
        lines[0] = lines[0][start_point + 1:]
        # print(lines)
        self.code_json = []
        self.tab_spaces = []
        code_json_line_index = -1
        for line_index in range(lines.__len__()):
            if lines[line_index].__len__() == 0:
                continue
            # print(lines[line_index])
            self.code_json.append([])
            code_json_line_index = code_json_line_index + 1
            if lines[line_index].startswith(self.indentation_char):
                start_point = lines[line_index].find("<")
                starting_string = lines[line_index][:start_point]
                indentation_char_count = lines[line_index][:start_point].count(self.indentation_char)
                if starting_string.__len__() != indentation_char_count * self.indentation_char.__len__():
                    lines[line_index] = "\t" * indentation_char_count + starting_string[starting_string.rfind(
                        self.indentation_char) + self.indentation_char.__len__():] + \
                                        lines[line_index][start_point:]
                else:
                    lines[line_index] = "\t" * indentation_char_count + lines[line_index][start_point:]

            indentation_char_count = 0
            while lines[line_index][indentation_char_count] == '\t':
                indentation_char_count = indentation_char_count + 1
            self.tab_spaces.append(indentation_char_count)

            # TODO: REMOVE ALL OF THIS IF IT GIVES NO PROBLEMS
            print("A:", lines[line_index])
            stra = lines[line_index].__str__
            lines[line_index] = self.correct_non_span(lines[line_index])
            strb = lines[line_index].__str__
            print("B:", lines[line_index])
            assert(stra == strb)

            words = lines[line_index].split("<span")
            for word_index in range(1, words.__len__()):
                color_index = words[word_index].find("color:")
                if color_index == -1:
                    color = self.default_text_color
                else:
                    starti = words[word_index][color_index:].find("#")
                    color = words[word_index][color_index + starti:color_index + starti + 7]

                start_point = words[word_index].find(">")
                end_point = words[word_index].find("</span>")
                text = words[word_index][start_point + 1:end_point]
                text = html.unescape(text)
                if text != "":
                    # print(text, "'" + color + "'")
                    self.code_json[code_json_line_index].append([text, color])
        # print(self.code_json)

    def correct_non_span(self, line_str):
        words = line_str.split("</span>")
        line_str = ""
        for i in range(words.__len__()):
            if i != words.__len__() - 1:
                j = words[i].find("<span")
            else:
                j = words[i].__len__()
            temp = ""
            starti = -1
            for k in range(j):
                if words[i][k] == "\t" and starti == -1:
                    continue
                else:
                    if starti == -1: starti = k
                    temp = temp + words[i][k]
            if temp != "":
                if i != words.__len__() - 1:
                    temp = '<span style="color:' + self.default_text_color + '">' + words[i][starti:j] + "</span>"
                else:
                    temp = '<span style="color:' + self.default_text_color + '">' + words[i][starti:j]
                temp = temp + words[i][j:]
                words[i] = temp
            if words[i] != "":
                line_str = line_str + words[i] + "</span>"
        return line_str


from manimlib.animation.creation import Write, ShowCreation
from manimlib.scene.scene import Scene

class CodeAnim(Scene):
    def construct(self):
        arr = [1, 3, 4]
        print_line_numbers=True
        code_py = Code('LaTeXExperiment/code_0.py', language='python', style='vim', highlight_color=YELLOW, lines_to_highlight=arr, background="window", insert_line_no=print_line_numbers).shift(UP)
        self.add(code_py)
        self.wait(3.)
        print(code_py.html_string)
        code_cpp = Code('LaTeXExperiment/code_0.cc', language='cpp', style='vim', highlight_color=YELLOW, lines_to_highlight=arr, background="window", insert_line_no=print_line_numbers).shift(0.5*DOWN)
        self.add(code_cpp)
        self.wait(3.)
