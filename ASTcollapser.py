import json
from string import Template

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

class StrongSentence(Sentence):
    def __init__(self,sentence:Sentence, strongParts:list):
        self.__sentence = sentence
        self.__strongParts = strongParts
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> str:
        return self.__sentence.importantParts() + self.__strongParts

class EmphasizedSentence(Sentence):
    def __init__(self,sentence:Sentence,emphasizedParts:list):
        self.__sentence = sentence
        self.__emphasizedParts = emphasizedParts
    def __str__(self) -> str:
        return str(self.__sentence)
    def importantParts(self) -> list:
        return self.__sentence.importantParts() + self.__emphasizedParts

def splitParagraph(paragraph:dict) -> list:
    '''
    Splits a paragraph into a lines based on SoftBreaks in the ast
    '''
    lineList:list = []
    line:list = []
    for d in paragraph['c']:
        if d['t'] == 'SoftBreak':
            lineList.append(line)
            line = []
        else:
            line.append(d)
    lineList.append(line)
    
    return lineList

def collapse(patternList:list, strongParts:list=[], emphasizedParts:list=[]) -> Sentence:
    '''
    Accepts a list of content patterns and returns Sentence
    '''
    cumulativeStr:str = ''
    strongTemplate:Template = Template('**$strongText**')
    emphasizedTemplate:Template = Template('*$emText*')
    mathTemplate:Template = Template('$$$inlineMath$$')
    codeTemplate:Tempalte = Template('`$inlineCode`')

    for pattern in patternList:
        if pattern['t'] == 'Str':
            cumulativeStr += pattern['c']
        elif pattern['t'] == 'Space':
            cumulativeStr += ' '
        elif pattern['t'] == 'Strong':
            strong = collapse(pattern['c'], strongParts=strongParts, emphasizedParts=emphasizedParts) 
            cumulativeStr += strongTemplate.substitute(strongText=str(strong)) 
            strongParts.append(str(strong))
        elif pattern['t'] == 'Emph':
            emphasis = collapse(pattern['c'], strongParts=strongParts, emphasizedParts=emphasizedParts)
            cumulativeStr += emphasizedTemplate.substitute(emText=str(emphasis)) 
            emphasizedParts.append(str(emphasis))
        elif pattern['t'] == 'Math' and pattern['c'][0]['t'] == 'InlineMath':
            cumulativeStr += mathTemplate.substitute(inlineMath=pattern['c'][1])
        elif pattern['t'] == 'Code':
            cumulativeStr += codeTemplate.substitute(inlineCode=pattern['c'][1])

    sentence = Sentence(cumulativeStr)
    if len(strongParts) > 0:
        sentence = EmphasizedSentence(sentence,strongParts)
    if len(emphasizedParts) > 0:
        sentence = StrongSentence(sentence,emphasizedParts)

    return sentence

