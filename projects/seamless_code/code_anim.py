#!/usr/bin/env python

from manimlib.animation.creation import Write, ShowCreation
from manimlib.scene.scene import Scene

"""
from functools import reduce
import operator as op
import os
from manimlib.constants import *
from manimlib.mobject.geometry import Line
from manimlib.mobject.svg.svg_mobject import SVGMobject
from manimlib.mobject.svg.svg_mobject import VMobjectFromSVGPathstring
from manimlib.mobject.types.vectorized_mobject import VGroup
from manimlib.mobject.types.vectorized_mobject import VectorizedPoint
from manimlib.utils.config_ops import digest_config
from manimlib.utils.strings import split_string_list_to_isolate_substrings
import manimlib.utils.tex_file_writing as TFW

from manimlib.mobject.svg.tex_mobject import TexSymbol   

from manimlib.animation.creation import Write, ShowCreation
from manimlib.scene.scene import Scene

from local_code_mobject import Code
"""

import html
from manimlib.constants import *
from manimlib.container.container import Container
from manimlib.mobject.geometry import Rectangle, Dot, RoundedRectangle
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
        "run_time": 1,
        "font": 'Ubuntu Mono',
        'stroke_width': 0,
        'indentation_char': "  ",
        'insert_line_no': False,
        'line_no_from': 1,
        "line_no_buff": 0.4,
        'style': 'vim',
        'language': 'cpp', # TODO: MOVE
        'generate_html_file': False,
        'default_text_color': WHITE,
        'lines_to_highlight': [],
        'highlight_color': GOLD,
        'highlight_opacity': 0.5,
        'highlight_buff': 0.025,
    }

    def __init__(self, file_name=None, **kwargs):
        Container.__init__(self, **kwargs)
        self.file_name = file_name or self.file_name
        self.ensure_valid_file()
        
        self.style = self.style.lower()
        self.gen_html_string()
        self.gen_code_json()

        self.code = self.gen_colored_lines()
        self.background = self.highlight_lines()
        print(self.background)

        if self.insert_line_no:
            self.line_numbers = self.gen_line_numbers()
            self.line_numbers.next_to(self.code, direction=LEFT, buff=self.line_no_buff)
            VGroup.__init__(self, self.line_numbers, *self.code, *self.background, **kwargs)
        else:
            VGroup.__init__(self, *self.code, *self.background, **kwargs)

        self.move_to(np.array([0, 0, 0]))

    def apply_points_function_about_point(self, func, about_point=None, about_edge=None):
        if about_point is None:
            if about_edge is None:
                about_edge = self.get_corner(UP + LEFT)
            about_point = self.get_critical_point(about_edge)
        for mob in self.family_members_with_points():
            mob.points -= about_point
            mob.points = func(mob.points)
            mob.points += about_point
        return self

    def ensure_valid_file(self):
        if self.file_name is None:
            raise Exception("Must specify file for Code")
        possible_paths = [
            os.path.join(os.path.join("assets", "codes"), self.file_name),
            self.file_name,
        ]
        for path in possible_paths:
            if os.path.exists(path):
                self.file_path = path
                return
        raise IOError("No file matching %s in codes directory" %
                      self.file_name)

    def gen_line_numbers(self):
        line_numbers_array = []
        for line_no in range(0, self.code_json.__len__()):
            number = str(self.line_no_from + line_no)
            line_numbers_array.append(number)
        line_numbers = Paragraph(*[i for i in line_numbers_array], line_spacing=self.line_spacing,
                            alignment="right", font=self.font, stroke_width=self.stroke_width).scale(self.scale_factor)
        return line_numbers

    def gen_colored_lines(self):
        lines_text = []
        for line_no in range(0, self.code_json.__len__()):
            line_str = ""
            for word_index in range(self.code_json[line_no].__len__()):
                line_str = line_str + self.code_json[line_no][word_index][0]
            lines_text.append(self.tab_spaces[line_no] * "\t" + line_str)
        code = Paragraph(*[i for i in lines_text], line_spacing=self.line_spacing, tab_width=self.tab_width,
                    alignment="left", font=self.font, stroke_width=self.stroke_width).scale(self.scale_factor)
        for line_no in range(code.__len__()):
            line = code[line_no]
            line_char_index = self.tab_spaces[line_no]
            for word_index in range(self.code_json[line_no].__len__()):
                line[line_char_index:line_char_index + self.code_json[line_no][word_index][0].__len__()].set_color(
                    self.code_json[line_no][word_index][1])
                line_char_index += self.code_json[line_no][word_index][0].__len__()
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

    def gen_html_string(self):
        file = open(self.file_path, "r")
        code_str = file.read()
        file.close()

        self.html_string = self.hilite_me(code_str, {}, self.style, "border:solid gray;border-width:.1em .1em .1em .8em;padding:.2em .6em;")
        if self.insert_line_no:
            self.html_string = self.insert_line_numbers(self.html_string)

        if self.generate_html_file:
            os.makedirs(os.path.join("assets", "codes", "generated_html_files"), exist_ok=True)
            file = open(os.path.join("assets", "codes", "generated_html_files", self.file_name + ".html"), "w")
            file.write(self.html_string)
            file.close()

    def gen_code_json(self):
        for i in range(3, -1, -1):
            self.html_string = self.html_string.replace("</" + " " * i, "</")
        for i in range(10, -1, -1):
            self.html_string = self.html_string.replace("</span>" + " " * i, " " * i + "</span>")
        self.html_string = self.html_string.replace("background-color:", "background:")

        if self.insert_line_no:
            start_point = self.html_string.find("</td><td><pre")
            start_point = start_point + 9
        else:
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
        for line_index in range(0, lines.__len__()):
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
            # print(lines[line_index])
            lines[line_index] = self.correct_non_span(lines[line_index])
            # print(lines[line_index])
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
        for i in range(0, words.__len__()):
            if i != words.__len__() - 1:
                j = words[i].find("<span")
            else:
                j = words[i].__len__()
            temp = ""
            starti = -1
            for k in range(0, j):
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


    def hilite_me(self, code, options, style, divstyles):
        style = style or 'colorful'
        defstyles = 'overflow:auto;width:auto;'

        formatter = HtmlFormatter(style=style,
                                linenos=False,
                                noclasses=True,
                                cssclass='',
                                cssstyles=defstyles + divstyles,
                                prestyles='margin: 0')
        html = highlight(code, get_lexer_by_name(self.language, **options), formatter)
        return html

    def insert_line_numbers(self, html):
        match = re.search('(<pre[^>]*>)(.*)(</pre>)', html, re.DOTALL)
        if not match: return html

        pre_open = match.group(1)
        pre = match.group(2)
        pre_close = match.group(3)

        html = html.replace(pre_close, '</pre></td></tr></table>')
        numbers = range(1, pre.count('\n') + 1)
        format = '%' + str(len(str(numbers[-1]))) + 'i'
        lines = '\n'.join(format % i for i in numbers)
        html = html.replace(pre_open, '<table><tr><td>' + pre_open + lines + '</pre></td><td>' + pre_open)
        return html


class CodeAnim(Scene):
    def construct(self):
        arr = [1, 3, 4]
        code_py = Code('LaTeXExperiment/code_0.py', language='python', lines_to_highlight=arr, background="window").shift(UP)
        self.add(code_py)
        self.wait(3.)
        print(code_py.html_string)
        code_cpp = Code('LaTeXExperiment/code_0.cc', language='cpp', lines_to_highlight=arr, background="window").shift(0.5*DOWN)
        self.add(code_cpp)
        self.wait(3.)