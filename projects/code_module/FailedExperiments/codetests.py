#!/usr/bin/env python

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

def tex_to_dvi(tex_file):
    result = tex_file.replace(".tex", ".dvi")
    if not os.path.exists(result):
        commands = [
            "latex",
            "-shell-escape",
            "-interaction=batchmode",
            "-halt-on-error",
            #"-output-directory=\"{}\"".format(TEX_DIR),
            "\"{}\"".format(tex_file),
            ">",
            "holA.LOG"
            #os.devnull
        ]
        print("Executing: ", " ".join(commands))
        exit_code = os.system(" ".join(commands))
        if exit_code != 0:
            log_file = tex_file.replace(".tex", ".log")
            raise Exception(
                ("Latex error converting to dvi. ") +
                "See log output above or the log file: %s" % log_file)
    return result

def tex_to_svg_file(expression, template_tex_file_body):
    tex_file = TFW.generate_tex_file(expression, template_tex_file_body)
    dvi_file = tex_to_dvi(tex_file)
    return TFW.dvi_to_svg(dvi_file)

##### MOBJECT
TEX_MOB_SCALE_FACTOR = 0.05

class SingleStringTexMobject(SVGMobject):
    CONFIG = {
        "template_tex_file_body": TEMPLATE_TEXT_FILE_BODY,
        "stroke_width": 0,
        "fill_opacity": 1.0,
        "background_stroke_width": 1,
        "background_stroke_color": BLACK,
        "should_center": True,
        "height": None,
        "organize_left_to_right": False,
        "alignment": "",
    }

    def __init__(self, tex_string, **kwargs):
        digest_config(self, kwargs)
        assert(isinstance(tex_string, str))
        self.tex_string = tex_string
        file_name = tex_to_svg_file(
            self.get_modified_expression(tex_string),
            self.template_tex_file_body
        )
        SVGMobject.__init__(self, file_name=file_name, **kwargs)
        if self.height is None:
            self.scale(TEX_MOB_SCALE_FACTOR)
        if self.organize_left_to_right:
            self.organize_submobjects_left_to_right()

    def get_modified_expression(self, tex_string):
        result = self.alignment + " " + tex_string
        result = result.strip()
        result = self.modify_special_strings(result)
        return result

    def modify_special_strings(self, tex):
        tex = self.remove_stray_braces(tex)
        should_add_filler = reduce(op.or_, [
            # Fraction line needs something to be over
            tex == "\\over",
            tex == "\\overline",
            # Makesure sqrt has overbar
            tex == "\\sqrt",
            # Need to add blank subscript or superscript
            tex.endswith("_"),
            tex.endswith("^"),
            tex.endswith("dot"),
        ])
        if should_add_filler:
            filler = "{\\quad}"
            tex += filler

        if tex == "\\substack":
            tex = "\\quad"

        if tex == "":
            tex = "\\quad"

        # Handle imbalanced \left and \right
        num_lefts, num_rights = [
            len([
                s for s in tex.split(substr)[1:]
                if s and s[0] in "(){}[]|.\\"
            ])
            for substr in ("\\left", "\\right")
        ]
        if num_lefts != num_rights:
            tex = tex.replace("\\left", "\\big")
            tex = tex.replace("\\right", "\\big")

        for context in ["array"]:
            begin_in = ("\\begin{%s}" % context) in tex
            end_in = ("\\end{%s}" % context) in tex
            if begin_in ^ end_in:
                # Just turn this into a blank string,
                # which means caller should leave a
                # stray \\begin{...} with other symbols
                tex = ""
        return tex

    def remove_stray_braces(self, tex):
        """
        Makes TexMobject resiliant to unmatched { at start
        """
        num_lefts, num_rights = [
            tex.count(char)
            for char in "{}"
        ]
        while num_rights > num_lefts:
            tex = "{" + tex
            num_lefts += 1
        while num_lefts > num_rights:
            tex = tex + "}"
            num_rights += 1
        return tex

    def get_tex_string(self):
        return self.tex_string

    def path_string_to_mobject(self, path_string):
        # Overwrite superclass default to use
        # specialized path_string mobject
        return TexSymbol(path_string)

    def organize_submobjects_left_to_right(self):
        self.sort(lambda p: p[0])
        return self


