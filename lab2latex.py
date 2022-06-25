import argparse
import html.parser
import http.client
import re
import urllib.parse

document = []
valid_title_pattern = re.compile('(Bonus )?Problem (\d )*\(\d+ pts\)', re.IGNORECASE)
header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def add_documentclass(type="article"):
    document.append('\\documentclass{%s}\n' % type)

def add_section_with_title(title):
    document.append('\\begin{section}\n')
    document.append('{%s}' % latex_escaped(title))
    
def add_numbered_list(items):
    document.append('\\begin{enumerate}')
    for item in items:
        document.append('\n\\item ' + latex_escaped(item))
    document.append('\n\\end{enumerate}\n')
    
def add_section_ending():
    document.append('\\end{section}\n')

def add_newpage():
    document.append('\\newpage\n')
    
def add_to_document(data):
    document.append(latex_escaped(data))

def add_generic_title_format():
    document.append('\\titleformat{\\section}{\\normalfont\\Large' 
                    + '\\bfseries}{}{0pt}{}\n')

def add_generic_usepackage():
    document.append('\\usepackage{titlesec,amsmath,amsthm,amsfonts}\n')

def add_title(title):
    document.append('\\title{%s}\n' % latex_escaped(title))

def add_date(date='\\today'):
    document.append('\\date{%s}\n' % date)

def add_begin_document():
    document.append('\\begin{document}\n')

def add_end_document():
    document.append('\\end{document}')

def add_titlepage():
    document.append('\\begin{titlepage}\n')
    document.append('\\maketitle \n')
    document.append('\\tableofcontents \n')
    document.append('\\end{titlepage}\n')

def add_author(author):
    document.append('\\author{%s}\n' % latex_escaped(author))


class LabHTMLParser(html.parser.HTMLParser):
    inside_header = False
    inside_p_tag = False
    valid_problem = False
    current_str = ""

    def handle_starttag(self, tag, attrs):
        if tag in header_tags:
            self.inside_header = True
        elif tag == 'p':
            self.inside_p_tag = True
        
    def handle_endtag(self, tag):
        if tag in header_tags:
            self.inside_header = False
        elif tag == 'p':
            self.clean_and_add_to_doc(self.current_str)
            self.current_str = ""
            self.inside_p_tag = False
            if self.valid_problem:
                add_section_ending()
                add_newpage()
            self.valid_problem = False

    def clean_and_add_to_doc(self, data):
        def split_after_question_mark(s):
            if s == '':
                return []
            index = s.find('?')
            if index == -1:
                return [s]
            else:
                return [s[:index+1]] + split_after_question_mark(s[index+1:])

        if self.valid_problem:
            newline_pattern = re.compile('\n')
            x = data
            x = newline_pattern.sub(' ', x)
            x = split_after_question_mark(x)
            x = list(map(lambda s: s.strip(), x))
            x = list(filter(lambda s: s != '', x))
            if len(x) > 1:
                add_numbered_list(x)
            else:
                add_to_document(x[0])

    def handle_data(self, data):
        if self.inside_header:
            valid_title = valid_title_pattern.search(data)
            if valid_title:
                self.valid_problem = True
                add_section_with_title(data)
        elif self.inside_p_tag:
            self.current_str += data
    

def latex_escaped(string):
    symbols_to_escape="&$%_^~#}{"
        
    def special_symbols_replaced(intermediate):
        result = ""
        
        for sym in intermediate:
            if sym in symbols_to_escape:
                result += '\\' + sym
            elif sym == '|':
                result += '\\textbar '
            elif sym == '\\':
                result += '\\textbackslash '
            elif sym == '<':
                result += '\\textless '
            elif sym == '>':
                result += '\\textmore '
            else:
                result += sym
        
        return result
    
    return re.sub(r'\/\\s', '\\\\slash{}', special_symbols_replaced(string))

def fetch_and_return_html(host, path):
    client = http.client.HTTPSConnection(host, port=443)
    client.request('GET',path)
    response = client.getresponse()
    the_html = response.read().decode()
    return the_html

def main():
    arg_parser = argparse.ArgumentParser(description='A script to convert a' \
                                                   + ' lab HTML document ' \
                                                   + 'into LaTeX')
    arg_parser.add_argument('-a', '--author', type=str,
                            help='The author of this lab report (you)',
                            required=True)
    arg_parser.add_argument('-t', '--title', type=str,
                            help='The title of this document', required=True)
    arg_parser.add_argument('-f', '--filename', type=str,
                            help='The file to output to', default='paper.tex')
    arg_parser.add_argument('--url', type=str,
                            help='The URL of the lab handout', required=True)
    args = arg_parser.parse_args()

    author   = args.author
    title    = args.title
    filename = args.filename
    url      = args.url

    parse_result = urllib.parse.urlparse(url)
    host = parse_result.netloc
    path = parse_result.path

    the_html = fetch_and_return_html(host, path)

    add_documentclass()
    add_generic_usepackage()
    add_generic_title_format()
    add_title(title)
    add_author(author)
    add_date()
    add_begin_document()
    add_titlepage()

    html_parser = LabHTMLParser()
    html_parser.feed(the_html)

    add_end_document()

    test_filename = 'test.tex'
    with open(filename, 'w') as f:
        for line in document:
            f.write(line)

if __name__ == '__main__':
    main()
