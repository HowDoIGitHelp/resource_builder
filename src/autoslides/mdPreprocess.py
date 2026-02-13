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
        rawParagraph = rawParagraph.replace("\n"," ")
        rawParagraph = rawParagraph.replace("$$ ", "$$\n")
        rawParagraph = rawParagraph.replace(" $$", "\n$$")
        rawSentences = re.split(r"\.\ ", rawParagraph)
        return ".\n".join([sentence for sentence in rawSentences if sentence != ""]) + "\n"

def preprocess(contents: str) -> str:
    processedContents = ""
    for child in Document(contents).children:
        if isinstance(child, Paragraph):
            processedContents += f"{ProcessedParagraph(child).processedRender()}\n"
        else:
            processedContents += f"{ProcessedBlockToken(child).processedRender()}\n"

    return processedContents

def escapedMathUnderscores(contents: str) -> str:
    pattern = r"(?<!\$)\$([^$]+)\$(?!\$)"
    escapedUnderscores = re.sub(pattern, lambda m: m.group(0).replace("_", r"\_"), contents)
    fixedLinebreaks = re.sub(pattern, lambda m: m.group(0).replace("\\", "\\\\"), contents)
    return fixedLinebreaks

def truncatedFrontmatter(contents: str) -> str:
    lines = contents.split("\n")
    trueStart = 0
    if lines[0] == "---":
        trueStart = 1
        i = 1
        while lines[i] != "---":
            i += 1
        if i < len(lines):
            trueStart = i + 1
    return "\n".join(lines[trueStart:])