class MyCodeMobject(SingleStringTexMobject):
    CONFIG = {
        "template_tex_file_body": TEMPLATE_TEXT_FILE_BODY,
        "alignment": "\\centering",

        "arg_separator": " ",
        "substrings_to_isolate": [],
        "tex_to_color_map": {},
    }

    def __init__(self, *tex_strings, **kwargs):
        digest_config(self, kwargs)
        tex_strings = self.break_up_tex_strings(tex_strings)
        self.tex_strings = tex_strings
        SingleStringTexMobject.__init__(
            self, self.arg_separator.join(tex_strings), **kwargs
        )
        self.break_up_by_substrings()
        self.set_color_by_tex_to_color_map(self.tex_to_color_map)

        if self.organize_left_to_right:
            self.organize_submobjects_left_to_right()

    def break_up_tex_strings(self, tex_strings):
        substrings_to_isolate = op.add(
            self.substrings_to_isolate,
            list(self.tex_to_color_map.keys())
        )
        split_list = split_string_list_to_isolate_substrings(
            tex_strings, *substrings_to_isolate
        )
        split_list = [str(x).strip() for x in split_list]
        #split_list = list(map(str.strip, split_list))
        split_list = [s for s in split_list if s != '']
        return split_list

    def break_up_by_substrings(self):
        """
        Reorganize existing submojects one layer
        deeper based on the structure of tex_strings (as a list
        of tex_strings)
        """
        new_submobjects = []
        curr_index = 0
        for tex_string in self.tex_strings:
            sub_tex_mob = SingleStringTexMobject(tex_string, **self.CONFIG)
            num_submobs = len(sub_tex_mob.submobjects)
            new_index = curr_index + num_submobs
            if num_submobs == 0:
                # For cases like empty tex_strings, we want the corresponing
                # part of the whole TexMobject to be a VectorizedPoint
                # positioned in the right part of the TexMobject
                sub_tex_mob.submobjects = [VectorizedPoint()]
                last_submob_index = min(curr_index, len(self.submobjects) - 1)
                sub_tex_mob.move_to(self.submobjects[last_submob_index], RIGHT)
            else:
                sub_tex_mob.submobjects = self.submobjects[curr_index:new_index]
            new_submobjects.append(sub_tex_mob)
            curr_index = new_index
        self.submobjects = new_submobjects
        return self

    def get_parts_by_tex(self, tex, substring=True, case_sensitive=True):
        def test(tex1, tex2):
            if not case_sensitive:
                tex1 = tex1.lower()
                tex2 = tex2.lower()
            if substring:
                return tex1 in tex2
            else:
                return tex1 == tex2

        return VGroup(*[m for m in self.submobjects if test(tex, m.get_tex_string())])

    def get_part_by_tex(self, tex, **kwargs):
        all_parts = self.get_parts_by_tex(tex, **kwargs)
        return all_parts[0] if all_parts else None

    def set_color_by_tex(self, tex, color, **kwargs):
        parts_to_color = self.get_parts_by_tex(tex, **kwargs)
        for part in parts_to_color:
            part.set_color(color)
        return self

    def set_color_by_tex_to_color_map(self, texs_to_color_map, **kwargs):
        for texs, color in list(texs_to_color_map.items()):
            try:
                # If the given key behaves like tex_strings
                texs + ''
                self.set_color_by_tex(texs, color, **kwargs)
            except TypeError:
                # If the given key is a tuple
                for tex in texs:
                    self.set_color_by_tex(tex, color, **kwargs)
        return self

    def index_of_part(self, part):
        split_self = self.split()
        if part not in split_self:
            raise Exception("Trying to get index of part not in TexMobject")
        return split_self.index(part)

    def index_of_part_by_tex(self, tex, **kwargs):
        part = self.get_part_by_tex(tex, **kwargs)
        return self.index_of_part(part)

    def sort_alphabetically(self):
        self.submobjects.sort(
            key=lambda m: m.get_tex_string()
        )


