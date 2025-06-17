# header one

Paragraphs with ***strong* *emphasis***.
Paragraph $1+3-3$ **is a paragraph**.
I *should* be **part of** `the previous` paragraph.

another paragraph with [links][1].

## math

$$
\begin{aligned}
x &= 2y\\
y &= 2x\\
e &= \begin{bmatrix}
1 & 2\\
3 & 1
\end{bmatrix}
\end{aligned}
$$

# quote 

> Paragraph quoted.
> same paragraph quoted.
> > Double quoted.
> > Double quoted sentence 2.

# code

```python
with open('test.md','r') as mdfile:
    #with MarkdownRenderer() as renderer:
    doc = Document(mdfile)
    blocks = []
    for i,child in enumerate(doc.children):
        #print(
        if not isInvisible(child):
            blocks.append(asBlock(child))

blocks
```

[**alt** text]:url.png "title"
[1]:url.html