from abc import ABC, abstractmethod
from mistletoe.markdown_renderer import MarkdownRenderer, LinkReferenceDefinition, BlankLine
from mistletoe.block_token import Paragraph, Heading, List, ListItem, BlockToken, CodeFence, Quote, Table, TableRow, TableCell
from mistletoe.span_token import LineBreak, RawText, Strong, Emphasis, Image, EscapeSequence, SpanToken
from mistletoe.token import Token
from head import Head
import math
import re
from args import LINES, LINEWIDTH
from component import Component, IndentedListItem, Sentence, MathLine, CodeLine, Row, collapse
from utils import rawTex, extractedMathEnvironments, delimitedTextToken, SentenceDelimiter


class UnsupportedTokenException(Exception):

    def __init__(self, token:BlockToken):
        self.unsupportedToken = token


def isImageBlock(paragraph:Paragraph):
    return len(paragraph.children) == 1 and isinstance(paragraph.children[0], Image)

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


class Block(ABC):

    @abstractmethod
    def height(self) -> int:
        pass

    def itemized(self, level=0, indentSize=0, leader=''):
        return [IndentedListItem(self, level=level, indentSize=indentSize, leader=leader)]

    @abstractmethod
    def slideContent(self, head:Head):
        pass

    def mdSlides(self, head:Head, lines=LINES):
        return f'{self.slideContent(head)}\n---\n\n' 

    def isLooseItem(self):
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
    elif isinstance(token, Table):
        return TableBlock(token)
    else:
        raise UnsupportedTokenException(token)


class CompositeBlock(Block):
    '''
    composite blocks can be split into multiple slides, split is based on number of lines
    '''

    def slides(self, head:Head, lines=LINES, lineWidth=LINEWIDTH) -> list:
        slides = []
        currentHeight = self.components()[0].height(lineWidth) if len(self.components()) > 0 else 0
        currentSlide = [self.components()[0]] if len(self.components()) > 0 else []
        for component in self.components()[1:]:
            if currentHeight + component.height(lineWidth) > lines:
                slides.append(self.slideContent(currentSlide, head))
                currentSlide = [component]
                currentHeight = component.height(lineWidth)
            else:
                currentSlide.append(component)
                currentHeight += component.height(lineWidth)
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
            cumulativeHeight += component.height(lineWidth)
        return cumulativeHeight


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
        return f'{cumulativeString[:-1]}'

    def isLooseItem(self):
        return True

class Item:

    def __init__(self, mdContent:Block):
        self.__leader = mdContent.leader
        self.__content = mdContent
        self.__indentSize = len(self.__leader) + 1
        self.__children = []
        for child in self.__content.children:
            self.__children.append(asBlock(child))

    def height(self, lineWidth=LINEWIDTH):
        cumulativeHeight = 0
        for child in self.__children:
            cumulativeHeight += child.height(lineWidth)
        return cumulativeHeight

    def content(self):
        return self.__content

    def itemized(self, level=0, indentSize=0, leader=''):
        itemsDFS = []
        if len(self.__children) > 0:
            itemsDFS += self.__children[0].itemized(
                    level=level+1, 
                    indentSize=self.__indentSize, 
                    leader=f'{self.__leader} '
            )
            for child in self.__children[1:]:
                #itemsDFS.append(child)
                itemsDFS += child.itemized(level=level+1, indentSize=self.__indentSize, leader='')
        return itemsDFS
    
    def __str__(self) -> str:
        components = self.itemized()
        md = ''
        md += f'{components[0]}\n'
        for i in range(1, len(components)):
            if components[i].isLooseItem() and components[i].level() == components[i-1].level():
                md += '\n'
            md += f'{components[i]}\n'
        return md

    def components(self) -> list:
        return self.itemized()


class ListBlock(CompositeBlock):

    def __init__(self, mdList:List):
        self.__mdList = mdList
        self.__children = []
        for item in self.__mdList.children:
            self.__children.append(asBlock(item))
        #self.__itemsDFS = self.itemized()

    def height(self, lineWidth=LINEWIDTH):
        cumulativeHeight = 0
        for child in self.__children:
            cumulativeHeight += child.height(lineWidth)
        return cumulativeHeight

    def nthItem(self, n:int) -> Block:
        return self.__items[n]
    
    def itemized(self, level=0, indentSize=0, leader='') -> list:
        itemsDFS = []
        for item in self.__children:
            itemsDFS += item.itemized(level=level, indentSize=indentSize, leader=leader)
        return itemsDFS

    def components(self) -> list:
        return self.__children

    def __str__(self) -> str:
        cumulativeString = ''
        for items in self.itemized():
            cumulativeString += f'{items}\n'
        return cumulativeString[:-1]

    def slideContent(self, components:list, head:Head) -> str:
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        md += f'{components[0]}\n'
        for i in range(1, len(components)):
            if components[i].isLooseItem() and components[i].level() == components[i-1].level():
                md += '\n'
            md += f'{components[i]}\n'
        return md

    def __slides(self, head:Head, lines=LINES, lineWidth=LINEWIDTH):
        slides = []
        currentHeight = 0
        currentSlide = []
        for i in range(len(self.components())-1):
            component = self.components()[i]
            nextComponent = self.components()[i+1]
            if currentHeight + component.height(lineWidth) > lines and component.level() >= nextComponent.level():
                slides.append(self.slideContent(currentSlide, head))
                currentSlide = [component]
                currentHeight = component.height(lineWidth)
            else:
                currentSlide.append(component)
                currentHeight += component.height(lineWidth)
        component = self.components()[-1]
        if currentHeight + component.height(lineWidth) > lines and component.level():
            slides.append(self.slideContent(currentSlide, head))
            currentSlide = [component]
            currentHeight = component.height(lineWidth)
        else:
            currentSlide.append(component)
            currentHeight += component.height(lineWidth)

        slides.append(self.slideContent(currentSlide, head))
        return slides


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


class TableBlock(CompositeBlock):
    
    def __init__(self, content:Table):
        self.__header = Row(content.header)
        self.__rows = [Row(child) for child in content.children]
        self.__alignmentRow = '|' if len(content.header.children) > 0 else ''
        for alignCode in content.column_align:
            if alignCode is None:
                self.__alignmentRow += '-----|'
            elif alignCode == 0:
                self.__alignmentRow += ':---:|'
            else:
                self.__alignmentRow += '----:|'


    def height(self, lineWidth=LINEWIDTH):
        cumulativeHeight = self.__header.height(lineWidth)
        for row in self.__rows:
            cumulativeHeight += row.height(lineWidth)
        return cumulativeHeight

    def components(self):
        return self.__rows

    def slideContent(self, components:list, head:Head):
        md = ''
        md += f'# {head.headText()}\n'
        md += '\n'
        md += f'{str(self.__header)}\n'
        md += f'{str(self.__alignmentRow)}\n'
        for row in components:
            md += f'{str(row)}\n'
        return md


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


