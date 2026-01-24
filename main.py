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
    preamble = open('slidesPre.html','r').read()
    postamble = open('slidesPost.html','r').read()
    output = open('slides.html', 'w+')
    output.write(preamble)

    for child in Document(file.read()).children:
        if isinstance(child, Heading):
            currentHead = Head(child)
            if currentHead.level() < 4:
                output.write(currentHead.mdSlides())
        else:
            output.write(asBlock(child, verbose = False).mdSlides(head = currentHead))

    output.write(postamble)

if __name__ == "__main__":
    main()
