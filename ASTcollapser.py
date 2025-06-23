import json
from string import Template
from abc import ABC, abstractmethod
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer, LinkReferenceDefinition, BlankLine
from mistletoe.block_token import Paragraph, Heading, List, ListItem, BlockToken, CodeFence, Quote
from mistletoe.span_token import LineBreak, RawText, Strong, Emphasis, Image, EscapeSequence, SpanToken
from mistletoe.token import Token
import math
import re

LINES = 6
LINEWIDTH = 50
class Component(ABC):
    '''
    CompositeBlocks are made up of Components
    '''
    @abstractmethod
    def height(self, lineWidth=LINEWIDTH):
        pass

class Sentence(Component):
    '''
    base class that can be decorated by StrongSentence and EmphasizedSentence
    '''
    def __init__(self,sentence:str):
        self.__sentence = sentence
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> list:
        return [] 
    def size(self) -> int:
        return len(self.__sentence)
    def height(self, lineWidth=LINEWIDTH):
        return math.ceil(self.size() / lineWidth)

class Head:
    def __init__(self, mdHeading:Heading):
        self.__level = mdHeading.level
        self.__content = collapse(mdHeading.children)
    def height(self, lineWidth=LINEWIDTH):
        return 0 
    def headText(self) -> str:
        return str(self.__content)

class Block(ABC):
    @abstractmethod
    def height(self) -> int:
        pass
    def items(self, level=0, indentSize=0, leader=''):
        return [IndentedListItem(self, level=level, indentSize=indentSize, leader=leader)]
    @abstractmethod
    def slideContent(self, head:Head):
        pass
    def mdSlides(self, head:Head, lines=LINES):
        return f'{self.slideContent(head)}\n---\n\n' 

class CompositeBlock(Block):
    '''
    composite blocks can be split into multiple slides, split is based on number of lines
    '''
    def slides(self, head:Head, lines=LINES) -> list:
        slides = []
        currentHeight = 0
        currentSlide = []
        for component in self.components():
            if currentHeight + component.height() > lines:
                slides.append(self.slideContent(currentSlide, head))
                currentSlide = [component]
                currentHeight = component.height()
            else:
                currentSlide.append(component)
                currentHeight += component.height()
        slides.append(self.slideContent(currentSlide, head))
        return slides
    def mdSlides(self, head:Head, lines=LINES) -> str:
        subDeck = ''
        for slide in self.slides(head, lines):
            subDeck += f'{slide}\n'
            subDeck += '\n---\n\n'
        return subDeck
    @abstractmethod
    def components(self) -> list:
        pass
    def height(self, lineWidth=LINEWIDTH):
        cumulativeHeight = 0
        for component in self.components():
            cumulativeHeight += component.height()
        return cumulativeHeight

class StrongSentence(Sentence):
    def __init__(self,sentence:Sentence, strongParts:list):
        self.__sentence = sentence
        self.__strongParts = strongParts
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> list:
        innerImportantParts = []
        for part in self.__strongParts:
            innerImportantParts += part.importantParts()
        return self.__sentence.importantParts() + self.__strongParts + innerImportantParts
    def size(self) -> int:
        return self.__sentence.size()

class EmphasizedSentence(Sentence):
    def __init__(self,sentence:Sentence,emphasizedParts:list):
        self.__sentence = sentence
        self.__emphasizedParts = emphasizedParts
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> list:
        innerImportantParts = []
        for part in self.__emphasizedParts:
            innerImportantParts += part.importantParts()
        return self.__sentence.importantParts() + self.__emphasizedParts + innerImportantParts
    def size(self) -> int:
        return self.__sentence.size()


class UnsupportedTokenException(Exception):
    def __init__(self, token:BlockToken):
        self.unsupportedToken = token

def isMathBlock(paragraph:Paragraph, mathFence = '$$') -> bool:
    '''
    mathblocks are not native to commonmark or mistletoe, this function checks if a paragraph is surrounded by the math fence token
    '''
    startsWithDollars = isinstance(paragraph.children[0], RawText) and paragraph.children[0].content.startswith(mathFence)
    endsWithDollars = isinstance(paragraph.children[-1], RawText) and paragraph.children[-1].content.endswith(mathFence)
    return startsWithDollars and endsWithDollars

def isInvisible(token:Token):
    if isinstance(token, BlankLine):
        return True
    if isinstance(token, LinkReferenceDefinition):
        return True
    else:
        return False

def asBlock(token:BlockToken) -> Block:
    '''
    convert mistletoe.block_token.BlockToken into Blocks
    '''
    if isinstance(token, Paragraph) and isMathBlock(token):
        return MathBlock(token)
    elif isinstance(token, Paragraph) and isImageBlock(token):
        return ImageBlock(token)
    elif isinstance(token, Paragraph):
        return ParagraphBlock(token)
    elif isinstance(token, Heading):
        return Head(token)
    elif isinstance(token, List):
        return ListBlock(token)
    elif isinstance(token, ListItem):
        return Item(token)
    elif isinstance(token, CodeFence):
        return CodeBlock(token)
    elif isinstance(token, Quote):
        return QuoteBlock(token)
    else:
        raise UnsupportedTokenException(token)