class MyCodeMobjectTest(Scene):
    def construct(self):
        #[highlightlines={1,3-4}]
        s = """\\begin{minted}{python}
def dfs(y, x):
    if not reachable[y][x] or visited[y][x] 
        return
    visited[y][x] = True
    for i in range(4):
        dfs(y + dy[i], x + dx[i])
\\end{minted}
"""

        print(s)
        title = MyCodeMobject(s)
        self.play(Write(title))
        self.wait()


class SvgTest(Scene):
    def construct(self):
        svg = SVGMobject("Tex/0ee1f20510463e3e.svg")
        print(svg)
        self.add(svg)
        self.wait()


from cairosvg import svg2png
from manimlib.mobject.types.image_mobject import ImageMobject   

class ImageTest(Scene):
    def construct(self):
        file = 'LaTeXExperiment/code_0'
        svg_code = open(file + '.svg').read()
        svg2png(bytestring=svg_code,scale=10,write_to=file+'.png')
        img = ImageMobject(file+'.png',invert=True)
        self.add(img)
        self.wait()


from manimlib.mobject.svg.code_mobject import Code
from manimlib.mobject.geometry import Dot


class CodeTest(Scene):
    def construct(self):
        code_py = Code('LaTeXExperiment/code_0.py', language='python', insert_line_no=False, background='window').shift(UP)
        self.add(code_py)
        self.wait()
        code_cpp = Code('LaTeXExperiment/code_0.cc', language='cpp', insert_line_no=False, background='window').shift(DOWN)
        self.add(code_cpp)
        self.wait()

from manimlib.mobject.svg.code_mobject import insert_line_numbers
from manimlib.container.container import Container
from manimlib.mobject.svg.text_mobject import Paragraph

import re
import html

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

