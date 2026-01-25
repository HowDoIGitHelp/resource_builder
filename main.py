from mdPreprocess import preprocess
from block import asBlock
from mistletoe import Document
from mistletoe.block_token import Heading
from component import collapse
from head import Head
import argparse

def main(args):
    file = open(args.source, 'r')
    processedMD = preprocess(file)
    open('temp.md','w+').write(processedMD)
    currentHead = None
    preamble = open('slidesPre.html','r').read().replace('{Title}', args.source)
    postamble = open('slidesPost.html','r').read()

    outputFileName = f"{args.source.split('.')[0]}.html"
    output = open(outputFileName, 'w+')
    output.write(preamble)

    for child in Document(processedMD).children:
        if isinstance(child, Heading):
            currentHead = Head(child)
            if currentHead.level() < 4:
                output.write(currentHead.mdSlides())
        else:
            output.write(asBlock(child, verbose = False).mdSlides(head = currentHead))

    output.write(postamble)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--source')
    args = parser.parse_args()
    main(args)
