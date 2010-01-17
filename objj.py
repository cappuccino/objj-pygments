import re
try:
    set
except NameError:
    from sets import Set as set

from pygments.scanner import Scanner
from pygments.lexer import Lexer, RegexLexer, include, bygroups, using, \
                           this, combined
from pygments.util import get_bool_opt, get_list_opt
from pygments.token import \
     Text, Comment, Operator, Keyword, Name, String, Number, Punctuation, \
     Error


class ObjectiveJLexer(RegexLexer):
    """
    For Objective-J source code with preprocessor directives.
    """

    name = 'Objective-J'
    aliases = ['objective-j', 'objectivej', 'obj-j', 'objj']
    filenames = ['*.m']
    mimetypes = ['text/x-objective-j']

    #: optional Comment or Whitespace
    _ws = r'(?:\s|//.*?\n|/[*].*?[*]/)*'

    def expand_func(self, match, *args):
        state = 0
        index_counter = 0
        tokens = list()
        tokentypes = [Name.Function, Text, Keyword.Type, Text, Name, Text]
        
        parts = re.split(r'(\)?' + ObjectiveJLexer._ws + r'\(?)', match.group(0))
        
        for part in parts:
            tokens.append((index_counter, tokentypes[state], part))
            index_counter += len(part)
            state = (state + 1) % len(tokentypes)
            
        return tokens

    tokens = {
        'root': [
            include('whitespace'),
            
            # function definition
            (r'([+-]' + _ws + r'\(' + _ws + r')' 
             r'([$a-zA-Z_][a-zA-Z0-0_]+)'       # return type
             r'(' + _ws + r'\)' + _ws + r')'
             r'([^;]+?)'                        # name + params
             r'(' + _ws + r')({)',
             bygroups(Text, Keyword.Type, Text, expand_func,
                      Text, Punctuation)),

            (r'(@interface|@implementation)(\s+)', bygroups(Keyword, Text),
             'classname'),
            (r'(@class|@protocol)(\s' + _ws + r')', bygroups(Keyword, Text),
             'forward_classname'),
            (r'(' + _ws + r')(@end)(' + _ws + r')', bygroups(Text, Keyword, Text)),

            include('statements'),
            ('[{}]', Punctuation),
            (';', Punctuation)
        ],
        'whitespace': [
            (r'^(\s*)(#if\s+0)', bygroups(Text, Comment.Preproc), 'if0'),
            (r'^(\s*)(#)', bygroups(Text, Comment.Preproc), 'macro'),
            (r'\n', Text),
            (r'\s+', Text),
            (r'\\\n', Text), # line continuation
            (r'//(\n|(.|\n)*?[^\\]\n)', Comment.Single),
            (r'/(\\\n)?[*](.|\n)*?[*](\\\n)?/', Comment.Multiline),
            (r'<!--', Comment),
        ],
        'slashstartsregex': [
            include('whitespace'),
            (r'/(\\.|[^[/\\\n]|\[(\\.|[^\]\\\n])*])+/'
             r'([gim]+\b|\B)', String.Regex, '#pop'),
            (r'(?=/)', Text, ('#pop', 'badregex')),
            (r'', Text, '#pop')
        ],
        'badregex': [
            ('\n', Text, '#pop')
        ],
        'statements': [
            (r'(L|@)?"', String, 'string'),
            (r"(L|@)?'(\\.|\\[0-7]{1,3}|\\x[a-fA-F0-9]{1,2}|[^\\\'\n])'", String.Char),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r'(\d+\.\d*|\.\d+|\d+)[eE][+-]?\d+[lL]?', Number.Float),
            (r'(\d+\.\d*|\.\d+|\d+[fF])[fF]?', Number.Float),
            (r'0x[0-9a-fA-F]+[Ll]?', Number.Hex),
            (r'0[0-7]+[Ll]?', Number.Oct),
            (r'\d+[Ll]?', Number.Integer),

            (r'^(?=\s|/|<!--)', Text, 'slashstartsregex'),
            (r'\+\+|--|~|&&|\?|:|\|\||\\(?=\n)|'
             r'(<<|>>>?|==?|!=?|[-<>+*%&\|\^/])=?', Operator, 'slashstartsregex'),
            (r'[{(\[;,]', Punctuation, 'slashstartsregex'),
            (r'[})\].]', Punctuation),

            (r'(@import)(\s+)([^\s]+)', bygroups(Keyword, Text, Keyword)),

            (r'(for|in|while|do|break|return|continue|switch|case|default|if|else|'
             r'throw|try|catch|finally|new|delete|typeof|instanceof|void'
             r'|prototype|__proto__)\b', Keyword, 'slashstartsregex'),

            (r'(var|with|function)\b', Keyword.Declaration, 'slashstartsregex'),
          
            (r'(@selector|@private|@protected|@public|@encode|'
             r'@synchronized|@try|@throw|@catch|@finally|@end|@property|'
             r'@synthesize|@dynamic|@for|@accessors|new)\b', Keyword),

            (r'(int|long|float|short|double|char|unsigned|signed|void|'
             r'id|BOOL|bool|boolean|IBOutlet|IBAction|SEL|@outlet|@action)\b', Keyword.Type),

            (r'(self|super)\b', Name.Builtin),

            (r'(TRUE|YES|FALSE|NO|Nil|nil|NULL)\b', Keyword.Constant),
            (r'(true|false|null|NaN|Infinity|undefined)\b', Keyword.Constant),
            (r'(ABS|ASIN|ACOS|ATAN|ATAN2|SIN|COS|TAN|EXP|POW|CEIL|FLOOR|ROUND|MIN|MAX'
             r'RAND|SQRT|E|LN2|LN10|LOG2E|LOG10E|PI|PI2|PI_2|SQRT1_2|SQRT2)\b', Keyword.Constant),

            (r'(Array|Boolean|Date|Error|Function|Math|netscape|'
             r'Number|Object|Packages|RegExp|String|sun|decodeURI|'
             r'decodeURIComponent|encodeURI|encodeURIComponent|'
             r'Error|eval|isFinite|isNaN|parseFloat|parseInt|document|this|'
             r'window)\b', Name.Builtin),

            (r'[$a-zA-Z_][a-zA-Z0-9_]*', Name),
        ],
        'classname' : [
            # interface definition that inherits
            ('([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)([a-zA-Z_][a-zA-Z0-9_]*)?',
             bygroups(Name.Class, Text, Name.Class), '#pop'),
            # interface definition for a category
            ('([a-zA-Z_][a-zA-Z0-9_]*)(\s*)(\([a-zA-Z_][a-zA-Z0-9_]*\))',
             bygroups(Name.Class, Text, Name.Label), '#pop'),
            # simple interface / implementation
            ('([a-zA-Z_][a-zA-Z0-9_]*)', Name.Class, '#pop')
        ],
        'forward_classname' : [
          ('([a-zA-Z_][a-zA-Z0-9_]*)(\s*,\s*)',
           bygroups(Name.Class, Text), 'forward_classname'),
          ('([a-zA-Z_][a-zA-Z0-9_]*)(\s*;?)',
           bygroups(Name.Class, Text), '#pop')
        ],
        'function': [
            include('whitespace'),
            include('statements'),
            (';', Punctuation),
            ('{', Punctuation, '#push'),
            ('}', Punctuation, '#pop'),
        ],
        'string': [
            (r'"', String, '#pop'),
            (r'\\([\\abfnrtv"\']|x[a-fA-F0-9]{2,4}|[0-7]{1,3})', String.Escape),
            (r'[^\\"\n]+', String), # all other characters
            (r'\\\n', String), # line continuation
            (r'\\', String), # stray backslash
        ],
        'macro': [
            (r'[^/\n]+', Comment.Preproc),
            (r'/[*](.|\n)*?[*]/', Comment.Multiline),
            (r'//.*?\n', Comment.Single, '#pop'),
            (r'/', Comment.Preproc),
            (r'(?<=\\)\n', Comment.Preproc),
            (r'\n', Comment.Preproc, '#pop'),
        ],
        'if0': [
            (r'^\s*#if.*?(?<!\\)\n', Comment.Preproc, '#push'),
            (r'^\s*#endif.*?(?<!\\)\n', Comment.Preproc, '#pop'),
            (r'.*?\n', Comment),
        ]
    }

    def analyse_text(text):
        if '@import' in text: # strings
            return True
        if re.match(r'CP[A-Z][a-zA-Z]+', text): # message
            return True
        return False

if __name__ == '__main__':
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import ObjectiveCLexer
    import sys

    code = open(sys.argv[1]).read()
    highlight(code, ObjectiveJLexer(), HtmlFormatter(noclasses=True), open(sys.argv[1] + '.html','w'))
       
