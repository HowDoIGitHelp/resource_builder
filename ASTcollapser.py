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
    def briefString(self) -> str:
        return '' 

class StrongSentence(Sentence):
    def __init__(self,sentence:Sentence, strongPart:str):
        self.__sentence = sentence
        self.__strongPart = strongPart
    def __str__(self) -> str:
        return str(self.__sentence)
    def briefString(self) -> str:
        return f"{self.__sentence.briefString()}, {self.strongPart}" 

class EmphasizedSentence(Sentence):
    def __init__(self,sentence:Sentence,emphasizedPart):
        self.__sentence = sentence
        self.__emphasizedPart = emphasizedPart
    def __str__(self) -> str:
        return str(self.__sentence)
    def briefString(self) -> str:
        return f"{self.__sentence.briefString()}, {self.__emphasizedPart}" 

def collapse(patternList:list, hasStrong:bool=False, hasEmphasis:bool=False) -> Sentence:
    '''
    Accepts a list of content patterns and returns Sentence
    '''
    cumulativeStr:str = ''
    strongTemplate:Template = Template('\\textbf{$strongtext}')
    emphasizedTemplate:Template = Template('\\em{$emtext}')

    for pattern in patternList:
        if pattern['t'] == 'Str':
            cumulativeStr += pattern['c']
        elif pattern['t'] == 'Space':
            cumulativeStr += ' '
        elif pattern['t'] == 'Strong':
            cumulativeStr += strongTemplate.substitute(strongtext=collapse(pattern['c'], hasStrong=True)) 
        elif pattern['t'] == 'Emph':
            cumulativeStr += emphasizedTemplate.substitute(emtext=collapse(pattern['c'], hasEmphasis=True)) 

    sentence = Sentence(cumulativeStr)
    if hasEmphasis:
        sentence = EmphasizedSentence(sentence,'')#to be implemented: strongPart
    if hasStrong:
        sentence = StrongSentence(sentence,'')#to be implemented: emphasizedPart

    return sentence

