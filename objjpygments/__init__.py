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
    filenames = ['*.j']
    mimetypes = ['text/x-objective-j']

    #: optional Comment or Whitespace
    _ws = r'(?:\s|//.*?\n|/[*].*?[*]/)*'

    flags = re.DOTALL | re.MULTILINE

    tokens = {
        'root': [                       
            include('whitespace'),

            # function definition
            (r'^(\s*[\+-]\s*)(.*?)(?=[^\(]{)', # ugly lookahead hack to handle types w/ curly braces
             bygroups(Text, using(this, state='function_signature'))),


            # class definition
            (r'(@interface|@implementation)(\s+)', bygroups(Keyword, Text),
             'classname'),
            (r'(@class|@protocol)(\s*)', bygroups(Keyword, Text),
             'forward_classname'),
            (r'(\s*)(@end)(\s*)', bygroups(Text, Keyword, Text)),

            include('statements'),
            ('[{\(\)}]', Punctuation),
            (';', Punctuation)
        ],
        'whitespace': [
            (r'(@import)(\s+)("(\\\\|\\"|[^"])*")', bygroups(Comment.Preproc, Text, String.Double)),
            (r'(@import)(\s+)(<(\\\\|\\>|[^>])*>)', bygroups(Comment.Preproc, Text, String.Double)),
            (r'(#(?:include|import))(\s+)("(\\\\|\\"|[^"])*")', bygroups(Comment.Preproc, Text, String.Double)),
            (r'(#(?:include|import))(\s+)(<(\\\\|\\>|[^>])*>)', bygroups(Comment.Preproc, Text, String.Double)),
            
            (r'#if\s+0', Comment.Preproc, 'if0'),
            (r'#', Comment.Preproc, 'macro'),

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

            (r'([$a-zA-Z_][a-zA-Z0-9_]*)(' + _ws + r')(?=\()', bygroups(Name.Function, using(this))),

            (r'[$a-zA-Z_][a-zA-Z0-9_]*', Name),
        ],
        'classname' : [
            # interface definition that inherits
            (r'([a-zA-Z_][a-zA-Z0-9_]*)(' + _ws + r':' + _ws + r')([a-zA-Z_][a-zA-Z0-9_]*)?',
             bygroups(Name.Class, using(this), Name.Class), '#pop'),
            # interface definition for a category
            (r'([a-zA-Z_][a-zA-Z0-9_]*)(' + _ws + r'\()([a-zA-Z_][a-zA-Z0-9_]*)(\))',
             bygroups(Name.Class, using(this), Name.Label, Text), '#pop'),
            # simple interface / implementation
            (r'([a-zA-Z_][a-zA-Z0-9_]*)', Name.Class, '#pop')
        ],
        'forward_classname' : [
            (r'([a-zA-Z_][a-zA-Z0-9_]*)(\s*,\s*)',
             bygroups(Name.Class, Text), '#push'),
            (r'([a-zA-Z_][a-zA-Z0-9_]*)(\s*;?)',
             bygroups(Name.Class, Text), '#pop')
        ],
        'function_signature': [
            include('whitespace'),

            # start of a selector w/ parameters
            (r'(\(' + _ws + r')'                # open paren
             r'([a-zA-Z_][a-zA-Z0-9_]+)'        # return type
             r'(' + _ws + r'\)' + _ws + r')'    # close paren
             r'([$a-zA-Z_][a-zA-Z0-9_]+' + _ws + r':)', # function name
             bygroups(using(this), Keyword.Type, using(this),
                 Name.Function), 'function_parameters'),

            # no-param function
            (r'(\(' + _ws + r')'                # open paren
             r'([a-zA-Z_][a-zA-Z0-9_]+)'        # return type
             r'(' + _ws + r'\)' + _ws + r')'    # close paren
             r'([$a-zA-Z_][a-zA-Z0-9_]+)',      # function name
             bygroups(using(this), Keyword.Type, using(this),
                 Name.Function), "#pop"),
 
            # no return type given, start of a selector w/ parameters
            (r'([$a-zA-Z_][a-zA-Z0-9_]+' + _ws + r':)', # function name
             bygroups (Name.Function), 'function_parameters'),

            # no return type given, no-param function
            (r'([$a-zA-Z_][a-zA-Z0-9_]+)',      # function name
             bygroups(Name.Function), "#pop"),


            ('', Text, '#pop'),
        ],
        'function_parameters': [
            include('whitespace'),

            # parameters
            (r'(\(' + _ws + ')'                 # open paren
             r'([^\)]+)'                        # type
             r'(' + _ws + r'\)' + _ws + r')+'   # close paren
             r'([$a-zA-Z_][a-zA-Z0-9_]+)',      # param name
             bygroups(using(this), Keyword.Type, using(this), Text)),

            # one piece of a selector name
            (r'([$a-zA-Z_][a-zA-Z0-9_]+' + _ws + r':)',     # function name
             Name.Function),

            # smallest possible selector piece
            (r'(:)', Name.Function),

            # var args
            (r'(,' + _ws + r'...)', using(this)),

            (r'([$a-zA-Z_][a-zA-Z0-9_]+)', Text)# param name
        ],
        'expression' : [
            (r'([$a-zA-Z_][a-zA-Z0-9_]*)(\()', bygroups(Name.Function, Punctuation)),
            (r'(\))', Punctuation, "#pop")
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
        if re.match('^\s*@import\s+[<"]', text, re.MULTILINE): # special directive found in most Objective-J files
            return True
        return False

       
