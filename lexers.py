import pygments.lexer
import pygments.lexers
import pygments.token
import pygments.util
import pygount

class XamlLexer(pygments.lexers.XmlLexer):
    name = "XAML"
    filenames = ["*.xaml"]

def load():
    pygount.analysis._SUFFIX_TO_FALLBACK_LEXER_MAP['xaml'] = XamlLexer()