class SentenceDelimiter(SpanToken):
    def __init__(self):
        pass

def delimitedTextToken(textToken:RawText):
    cumulativeTokenList = []
    tokens = textToken.content.split('. ')
    for token in tokens[:-1]:
        cumulativeTokenList += [RawText(f'{token}.'), SentenceDelimiter()]
    if tokens[-1] != '':
        cumulativeTokenList.append(RawText(tokens[-1]))
    return cumulativeTokenList

class ParagraphBlock(CompositeBlock):
    def __init__(self, mdParagraph:Paragraph):
        self.__mdParagraph = mdParagraph
        self.__sentences = [collapse(spanList) for spanList in self.decompose()]
    def decompose(self) -> list:
        '''
        Decompose a paragraph into list of span tokens based on SoftBreaks (single line breaks)
        '''
        spanTokenList = []
        for child in self.__mdParagraph.children:
            if isinstance(child, RawText):
                spanTokenList += delimitedTextToken(child)
            else:
                spanTokenList.append(child)
        sentenceComposites = []
        rawSentences = []
        for spanToken in spanTokenList:
            if isinstance(spanToken, LineBreak) or isinstance(spanToken, SentenceDelimiter):
                rawSentences.append(sentenceComposites)
                sentenceComposites = []
            else:
                sentenceComposites.append(spanToken)
        rawSentences.append(sentenceComposites)
        return rawSentences
    def components(self):
        return self.__sentences
    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        for sentence in components:
            md += f'- {sentence}\n'
        return md
    def __str__(self) -> str:
        cumulativeString = ''
        for sentence in self.__sentences:
            cumulativeString += f'{sentence} '
        return cumulativeString[:-1]

class IndentedListItem(Component):
    def __init__(self, content:Block, indentSize=0, level=0, leader=''):
        self.__level = level
        self.__content = content
        self.__leader = leader
        self.__indentSize = indentSize
        self.__prefix = ' ' * ((indentSize * level) - len(leader))
        self.__prefix += leader
    def __str__(self) -> str:
        return f'{self.__prefix}{self.__content}'
    def height(self, lineWidth=LINEWIDTH) -> int:
        return math.ceil(len(str(self)) / lineWidth)

class Item:
    def __init__(self, mdContent:Block):
        self.__leader = mdContent.leader
        self.__content = mdContent
        self.__indentSize = len(self.__leader) + 1
        self.__children = []
        for child in self.__content.children:
            self.__children.append(asBlock(child))
    def height(self):
        cumulativeHeight = 0
        for child in self.__children:
            cumulativeHeight += child.height()
        return cumulativeHeight
    def content(self):
        return self.__content
    def items(self, level=0, indentSize=0, leader=''):
        itemsDFS = []
        if len(self.__children) > 0:
            itemsDFS += self.__children[0].items(
                    level=level+1, 
                    indentSize=self.__indentSize, 
                    leader=f'{self.__leader} '
            )
            for child in self.__children[1:]:
                #itemsDFS.append(child)
                itemsDFS += child.items(level=level+1, indentSize=self.__indentSize, leader='')
        return itemsDFS
    def components(self) -> list:
        return self.items()

class ListBlock(CompositeBlock):
    def __init__(self, mdList:List):
        self.__mdList = mdList
        self.__items = []
        for item in self.__mdList.children:
            self.__items.append(asBlock(item))
    def height(self, lineWidth=LINEWIDTH):
        cumulativeHeight = 0
        for item in self.__items:
            cumulativeHeight += item.height()
        return cumulativeHeight
    def nthItem(self, n:int) -> Block:
        return self.__items[n]
    def items(self, level=0, indentSize=0, leader='') -> list:
        itemsDFS = []
        for item in self.__items:
            itemsDFS += item.items(level=level, indentSize=indentSize, leader=leader)
        return itemsDFS
    def components(self) -> list:
        return self.items()
    def __str__(self) -> str:
        cumulativeString = ''
        for items in self.items():
            cumulativeString += f'{items}\n'
        return cumulativeString[:-1]
    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        for line in components:
            md += f'{line}\n'
        return md
    #override CompositeBlock.slides() to prevent orphaned list item children
class CodeLine(Component):
    def __init__(self, content):
        self.__content = content
    def height(self, lineWidth=LINEWIDTH):
        return math.ceil(len(self.__content) / lineWidth)
    def __str__(self) -> str:
        return self.__content

class CodeBlock(CompositeBlock):
    def __init__(self, mdCodeFence:CodeFence):
        self.__language = mdCodeFence.language
        self.__lines = []
        for lineContent in mdCodeFence.children[0].content.split('\n'):
            self.__lines.append(CodeLine(lineContent))
    def components(self):
        return self.__lines
    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        md += f'```{self.__language}\n'
        for line in components:
            md += f'{line}\n'
        md += '```'
        return md

