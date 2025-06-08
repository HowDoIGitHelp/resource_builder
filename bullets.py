from ASTcollapser import *

class Head:
    def __init__(self, content:str, level:int):
        self.__content = content
        self.__level = level

class Bullet:
    def __init__(self, content:str):
        self.__content = content

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


