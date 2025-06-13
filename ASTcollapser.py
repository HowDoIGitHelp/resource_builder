import json
from string import Template
from abc import ABC, abstractmethod
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.block_token import Paragraph, Heading, List, ListItem, BlockToken
from mistletoe.span_token import LineBreak, RawText, Strong, Emphasis
import math
class Sentence:
    '''
    base class that can be decorated by StrongSentence and EmphasizedSentence
    '''
    def __init__(self,sentence:str):
        self.__sentence = sentence
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> list:
        return [] 

class Block(ABC):
    @abstractmethod
    def mdContent(self) -> str:
        pass
    @abstractmethod
    def height(self) -> int:
        pass

class CompositeBlock(Block):
    '''
    composite blocks can be split into multiple slides, split is based on number of lines
    '''
    @abstractmethod
    def split(self, lines=4) -> list:
        pass

class SlideContent(ABC):
    @abstractmethod
    def mdContent(self):
        pass
    
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

class UnsupportedTokenException(Exception):
    pass

def asBlock(token:BlockToken) -> Block:
    '''
    convert mistletoe.block_token.BlockToken into Blocks
    '''
    if isinstance(token, Paragraph):
        return ParagraphBlock(token)
    elif isinstance(token, List):
        return ListBlock(token)
    elif isinstance(token, ListItem):
        return ItemBlock(token)
    else:
        raise UnsupportedTokenError()

class ParagraphBlock(CompositeBlock):
    def __init__(self, mdParagraph:Paragraph):
        self.__mdParagraph = mdParagraph
        self.__sentences = [collapse(spanList) for spanList in self.decompose()]
    def decompose(self) -> list:
        '''
        Decompose a paragraph into list of span tokens based on SoftBreaks (single line breaks)
        '''
        lineList:list = []
        line:list = []
        for child in self.__mdParagraph.children:
            if isinstance(child,LineBreak):
                lineList.append(line)
                line = []
            else:
                line.append(child)
        lineList.append(line)
        return lineList
    def paragraphSize(self):
        with MarkdownRenderer() as renderer:
            return len(renderer.render(self.__mdParagraph))
    def height(self, lineWidth=30):
        return math.ceil(self.paragraphSize() / lineWidth)
    def mdContent(self):
        pass
    def split(self):
        pass
class ItemBlock(CompositeBlock):
    def __init__(self, mdContent:Block):
        self.__leader = mdContent.leader
        self.__content = mdContent
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
    def mdContent(self) -> str:
        pass
    def split(self, lines=4):
        pass
class ListBlock(CompositeBlock):
    def __init__(self, mdList:List):
        self.__mdList = mdList
        self.__items = []
        for item in self.__mdList.children:
            self.__items.append(asBlock(item))
    def height(self, lineWidth=30):
        cumulativeHeight = 0
        for item in self.__items:
            cumulativeHeight += item.height()
        return cumulativeHeight
    def nthItem(self, n:int) -> Block:
        return self.__items[n]
    def split(self, lines=4) -> list:
        pass
    def mdContent(self) -> str:
        pass


           

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

