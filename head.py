from mistletoe.block_token import Heading
from component import collapse
from args import LINEWIDTH

class Head:

    def __init__(self, mdHeading:Heading):
        self.__level = mdHeading.level
        self.__content = collapse(mdHeading.children)

    def height(self, lineWidth=LINEWIDTH):
        return 0

    def headText(self) -> str:
        return str(self.__content)

    def level(self):
        return self.__level

    def mdSlides(self) -> str:
        md = ''
        md += 'class: center, middle\n'
        md += f'# {self.headText()}'
        md += '\n\n---\n'
        return md
