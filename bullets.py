from mistletoe import Document
from mistletoe.markdown_renderer import markdown_renderer
from mistletoe.latex_renderer import latex_renderer

class Head:
    def __init__(self, content:str, level:int):
        self.__content = content
        self.__level = level

class Bullet:
    def __init__(self, content:str):
        self.__content = content
        self.__head = head

class Block:
    def __init__(self, content:str):
        self.__content = content
        self.__head = head


class ImageBlock(Block):
    pass

class MathBlock(Block):
    pass

class TableBlock(Block):
    pass

def contentStream(self, file:File):
    with MardownRenderer() as renderer:
        markdownTree = Document(file)

