from html.parser import HTMLParser
import sys


class SimpleHTMLChecker(HTMLParser):
    VOID_ELEMENTS = set([
        'area','base','br','col','embed','hr','img','input','link','meta',
        'param','source','track','wbr'
    ])

    def __init__(self):
        super().__init__()
        self.stack = []  # (tag, lineno, pos)
        self.issues = []

    def handle_starttag(self, tag, attrs):
        tag_l = tag.lower()
        lineno, offset = self.getpos()
        if tag_l in self.VOID_ELEMENTS:
            return
        self.stack.append((tag_l, lineno, offset))

    def handle_startendtag(self, tag, attrs):
        # self-closing tag
        return

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        lineno, offset = self.getpos()
        if not self.stack:
            self.issues.append(f"Unexpected closing tag </{tag_l}> at line {lineno}")
            return
        # Pop until matching start tag found
        temp = []
        while self.stack:
            top_tag, top_line, top_off = self.stack.pop()
            if top_tag == tag_l:
                # matched
                # push back any tags we popped that weren't matched
                for t in reversed(temp):
                    self.stack.append(t)
                return
            else:
                temp.append((top_tag, top_line, top_off))
                self.issues.append(
                    f"Mismatched or unclosed tag <{top_tag}> opened at line {top_line}, closed implicitly before </{tag_l}> at line {lineno}"
                )
        # if we reach here, no matching start tag
        self.issues.append(f"No matching start tag for </{tag_l}> at line {lineno}")

    def close(self):
        super().close()
        # any remaining open tags are unclosed
        for tag, line, off in self.stack:
            self.issues.append(f"Unclosed tag <{tag}> opened at line {line}")


def main():
    if len(sys.argv) < 2:
        print('Usage: check_html.py path/to/file.html')
        sys.exit(2)
    path = sys.argv[1]
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read()
    except Exception as e:
        print(f'Error reading {path}: {e}')
        sys.exit(2)

    parser = SimpleHTMLChecker()
    try:
        parser.feed(data)
        parser.close()
    except Exception as e:
        print(f'Parsing error: {e}')
        sys.exit(2)

    if parser.issues:
        print(f'Found {len(parser.issues)} HTML issue(s) in {path}:')
        for it in parser.issues:
            print('- ' + it)
        sys.exit(1)
    else:
        print(f'No unclosed/mismatched tags found in {path}.')
        sys.exit(0)


if __name__ == '__main__':
    main()
