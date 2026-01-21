from mistletoe.block_token import Paragraph, Heading, List, ListItem, BlockToken, CodeFence, Quote, Table, TableRow, TableCell
from mistletoe.span_token import RawText, Emphasis, Strong, SpanToken, EscapeSequence
from args import LINEWIDTH
from component import collapse
import re
from string import Template


class SentenceDelimiter(SpanToken):

    def __init__(self):
        self.content = ''

def extractedMathEnvironments(mathBlock, environment) -> dict:
    '''
    this function extracts multiline math environments (e.g. matrix, bmatrix) so that the MathBlock.__init__() can safely split math blocks by newlines 
    it does not support nested multiline environments e.g. matrix inside a matrix
    '''
    pattern = Template(r'\\begin{$env}.*?\\end{$env}')
    multilinePattern = re.compile(pattern.substitute(env=environment))
    multilineBlocks = multilinePattern.findall(mathBlock)
    replacedMathBlock = re.sub(multilinePattern, f'$${environment}$$', mathBlock)
    return {'extractedBlocks':multilineBlocks, 'replacedMathBlock':replacedMathBlock}


def delimitedTextToken(textToken:RawText) -> list:
    '''
    this function takes a RawText span token and splits it into multiple RawText tokens with SentenceDelimiters in between
    the delimiter is the string '. '
    this function will not split inline math pharases
    '''
    pattern = re.compile(r'\$.*?\$')
    inlineMathParts = re.findall(pattern, textToken.content)
    rawTextContent = pattern.sub('$inlineMath$', textToken.content)
    cumulativeTokenList = []
    tokens = rawTextContent.split('. ')
    for token in tokens[:-1]:
        cumulativeTokenList += [RawText(f'{token}.'), SentenceDelimiter()]
    if tokens[-1] != '':
        cumulativeTokenList.append(RawText(tokens[-1]))
    i = 0
    while i < len(inlineMathParts):
        for token in cumulativeTokenList:
            for j in range(token.content.count('$inlineMath$')):
                token.content = token.content.replace('$inlineMath$', inlineMathParts[i] ,1)
                i += 1
    return cumulativeTokenList

def rawTex(mathParagraph):
    rawLines = [line for line in mathParagraph.children]
    cumulativeString = ''
    for span in mathParagraph.children:
        if isinstance(span, EscapeSequence):
            cumulativeString += f'\\{span.children[0].content}'
        else:
            cumulativeString += f'{collapse([span])}'

    return cumulativeString[2:-2]
