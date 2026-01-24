from mdPreprocess import preprocess
from block import asBlock
from mistletoe import Document
from mistletoe.block_token import Heading
from component import collapse
from head import Head

def main():
    file = open('Counting and Discrete Probability.md', 'r')
    processedMD = preprocess(open('Counting and Discrete Probability.md', 'r'))
    currentHead = None
    for child in Document(file.read()).children:
        if isinstance(child, Heading):
            currentHead = Head(child)
        else:
            print(asBlock(child).mdSlides(head = currentHead))

if __name__ == "__main__":
    main()
