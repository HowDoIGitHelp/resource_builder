import json
from string import Template
from abc import ABC, abstractmethod
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.block_token import Paragraph, Heading, List, BlockToken
from mistletoe.span_token import LineBreak, RawText, Strong, Emphasis

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

class CompositeBlock(Block):
    @abstractmethod
    def split(self, lines=4) -> list:
        pass

class TextBlock(Block):
    @abstractmethod
    def height(self, lineWidth=30):
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

def ListBlock(CompositeBlock):
    def __init__(self, mdList:List):
        self.__mdList = mdList
    def height(self, lineWidth=30):
        cumulativeHeight = 0
        for item in self.children:
            for child in item.children:
                if isinstance(child, Paragraph):
                    cumulativeHeight += paragraphHeight(child)
                elif isinstance(child, List):
                    cumulativeHeight += child.height
        return cumulativeHeight
    def split(self, lines=4) -> list:
        pass

def paragraphSize(paragraph:Paragraph):
    with MarkdownRenderer() as renderer:
        return renderer.render(len(paragraph))

def paragraphHeight(paragraph:Paragraph, lineWidth=30):
    return math.ceil(paragraphSize(paragraph) / lineWidth)
           
def splitParagraph(paragraph:Paragraph) -> list:
    '''
    Splits a paragraph into a lines based on SoftBreaks (single line breaks)
    '''
    lineList:list = []
    line:list = []
    for child in paragraph.children:
        if isinstance(child,LineBreak):
            lineList.append(line)
            line = []
        else:
            line.append(child)
    lineList.append(line)
    
    return lineList

def collapse(spanList:list) -> Sentence:
    '''
    Accepts a list of content patterns and returns Sentence
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