class QuoteBlock(CompositeBlock):
    def __init__(self, mdContent):
        self.__mdQuote = mdContent
        self.__children = []
        for child in self.__mdQuote.children:
            self.__children.append(asBlock(child))
    def components(self):
        return self.__children
    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        for line in components:
            md += f'> {line}\n'
        return md
    def __str__(self) -> str:
        cumulativeString = ''
        for child in self.__children:
            cumulativeString += f'> {child} '
        return cumulativeString[:-1]
    def height(self, lineWidth=LINEWIDTH) -> int:
        cumulativeHeight = 0
        for child in self.__children:
            cumulativeHeight += math.ceil(len(str(child)) / lineWidth)#change height calculation
        return cumulativeHeight

def extractedMathEnvironments(mathBlock, environment) -> dict:#does not support nested environments e.g. matrix inside a matrix
    pattern = Template(r'\\begin{$env}.*?\\end{$env}')
    multilinePattern = re.compile(pattern.substitute(env=environment))
    multilineBlocks = multilinePattern.findall(mathBlock)
    replacedMathBlock = re.sub(multilinePattern, f'$${environment}$$', mathBlock)
    return {'extractedBlocks':multilineBlocks, 'replacedMathBlock':replacedMathBlock}

class MathLine(Component):
    def __init__(self, mathTeX:str):
        self.__mathTeX = mathTeX
    def height(self, lineWidth=LINEWIDTH):
        return self.__mathTeX.count('\\\\') + 1
    def __str__(self) -> str:
        return self.__mathTeX

def rawTex(mathParagraph):
    rawLines = [line for line in mathParagraph.children]
    cumulativeString = ''
    for span in mathParagraph.children:
        if isinstance(span, EscapeSequence):
            cumulativeString += f'\\{span.children[0].content}'
        else:
            cumulativeString += span.content
    return cumulativeString[2:-2]
        


class MathBlock(CompositeBlock):
    def __init__(self, mdParagraph:Paragraph):
        self.__isAligned = False
        jointLines = rawTex(mdParagraph) 
        if jointLines.startswith('\\begin{aligned}') and jointLines.endswith('\\end{aligned}'):
            self.__isAligned = True
            jointLines = jointLines[15:-13]
        multilineEnvironments = ['bmatrix','matrix']
        extractedBlocks = {}
        #remove all multiline blocks (e.g. matrices) while saving removed blocks to extractedBlocks
        for env in multilineEnvironments:
            exME = extractedMathEnvironments(jointLines, env)
            jointLines = exME['replacedMathBlock']
            extractedBlocks[env] = exME['extractedBlocks']
        #now that all multiline blocks are gone, replace newline separators with $$nl$$ token
        #this replacement is now safe since there are no multiline environments in the string
        jointLines = jointLines.replace('\\\\', '$$nl$$')
        #place all extracted blocks back
        for env in multilineEnvironments:
            for block in extractedBlocks[env]:
                jointLines = jointLines.replace(f'$${env}$$', block, 1)
        #safely split the math block using the $$nl$$ token
        self.__lines = [MathLine(line) for line in jointLines.split('$$nl$$')]
    def components(self):
        return self.__lines
    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        md += f'<div>\n$$\n'
        if self.__isAligned:
            md += '\\begin{aligned}\n'
        for line in components:
            md += f'{line}\\\\\n'
        if len(components) > 0:
            md = f'{md[:-3]}\n'#remove the latex newline '\\' on the last line  
        if self.__isAligned:
            md += '\\end{aligned}\n'
        md += '$$\n</div>'
        return md
    def __str__(self) -> str:
        cumulativeString = ''
        for component in self.__lines:
            cumulativeString += f'{str(component)} \\\\' 

        if self.__isAligned:
            return '<div> $$ \\begin{aligned} ' + cumulativeString + ' \\end{aligned} $$ </div>'
        else:
            return '<div> $$ ' + cumulativeString + ' $$ </div>'

def isImageBlock(paragraph:Paragraph):
    return len(paragraph.children) == 1 and isinstance(paragraph.children[0], Image)

class ImageBlock(Block):
    def __init__(self, paragraph:Paragraph):
        self.__mdImage = paragraph.children[0]
        self.__altText:Sentence = collapse(self.__mdImage.children)
        self.__title = self.__mdImage.title
        self.__src = self.__mdImage.src
    def height(self, lineWidth=LINEWIDTH):
        return 1
    def slideContent(self, head:Head):
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        md += f'![{self.__altText}]({self.__src})'
        return md


def collapse(spanList:list) -> Sentence:
    '''
    Collapses a list of span tokens and returns Sentence
    '''
    emphasizedParts = []
    strongParts = []
    mdSpanList = []
    for token in spanList:
        if isinstance(token, Emphasis):
            emphasizedParts.append(collapse(token.children))
        elif isinstance(token, Strong):
            strongParts.append(collapse(token.children))
        with MarkdownRenderer() as renderer:
            mdSpanList.append(renderer.render(token)[:-1])

    s = Sentence(''.join(mdSpanList))
    if len(emphasizedParts) > 0:
        s = EmphasizedSentence(s,emphasizedParts)
    if len(strongParts) > 0:
        s = StrongSentence(s,strongParts)
    return s

