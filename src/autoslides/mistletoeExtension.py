import json
from abc import ABC,abstractmethod
from bullets import *

class MDContent(ABC):
    @abstractmethod
    def breakdown:
        pass

class MDHeading:
    def texForm(self):
        return self.content

    def headForm(self):
        return Head(self.content, self.level)

class MDList(MDContent):
    def breakdown(self):
        with MarkdownRenderer() as renderer:
            return [Bullet(renderer.render(child)) for child in self.children if len(child.content) != 0]
        return []

class MDQuote(MDContent):
    pass

class MDParagraph(MDContent):
    def breakdown(self):
        return [Bullet(child.content) for child in self.children if len(child.content) != 0]

    def texForm(self):
        return [child for child in self.children if len(child.content) != 0].join('. ')

class MDRawText(MDContent):
    pass

class MDImage(MDContent):
    pass

class MDEmphasis(MDContent):
    pass

class MDEscapeSequence(MDContent):
    pass


