import re
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer,BlankLine, LinkReferenceDefinition
from mistletoe.html_renderer import HTMLRenderer
from mistletoe.block_token import Paragraph, BlockToken

class ProcessedBlockToken:
    def __init__(self, blockToken:BlockToken):
        self.__blockToken = blockToken
    def processedRender(self):
        with MarkdownRenderer() as renderer:
            mdRender = renderer.render(self.__blockToken)
        return mdRender

class ProcessedParagraph(ProcessedBlockToken):
    def __init__(self, blockToken:BlockToken):
        self.__blockToken = blockToken
    def processedRender(self):
        with MarkdownRenderer() as renderer:
            rawParagraph = renderer.render(self.__blockToken)
        rawParagraph = rawParagraph.replace('\n',' ')
        rawParagraph = rawParagraph.replace('$$ ', '$$\n')
        rawParagraph = rawParagraph.replace(' $$', '\n$$')
        rawSentences = re.split(r'\.\ ', rawParagraph)
        return '.\n'.join([sentence for sentence in rawSentences if sentence != '']) + '\n'

def preprocess(file):
    processedContents = ''
    for child in Document(file).children:
        if isinstance(child, Paragraph):
            processedContents += f'{ProcessedParagraph(child).processedRender()}\n'
        else:
            processedContents += f'{ProcessedBlockToken(child).processedRender()}\n'

    return processedContents
