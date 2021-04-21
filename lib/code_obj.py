import numpy as np
import hashlib
from html.parser import HTMLParser
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

import manimlib.constants as consts
from manimlib.mobject.geometry import Rectangle
from manimlib.mobject.shape_matchers import SurroundingRectangle
from manimlib.mobject.svg.text_mobject import Paragraph, Text, TextSetting
from manimlib.mobject.types.vectorized_mobject import VGroup
from manimlib.utils.config_ops import digest_config

# NOTE: Some changes made to Text to adapt this
# Should adapt Test to this class
class VariableStyleLine(Text):
    CONFIG = {
        "font": 'Ubuntu Mono',
        "slant": consts.NORMAL,
        "weight": consts.NORMAL,
    }
    def __init__(self, line_settings, **kwargs):
        assert(len(self.get_text(line_settings)) == len(line_settings)), "Sizes don't match"
        digest_config(self, kwargs)
        self.line_settings = line_settings
        Text.__init__(self, self.get_text(line_settings), **kwargs)
        self.set_color_by_index()
    
    def get_text(self, line_settings):
        return "".join(index_settings["text"] for index_settings in line_settings)

    def set_color_by_index(self):
        for index, index_settings in enumerate(self.line_settings):
            if "color" in index_settings:
                self[index].set_color(index_settings["color"])

    # override
    def get_extra_settings(self):
        return [TextSetting(index, index + 1, *[
            index_settings["font"] if "font" in index_settings else self.font,
            index_settings["slant"] if "slant" in index_settings else self.slant,
            index_settings["weight"] if "weight" in index_settings else self.weight])
                for index, index_settings in enumerate(self.line_settings)]

    # override
    def text2hash(self):
        settings = self.font + self.slant + self.weight
        settings += str(self.t2f) + str(self.t2s) + str(self.t2w)
        settings += str(self.lsh) + str(self.size)
        settings += str(self.line_settings)
        id_str = self.text+settings
        hasher = hashlib.sha256()
        hasher.update(id_str.encode())
        return hasher.hexdigest()[:16]

# Should specialize TextWithFixedHeigth
class VariableStyleLineWithFixedHeight(VariableStyleLine):
    def __init__(self, line_settings, **kwargs):
        VariableStyleLine.__init__(self, line_settings, **kwargs)
        max_height = Text("(gyt{[/QW", **kwargs).get_height()
        rectangle = Rectangle(width=0, height=max_height, fill_opacity=0,
                              stroke_opacity=0,
                              stroke_width=0)
        self.submobjects.append(rectangle)

# Should specialize Paragraph
class VariableStyleParagraph(VGroup):
    CONFIG = {
        "line_spacing": 0.1,
        "alignment": "left",
    }

    def __init__(self, text_settings, **kwargs):
        digest_config(self, kwargs)
        self.lines = [VariableStyleLineWithFixedHeight(line_settings, **kwargs) for line_settings in text_settings]
        self.char_height = self.lines[0].get_height()
        self.align_lines()
        VGroup.__init__(self, *self.lines, **kwargs)
        self.move_to(np.array([0, 0, 0]))

    # Copied and adapted from paragraph (the other functions there made no sense)
    def align_lines(self):
        for line_no in range(self.lines.__len__()):
            factor_dict = {'left': 1, 'center': 0, 'right': '1'}
            if self.alignment not in factor_dict:
                raise Exception("Invalid alignment: {}".format(self.alignment))
            self.lines[line_no].move_to(np.array(
                [factor_dict[self.alignment]*(self.lines[line_no].get_width() / 2), - line_no * (self.char_height + self.line_spacing), 0]))

# Renaming
class CodeText(VariableStyleParagraph):
    pass

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
        'highlight_settings': {},
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

        if file_name is not None:
            extension = file_name.split('.')[-1]
            if extension in ['cc', 'cpp']:
                self.language = 'cpp'
            if extension == 'py':
                self.language = 'python'
        
        self.file_name = file_name
        self.code_str = (code_str if code_str else open(file_name, "r").read()).replace('\t', ' '*self.tab_width)
        
        self.code = self.get_codetext()
        self.highlight_lines(self.highlight_settings)

        objs = [self.code, *self.background]
        if self.show_line_numbers:
            objs = [self.gen_line_numbers().next_to(self.code, direction=consts.LEFT, buff=self.line_no_buff)] + objs
        VGroup.__init__(self, *objs, **kwargs)

    def gen_line_numbers(self):
        return Paragraph(*[str(self.line_no_from + line_no) for line_no in range(self.text_settings.__len__())], alignment="right", font=self.font)

    def get_codetext(self):
        self.text_settings = self.gen_text_settings()
        return CodeText(self.text_settings, alignment="left", font=self.font)

    def get_highlited_lines(self, highlight_settings):
        return [
            SurroundingRectangle(
                self.code[line_no],
                buff=self.highlight_buff,
                color=(highlight_settings[line_no + 1] if line_no + 1 in highlight_settings else self.highlight_color),
                fill_color=(highlight_settings[line_no + 1] if line_no + 1 in highlight_settings else self.highlight_color),
                fill_opacity=(self.highlight_opacity if line_no + 1 in highlight_settings else 0.),
                stroke_width=0
            ) for line_no in range(self.code.__len__())]

    def highlight_lines(self, highlight_settings):
        self.highlight_settings = highlight_settings
        self.background = self.get_highlited_lines(highlight_settings)
        return self.background
 
    def gen_text_settings(self):
        class CodeHTMLParser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.text_settings = [[]]
                self.default_format = {"color" : "#FFFFFF", "weight" : "NORMAL", "slant" : "NORMAL"}
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
                        assert(data_key in ["color", "weight", "slant"]), "Unexpected DataKey {}".format(data_key)
                        self.cur_format[data_key] = data_val.upper()

            def handle_data(self, data):
                lines = data.splitlines()
                for i in range(len(lines)):
                    if i > 0:
                        self.text_settings.append([])
                    new_info = self.cur_format.copy()
                    for c in lines[i]:
                        new_info["text"] = c
                        self.text_settings[-1].append(new_info.copy())

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

        self.html_string = self.html_string.replace("font-weight", "weight")
        self.html_string = self.html_string.replace("font-style", "slant")

        html_parser = CodeHTMLParser()
        html_parser.feed(self.html_string)
        html_parser.close()
        self.text_settings = html_parser.text_settings
        return self.text_settings

"""
Code Styles:
dict_keys(['default', 'emacs', 'friendly', 'colorful', 'autumn', 'murphy', 'manni', 'monokai', 'perldoc',
'pastie', 'borland', 'trac', 'native', 'fruity', 'bw', 'vim', 'vs', 'tango', 'rrt', 'xcode', 'igor',
'paraiso-light', 'paraiso-dark', 'lovelace', 'algol', 'algol_nu', 'arduino', 'rainbow_dash', 'abap',
'solarized-dark', 'solarized-light', 'sas', 'stata', 'stata-light', 'stata-dark', 'inkpot'])
"""