import json
"""
    CONFIG = {
        "tab_width": 3,
        "line_spacing": 0.1,
        "scale_factor": 0.5,
        "run_time": 1,
        "font": 'Monospac821 BT',
        'stroke_width': 0,
        'margin': 0.3,
        'indentation_char': "  ",
        "background": "rectangle",  # or window
        "corner_radius": 0.2,
        'insert_line_no': True,
        'line_no_from': 1,
        "line_no_buff": 0.4,
        'style': 'vim',
        'language': 'cpp',
        'generate_html_file': False
    }
"""
class MyCode(Code):
    CONFIG = {
        "font": 'Ubuntu Mono',
        'indentation_char': "  ",
        "background": None,
        'insert_line_no': False,
        'style': 'vim',
        'language': 'cpp',
        'generate_html_file': False,
        'lines_to_highlight': []
    }
    def hilite_me(self, code, lexer, options, style, linenos, divstyles):
        lexer = lexer or 'python'
        style = style or 'colorful'
        defstyles = 'overflow:auto;width:auto;'

        print("EO: ", self.lines_to_highlight)

        formatter = HtmlFormatter(style=style,
                                linenos=False,
                                noclasses=True,
                                cssclass='',
                                cssstyles=defstyles + divstyles,
                                prestyles='margin: 0',
                                hl_lines=self.lines_to_highlight)
        html = highlight(code, get_lexer_by_name(lexer, **options), formatter)
        if linenos:
            html = insert_line_numbers(html)
        html = "<!-- HTML generated using hilite.me -->" + html
        print(html)
        return html

    def gen_html_string(self):
        file = open(self.file_path, "r")
        code_str = file.read()
        file.close()
        self.html_string = self.hilite_me(code_str, self.language, {}, self.style, self.insert_line_no,
                                     "border:solid gray;border-width:.1em .1em .1em .8em;padding:.2em .6em;")
        if self.generate_html_file:
            os.makedirs(os.path.join("assets", "codes", "generated_html_files"), exist_ok=True)
            file = open(os.path.join("assets", "codes", "generated_html_files", self.file_name + ".html"), "w")
            file.write(self.html_string)
            file.close()

    def gen_code_json(self):
        if self.background_color == "#111111" or \
                self.background_color == "#272822" or \
                self.background_color == "#202020" or \
                self.background_color == "#000000":
            self.default_color = "#ffffff"
        else:
            self.default_color = "#000000"
        for i in range(3, -1, -1):
            self.html_string = self.html_string.replace("</" + " " * i, "</")
        for i in range(10, -1, -1):
            self.html_string = self.html_string.replace("</span>" + " " * i, " " * i + "</span>")
        #self.html_string = self.html_string.replace("background-color:", "background:")

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
                print("wi: ", line_index, word_index, words[word_index])
                color_index = words[word_index].find("color:")
                if color_index == -1:
                    color = self.default_color
                else:
                    starti = words[word_index][color_index:].find("#")
                    color = words[word_index][color_index + starti:color_index + starti + 7]

                bg_color_index = words[word_index].find("background-color:")
                if bg_color_index == -1:
                    bg_color = None # self.default_bg_color?
                else:
                    starti = words[word_index][bg_color_index:].find("#")
                    bg_color = words[word_index][bg_color_index + starti:bg_color_index + starti + 7]

                print("cols: ", color, bg_color)
                start_point = words[word_index].find(">")
                end_point = words[word_index].find("</span>")
                text = words[word_index][start_point + 1:end_point]
                text = html.unescape(text)
                if text != "":
                    print(text, "'" + color + "'")
                    self.code_json[code_json_line_index].append([text, color, bg_color])
        print(self.code_json)

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
            if (line_no in self.lines_to_highlight):
                line.set_fill(BLUE).set_opacity(1.)
            for word_index in range(self.code_json[line_no].__len__()):
                #print("A1", line, line_char_index, line[line_char_index:line_char_index + self.code_json[line_no][word_index][0].__len__()])
                #print("A2", self.code_json[line_no][word_index])
                line[line_char_index:line_char_index + self.code_json[line_no][word_index][0].__len__()].set_color(
                    self.code_json[line_no][word_index][1])

                line_char_index += self.code_json[line_no][word_index][0].__len__()
        return code


    def __init__(self, file_name=None, **kwargs):
        Container.__init__(self, **kwargs)
        self.file_name = file_name or self.file_name
        self.ensure_valid_file()
        self.style = self.style.lower()
        self.gen_html_string()
        self.background_color = None
        self.gen_code_json()

        self.code = self.gen_colored_lines()
        print(self.code)
        if self.insert_line_no:
            self.line_numbers = self.gen_line_numbers()
            self.line_numbers.next_to(self.code, direction=LEFT, buff=self.line_no_buff)

        if self.insert_line_no:
            VGroup.__init__(self, self.line_numbers, *self.code, **kwargs)
        else:
            VGroup.__init__(self, *self.code, **kwargs) # Delete Dot
        self.move_to(np.array([0, 0, 0]))

class MyCodeTest(Scene):
    def construct(self):
        arr = [1, 3, 4]
        code_py = MyCode('LaTeXExperiment/code_0.py', language='python', lines_to_highlight=arr).shift(UP)
        self.add(code_py)
        self.wait(3.)
        print(code_py.html_string)
        code_cpp = MyCode('LaTeXExperiment/code_0.cc', language='cpp', lines_to_highlight=arr).shift(0.5*DOWN)
        self.add(code_cpp)
        self.wait(3.)
