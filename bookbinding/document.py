from reportlab.pdfgen.canvas import Canvas

inch = 72.

FONT_SIZE = 10.
LINE_HEIGHT = FONT_SIZE + 2.

PAGE_WIDTH = 6. * 72.
PAGE_HEIGHT = 9. * 72.

INNER_MARGIN = 54.
OUTER_MARGIN = inch
BOTTOM_MARGIN = inch + 6.
TOP_MARGIN = inch - 6.

class Setter(object):
    pass

class Page(object):

    def __init__(self, document, folio=0, previous=None):
        self.document = document
        self.folio = folio
        self.previous = previous

    def next(self):
        return Page(self.document, self.folio + 1, self)

class Chase(object):
    def __init__(self, page, x, y, w, h):
        self.page = page
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def next(self):
        return Chase(self.page.next(), self.x, self.y, self.w, self.h)

class Document(object):

    def format(self, story):

        p = Page(self, 0)
        c = Chase(p, OUTER_MARGIN, BOTTOM_MARGIN,
                  PAGE_WIDTH - OUTER_MARGIN - INNER_MARGIN,
                  PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN)

        canvas = Canvas(
            'book.pdf', pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
        canvas.setFont('Roman', FONT_SIZE)

        line = Line(c)
        line.text = u'foo'
        for item in story:
            if item.__class__.__name__ == 'Spacer':
                if line.at_bottom():
                    line = line.next()
                    line.words = [u'*']
                    line.align = 'center'
                line = line.next()
                if line.at_bottom():
                    line = line.down(1)
                    line.words = [u'*']
                    line.align = 'center'
            elif isinstance(item, Paragraph):
                for s in [item.text]:
                    line = wrap_paragraph(canvas, line, item)

        lines = []
        while line:
            lines.append(line)
            line = line.previous

        lines.reverse()

        page = None
        for line in lines:
            if line.chase.page is not page:
                canvas.showPage()
                canvas.setFont('Roman', FONT_SIZE)
                page = line.chase.page
            if line.justify:
                ww = canvas.stringWidth(u''.join(line.words))
                space = (line.w - line.indent - ww) / (len(line.words) - 1)
                x = 0
                for word in line.words:
                    canvas.drawString(c.x + x + line.indent, line.ay(), word)
                    x += space + canvas.stringWidth(word)
            elif line.align == 'center':
                s = u' '.join(line.words)
                ww = canvas.stringWidth(s)
                canvas.drawString(c.x + line.chase.w / 2. - ww / 2.,
                                  line.ay(), s)
            else:
                canvas.drawString(c.x, line.ay(), u' '.join(line.words))

        canvas.save()

def wrap_paragraph(canvas, line, pp):
    words = pp.text.split()
    indent = FONT_SIZE if pp.style.startswith('indented') else 0
    width = line.w - indent
    while words:
        i = 2
        el = u' '.join(words[:i])
        while canvas.stringWidth(el) < width:
            if i >= len(words):
                break
            el += u' ' + words[i]
            i += 1
        else:
            i -= 1
        line = line.next()
        line.words = words[:i]
        line.justify = i < len(words)
        line.indent = indent
        words = words[i:]
        indent, width = 0, line.w
    return line

class Line(object):

    def __init__(self, chase, previous=None, y=None):
        if y is None:
            y = chase.h - LINE_HEIGHT
        self.chase = chase
        self.w = chase.w
        self.y = y
        self.previous = previous
        self.justify = None
        self.words = ()
        self.align = None

    def next(self):
        if not self.at_bottom():
            return self.down(1)
        else:
            next_chase = self.chase.next()
            return Line(next_chase, previous=self)

    def down(self, n):
        return Line(self.chase, previous=self, y=self.y - n * LINE_HEIGHT)

    def at_bottom(self):
        return self.y <= LINE_HEIGHT

    def ay(self):
        return self.chase.y + self.y

class Paragraph(object):

    def __init__(self, text, style):
        self.text = text
        self.style = style
