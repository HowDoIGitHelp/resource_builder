from abc import ABC, abstractmethod
from args import LINEWIDTH
from mistletoe.block_token import TableCell, TableRow
from mistletoe.span_token import Emphasis, Strong
from mistletoe.markdown_renderer import MarkdownRenderer
import math


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


class IndentedListItem(Component):

    def __init__(self, content:'Block', indentSize=0, level=0, leader=''):
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

    def level(self):
        return self.__level

    def isLooseItem(self):
        return self.__content.isLooseItem() and len(self.__leader) == 0


class CodeLine(Component):

    def __init__(self, content):
        self.__content = content

    def height(self, lineWidth=LINEWIDTH):
        return math.ceil(len(self.__content) / lineWidth)

    def __str__(self) -> str:
        return self.__content


class MathLine(Component):

    def __init__(self, mathTeX:str):
        self.__mathTeX = mathTeX

    def height(self, lineWidth=LINEWIDTH):
        return self.__mathTeX.count('\\\\') + 1

    def __str__(self) -> str:
        return self.__mathTeX


class Cell:

    def __init__(self, content:TableCell):
        self.__content = collapse(content.children)
        self.__align = content.align

    def height(self, lineWidth=LINEWIDTH) -> int:
        return self.__content.height(lineWidth)

    def __str__(self) -> str:
        return str(self.__content)


class Row(Component):

    def __init__(self, content:TableRow):
        self.__cells = [Cell(child) for child in content.children]

    def height(self, lineWidth=LINEWIDTH):
        tallestCell = self.__cells[0]
        for cell in self.__cells[1:]:
            if cell.height(lineWidth) > tallestCell.height(lineWidth):
                tallestCell = cell
        return tallestCell.height(lineWidth)

    def __str__(self) -> str:
        cumulativeString = '|' if len(self.__cells) > 0 else '' 
        for cell in self.__cells:
            cumulativeString += f' {str(cell)} |'
        return cumulativeString

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
