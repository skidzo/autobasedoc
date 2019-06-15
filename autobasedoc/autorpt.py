# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 16:45:06 2013

Class AutoDocTemplate customized for automatic document creation
this inherits and partly redefines reportlab code

"""
from __future__ import print_function

import os
import sys

from autobasedoc import is_python3
import autobasedoc.autoplot as ap

from hashlib import sha1
from operator import attrgetter
from itertools import count
from collections import OrderedDict
import copy
import random
import string

from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm, mm  #,pica

from reportlab.platypus import (Image, Paragraph, PageBreak, Table, TableStyle,
                                Spacer, Flowable, KeepTogether, FrameBreak, PageBegin)

from reportlab.platypus.doctemplate import (
    BaseDocTemplate, PageTemplate, NextPageTemplate, _doNothing, LayoutError,
    ActionFlowable, FrameActionFlowable, _addGeneratedContent, _fSizeString,
    NullActionFlowable)

from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import SlowPageBreak, DDIndenter, PageBreakIfNotEmpty
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle

# Configure Fonts!
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import getFont
from reportlab.pdfbase.pdfdoc import PDFInfo
from reportlab.pdfbase.ttfonts import TTFont

from autobasedoc import base_fonts

_baseFontNames = base_fonts()
_basePath = os.path.realpath(os.path.dirname(__file__))

sys.path.append(_basePath)

# #TODO: cx Freeze, this needs adoption to your version of cx_freeze
# if _basePath.endswith("library.zip"):
#     _basePath = os.path.realpath(os.path.join(_basePath, '../'))

__font_dir__ = os.path.realpath(os.path.join(_basePath, "fonts"))
#__assets_dir__ = os.path.realpath(os.path.join(_basePath,"assets"))

color_dict = {}


def setup_color_dict(colors):
    """
    setup colors
    only adding items where key is str AND value is Color to the color_dict
    """
    for k, v in vars(colors).items():
        if isinstance(k, str) and isinstance(v, Color):
            color_dict.update({k: v})


setup_color_dict(colors)

color_dict.update({
    'gray40': Color(0.4, 0.4, 0.4, 1),
    'lightred': Color(.980392, .501961, .447059, 1)
})


def registerFont(faceName, afm, pfb):
    """
    Helvetica BUT AS AFM

    The below section is NOT equal to::

        _baseFontName  ='Helvetica'
        _baseFontNameB ='Helvetica-Bold'
        _baseFontNameI ='Helvetica-Oblique'
        _baseFontNameBI='Helvetica-BoldOblique'

    we will mapp afm files from matplotlib with pfb files from reportlab

    this will give embedded Type1 Face Fonts

    """
    afm = os.path.join(__font_dir__, "".join(afm, ".afm"))
    pfb = os.path.join(__font_dir__, "".join(pfb, ".pfb"))

    face = pdfmetrics.EmbeddedType1Face(afm, pfb)
    pdfmetrics.registerTypeFace(face)
    justFont = pdfmetrics.Font(faceName, faceName, 'WinAnsiEncoding')
    pdfmetrics.registerFont(justFont)


def setTtfFonts(familyName,
                font_dir,
                normal=(None, None),
                bold=(None, None),
                italic=(None, None),
                bold_italic=(None, None)):
    """
    Sets fonts for True Type Fonts
    """
    normalName, normalFile = normal
    boldName, boldFile = bold
    italicName, italicFile = italic
    bold_italicName, bold_italicFile = bold_italic

    pdfmetrics.registerFont(
        TTFont(normalName, os.path.join(font_dir, normalFile)))
    pdfmetrics.registerFont(TTFont(boldName, os.path.join(font_dir, boldFile)))
    pdfmetrics.registerFont(
        TTFont(italicName, os.path.join(font_dir, italicFile)))
    pdfmetrics.registerFont(
        TTFont(bold_italicName, os.path.join(font_dir, bold_italicFile)))

    addMapping(familyName, 0, 0, normalName)
    addMapping(familyName, 1, 0, boldName)
    addMapping(familyName, 0, 1, italicName)
    addMapping(familyName, 1, 1, bold_italicName)

    base_fonts().update({"normal": getFont(normalName).fontName})
    base_fonts().update({"bold": getFont(boldName).fontName})
    base_fonts().update({"italic": getFont(italicName).fontName})
    base_fonts().update({"bold_italic": getFont(bold_italicName).fontName})


def setFonts(typ):
    """
    Sets fonts for standard font-types

    :param typ: one of sans-serif-afm, serif (sans-serif is default on init)
    :type typ: str
    """
    if typ == 'sans-serif-afm':
        baseNameDict = {
            'Helvetica': "_a______",
            'Helvetica-Bold': "_ab_____",
            'Helvetica-Oblique': "_ai_____",
            'Helvetica-BoldOblique': "_abi____"
        }

        for afm, pfb in baseNameDict.items():
            faceName = afm
            registerFont(faceName, afm, pfb)

        base_fonts().update({
            "normal": pdfmetrics.getFont('Helvetica').fontName
        })
        base_fonts().update({
            "bold": pdfmetrics.getFont('Helvetica-Bold').fontName
        })
        base_fonts().update({
            "italic": pdfmetrics.getFont('Helvetica-Oblique').fontName
        })
        base_fonts().update({
            "bold_italic": pdfmetrics.getFont('Helvetica-BoldOblique').fontName
        })

    elif typ == 'serif':
        setTtfFonts(
            'Calibri',
            __font_dir__,
            normal=('Calibri', 'CALIBRI.TTF'),
            italic=('CalibriBd', 'CALIBRIB.TTF'),
            bold=('CalibriIt', 'CALIBRII.TTF'),
            bold_italic=('CalibriBI', 'CALIBRIZ.TTF'))


def reprFrame(frame):
    _dict = vars(frame)
    for key in sorted(list(_dict.keys())):
        print(key, ": ", _dict[key])


def getTableStyle(tSty=None, tSpaceAfter=0, tSpaceBefore=0):
    """
    :param tSty: TableStyle(tSty) default is None
    :param tSpaceBefore: space before table, default: 0
    :param tSpaceAfter: space after table, default: 0

    :returns: TableStyle object

    use the add method of that object to add style commands e.g.:
    to add a background in the first row::

        tableStyle.add(("BACKGROUND",(0,0),(2,0),ar.colors.green))
        tableStyle.add(("BACKGROUND",(2,0),(4,0),ar.colors.lavender))

    to change text color on the first two columns::

        tableStyle.add(("TEXTCOLOR",(0,0),(1,-1),ar.colors.red))

    to change alignment of all cells to 'right'::

        tableStyle.add(("ALIGN",(0,0),(-1,-1),"RIGHT"))

    to add a grid for the whole table::

        tableStyle.add(("GRID",(0,0),(-1,-1),0.5,ar.colors.black))

    some further examples of command entries::

        ("ALIGN",(0,0),(1,-1),"LEFT"),
        ("ALIGN",(1,0),(2,-1),"RIGHT"),
        ("ALIGN",(-2,0),(-1,-1),"RIGHT"),
        ("GRID",(1,1),(-2,-2),1,ar.colors.green),
        ("BOX",(0,0),(1,-1),2,ar.colors.red),
        ("LINEABOVE",(1,2),(-2,2),1,ar.colors.blue),
        ("LINEBEFORE",(2,1),(2,-2),1,ar.colors.pink),
        ("BACKGROUND", (0, 0), (0, 1), ar.colors.pink),
        ("BACKGROUND", (1, 1), (1, 2), ar.colors.lavender),
        ("BACKGROUND", (2, 2), (2, 3), ar.colors.orange),
        ("BOX",(0,0),(-1,-1),2,ar.colors.black),
        ("GRID",(0,0),(-1,-1),0.5,ar.colors.black),
        ("VALIGN",(3,0),(3,0),"BOTTOM"),
        ("BACKGROUND",(3,0),(3,0),ar.colors.limegreen),
        ("BACKGROUND",(3,1),(3,1),ar.colors.khaki),
        ("ALIGN",(3,1),(3,1),"CENTER"),
        ("BACKGROUND",(3,2),(3,2),ar.colors.beige),
        ("ALIGN",(3,2),(3,2),"LEFT"),
        ("GRID", (0,0), (-1,-1), 0.25, ar.colors.black),
        ("ALIGN", (1,1), (-1,-1), "RIGHT")
        ("FONTSIZE", (1,0), (1,0), self.fontsizes["table"])

        ('SPAN',(1,0),(1,-1))
    """
    if not tSty:
        tSty = list()
    else:
        pass

    tableStyle = TableStyle(tSty)

    tableStyle.spaceAfter = tSpaceAfter
    tableStyle.spaceBefore = tSpaceBefore

    return tableStyle


class StyledTable(object):
    """
    data object to store all data and styles of ONE table

    This class is an independent representation for the metadata and parameters
    of the results to be shown in ONE table::

        +----------------------------------+
        |            table                 |
        |                                  |
        +----------------------------------+


    """

    def __init__(self, gridded=False, leftTablePadding=0, hTableAlignment=None):
        """
        :param gridded: if True, the table style is gridded, default is False
        :type gridded: bool
        :param leftTablePadding: if a number > 0 is inserted, the table gets a left empty column to be like left-padded
        :type leftTablePadding: int
        """
        self.hTableAlignment = hTableAlignment
        self.tableData = list()
        self.tableStyleCommands = list()
        # for finalizing specific cell formats
        self.tableExtraStyleCommands = list()
        self.fontsize = 10
        self.addTableStyleCommand(('FONT', (0, 0), (-1, -1),
                                   _baseFontNames["normal"]))
        if gridded:
            self.addTableStyleCommand(("GRID", (0, 0), (-1, -1), 0.5,
                                       colors.black))
        if leftTablePadding:
            self.offsetCol = 1
            self.leftTablePadding = leftTablePadding
        else:
            self.offsetCol = 0
            self.leftTablePadding = 0
        self.headerRow = 0
        self.title = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(5))
        # BUG: VALIGN does not work with different font sizes !!!
        self.addTableStyleCommand(
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'))
        self.addTableStyleCommand(
            ('FONTSIZE', (0, 0), (-1, -1), self.fontsize))

    def setFontSizeColor(self, size, color, row, col):
        """
        FONTSIZE (or SIZE)      - takes fontsize in points; leading may get out of sync.
        TEXTCOLOR
        """
        cmd_size = ("FONTSIZE", (self.offsetCol + col, row),
                    (self.offsetCol + col, row), size)
        cmd_color = ("TEXTCOLOR", (self.offsetCol + col, row),
                     (self.offsetCol + col, row), color)

        # adjust the paddings in the cells with larger fonts
        cmd_padding_bottom = ('BOTTOMPADDING', (self.offsetCol + col, row),
                              (self.offsetCol + col, row), size - self.fontsize + 3)
        cmd_padding_top = ('TOPPADDING', (self.offsetCol + col, row),
                           (self.offsetCol + col, row), 0)
        cmd_padding_right = ('RIGHTPADDING', (self.offsetCol + col, row),
                             (self.offsetCol + col, row), 0.2 * cm)
        self.addTableExtraStyleCommand(cmd_size)
        self.addTableExtraStyleCommand(cmd_color)
        self.addTableExtraStyleCommand(cmd_padding_bottom)
        self.addTableExtraStyleCommand(cmd_padding_top)
        self.addTableExtraStyleCommand(cmd_padding_right)

    def addTableExtraStyleCommand(self, cmd):
        if isinstance(cmd, list):
            for cm in cmd:
                self.tableExtraStyleCommands.append(cm)

        if isinstance(cmd, tuple):
            self.tableExtraStyleCommands.append(cmd)

    def addTableStyleCommand(self, cmd, extra=False):
        """
        Adds style command to table.

        line commands are like:
        op, start, stop, weight, colour, cap, dashes, join, linecount, linespacing

        op is one of:
        GRID, BOX,OUTLINE, INNERGRID, LINEBELOW, LINEABOVE, LINEBEFORE, LINEAFTER

        cell commands are like ...

        :param cmd: one table command data for styles
        :type cmd: tuple
        """
        if isinstance(cmd, list):
            for cm in cmd:
                self.tableStyleCommands.append(cm)
        if isinstance(cmd, tuple):
            self.tableStyleCommands.append(cmd)

    def setTableData(self, data):
        """
        Overwrites the table data with fresh new data.
        If leftTablePadding is activated an empty column is inserted here automatically.

        :param data: the new data
        :type data: list of tuples

        """
        self.tableData = data
        if self.leftTablePadding > 0:
            for t in self.tableData:
                t.insert(0, "")

    def addTableLine(self, line):
        """
        Adds a table line to data.
        If leftTablePadding is activated an empty column is inserted here automatically.

        :param line: the data of one table line
        :type line: tuple, list
        """
        if isinstance(line, tuple):
            line = list(line)
        if self.leftTablePadding > 0:
            line.insert(0, "")
        self.tableData.append(line)

    def addHorizontalLines(self, color="blue", offsetCol=None, exclude=[]):
        """
        Adds horizontal lines only. Apply after inserting all data and after inserting the header line.
        If no header line exists also a top line is included.

        :param color: the color of the horizontal line
        :type color: str
        """
        if offsetCol is None:
            offsetCol = self.offsetCol
        color = getattr(colors, color)
        for ri in range(self.headerRow, self.linesCount()):
            if ri in exclude:
                continue
            self.addTableStyleCommand(
                ("LINEBELOW", (offsetCol, ri), (-1, ri), 0.4, color))
        if self.headerRow == 0:
            self.addTableStyleCommand(
                ("LINEABOVE", (offsetCol, 0), (-1, 0), 0.4, color))

    def addDoubleLine(self, color="blue", line=0):
        """
        Adds a double line below the line specified

        :param line: the number of the line below which the double line is inserted
        :type col: int
        :param color: the color of the vertical line
        :type color: str
        """
        cmd = ("LINEBELOW", (self.offsetCol, line), (-1, line), 0.4,
               color, 1, None, None, 2, 0.6)
        self.tableStyleCommands.append(cmd)

    def addVerticalLine(self, col, color="blue"):
        """
        Adds vertical lines only. Apply after inserting all data.

        :param col: the number of the column after which the vertical line is inserted
        :type col: int
        :param color: the color of the horizontal line
        :type color: str
        """
        color = getattr(colors, color)
        self.addTableStyleCommand(
            ("LINEAFTER", (col + self.offsetCol, 0), (col + self.offsetCol, -1), 0.4, color))

    def addTableHeader(self, line, fonttype="bold", color="blue"):
        """
        Prepends a table line to data and insert the correct styles, like double underline and bold.

        :param line: the data for the header line
        :type line: tuple, list
        :param fonttype: one of normal, bold, italic
        :type fonttype: str
        :param color: the color of the horizontal line
        :type color: str
        """
        self.headerRow = 1
        color = getattr(colors, color)
        line = copy.copy(line)
        if isinstance(line, tuple):
            line = list(line)
        if self.leftTablePadding > 0:
            line.insert(0, "")
        self.tableData.insert(0, line)
        cmd = ('FONT', (self.offsetCol, 0),
               (-1, 0), _baseFontNames[fonttype])
        self.tableStyleCommands.append(cmd)
        self.addDoubleLine()

    def linesCount(self):
        """
        Returns the number of rows/lines including header line.

        """
        return len(self.tableData)

    def colsCount(self):
        """
        Returns the number of columns.

        """
        return len(self.tableData[0])

    def handleStyleCommands(self):
        """
        Creates real tableStyle from tableStyleCommands.

        """
        tableStyle = getTableStyle()
        for cmd in self.tableStyleCommands:
            if not len(cmd) == 0:
                tableStyle.add(*cmd)
        for cmd in self.tableExtraStyleCommands:
            if not len(cmd) == 0:
                tableStyle.add(*cmd)
        return tableStyle

    @property
    def as_flowable(self):
        """
        Shortage name
        """
        if not self.tableData:
            self.tableData = [[""]]
        return self.layoutTable(hTableAlignment=None, colWidths=None)

    def layoutTable(self, hTableAlignment=TA_LEFT, colWidths=None):
        """
        Returns a table flowable with automatically estimated column width.

        :param styledTable: a styled table
        :type styledTable: StyledTable
        :param hTableAlignment: the table alignment on the frame
        :type hTableAlignment: int
        :param colWidths: the columns width in cm
        :type colWidths: list
        :param spaceBefore: the space above the table in cm
        :type spaceBefore: float
        :param spaceAfter: the space below the table in cm
        :type spaceAfter: float

        :returns: a table flowable element
        """
        self.addTableStyleCommand(
            ('LEFTPADDING', (0, 0), (-1, -1), 0.1 * cm))
        self.addTableStyleCommand(
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'))
        if colWidths:
            colWidths = [x * cm for x in colWidths]
        table = Table(self.tableData, colWidths=colWidths,
                         spaceBefore=0, spaceAfter=0)
        table.setStyle(self.handleStyleCommands())
        if hTableAlignment:
            table.hAlign = hTableAlignment
        elif self.hTableAlignment:
            table.hAlign = self.hTableAlignment
        return table


def addPlugin(canv, doc, frame="First"):
    """
    holds all functions to handle placing all elements on the canvas...

    :param canv: canvas object
    :param doc: AutoDocTemplate instance
    :param frame: template name of the Frame

    This function suggests that you have stored page info Items
    in doc.pageInfos.

    By default if there is no frame='Later' option, we use the frame='First'

    If you don't want to decorate your Later pages,
    please define an empty pageTemplate with frame='Later'

    """

    def drawString(pitem, text, posy):
        """
        draws a String in posy:

        - l draws in align 'Left'
        - c draws in align 'Center'
        - r draws in align 'Right'

        """
        if pitem.pos == "l":
            canv.drawString(doc.leftMargin, posy, text)

        elif pitem.pos == "c":
            canv.drawCentredString(doc.centerM, posy, text)

        elif pitem.pos == "r":
            canv.drawRightString(doc.rightM, posy, text)

    def drawLine(pitem, posy):  #,rightMargin=None
        """
        draws a Line in posy::

            l---------------r
        """
        left, right = doc.leftM, doc.rightM

        #print("drawLine at posy:",posy)
        #print("from %s to %s"%(left,right))

        if getattr(pitem, "rightMargin", None):
            right -= pitem.rightMargin

        canv.line(left, posy, right, posy)

    def drawImage(pitem, pos):
        """
        pos = (x,y)

        draws a footer/header image at pos if pitem.pos='r'::

                +-------------------+ pos
                |                   |
                |       image       |
                |                   |
                |                   |
                +-------------------+

        draws a footer/header image at pos if pitem.pos='l'::

            pos +-------------------+
                |                   |
                |       image       |
                |                   |
                |                   |
                +-------------------+

        every image can be shifted/translated if a 'shift' attribute is found on pitem::

                ^
                |y
            pos +-->
                 x
        """

        def shift(pitem, x, y):
            """
            apply shift x,y on pitem
            """
            if getattr(pitem, "shift", None):
                x += pitem.shift[0]
                y += pitem.shift[1]

            return x, y

        x, y = pos

        ### here must be placed a positioning for the three locations

        if pitem.typ.startswith("header"):
            if pitem.pos.startswith("r"):
                x = doc.rightM
                x -= pitem.image.drawWidth
                y -= pitem.image.drawHeight
                x, y = shift(pitem, x, y)

            if pitem.pos.startswith("l"):
                x = doc.leftM
                #x-=pitem.image.drawWidth
                y -= pitem.image.drawHeight
                x, y = shift(pitem, x, y)
            else:
                x, y = shift(pitem, x, y)

        elif pitem.typ.startswith("footer"):
            if pitem.pos.startswith("r"):
                x = doc.rightM
                x -= pitem.image.drawWidth
                y -= pitem.image.drawHeight
                x, y = shift(pitem, x, y)

            if pitem.pos.startswith("l"):
                x = doc.leftM
                #x-=pitem.image.drawWidth
                y -= pitem.image.drawHeight
                x, y = shift(pitem, x, y)
            else:
                x, y = shift(pitem, x, y)

        pitem.image.drawOn(canv, x, y)
        #print("added image")

    lkeys = []

    if doc.pageInfos:

        for pkey, pitem in doc.pageInfos.items():
            #print(pkey)
            #pitem=doc.pageInfos[pkey]
            #print( pitem.frame )

            if pitem.frame.startswith(frame):
                lkeys.append(pkey)

                text = "%s" % pitem.text
                #add Page Number if requested
                if pitem.addPageNumber:
                    text += "%d" % doc.page
                    #if is_talkative:
                    print(text)
                if pitem.typ.startswith("header"):
                    #Header
                    posy = doc.headM
                    if not pitem.text is None:
                        #print("drawString",text)
                        drawString(pitem, text, posy)
                    elif not pitem.image is None:
                        pos = (doc.leftMargin, posy)
                        drawImage(pitem, pos)
                        #print("drawImage",pitem.image)
                    if pitem.line:
                        canv.setLineWidth(doc.lineWidth)
                        drawLine(pitem, posy - doc.topM + doc.fontSize)

                elif pitem.typ.startswith("footer"):
                    #Footer
                    posy = doc.bottomM
                    if not pitem.text is None:
                        drawString(pitem, text, posy)
                    elif not pitem.image is None:
                        pos = (doc.leftMargin, posy)
                        drawImage(pitem, pos)
                        #print("drawImage",pitem.image)
                    if pitem.line:
                        canv.setLineWidth(doc.lineWidth)
                        drawLine(pitem, posy + doc.topM)
                else:
                    break
        if len(lkeys) == 0:
            addPlugin(canv, doc, frame="First")
    else:
        pass
        #print("going through the pageInfo items:",lkeys)


def drawFirstPortrait(canv, doc):
    """
    This is the Title Page Template (Portrait Oriented)
    """
    canv.saveState()
    #set Page Size
    frame, pagesize = doc.getFrame('FirstP', orientation="Portrait")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="First")

    canv.restoreState()


def drawFirstLandscape(canv, doc):
    """
    This is the Template of any later drawn Landscape Oriented Page

    the frame object is only used as a reference to be able to draw to the canvas

    After creation a Frame is not usually manipulated directly by the
    applications program -- it is used internally by the platypus modules.

    Here is a diagramatic abstraction for the definitional part of a Frame::

                width                    x2,y2
        +---------------------------------+
        | l  top padding                r | h
        | e +-------------------------+ i | e
        | f |                         | g | i
        | t |                         | h | g
        |   |                         | t | h
        | p |                         |   | t
        | a |                         | p |
        | d |                         | a |
        |   |                         | d |
        |   +-------------------------+   |
        |    bottom padding               |
        +---------------------------------+
        (x1,y1) <-- lower left corner

    NOTE!! Frames are stateful objects.  No single frame should be used in
    two documents at the same time (especially in the presence of multithreading.
    """
    canv.saveState()
    #set Page Size
    frame, pagesize = doc.getFrame('FirstL', orientation="Landscape")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="First")

    canv.restoreState()


def drawLaterPortrait(canv, doc):
    """
    This is the Template of any following Portrait Oriented Page
    """
    canv.saveState()
    #set Page Size

    frame, pagesize = doc.getFrame('LaterP', orientation="Portrait")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="Later")

    canv.restoreState()


def drawLaterLandscape(canv, doc):
    """
    This is the Template of any later drawn Landscape Oriented Page
    """
    canv.saveState()

    #set Page Size and
    #some variables

    frame, pagesize = doc.getFrame('LaterL', orientation="Landscape")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="Later")

    canv.restoreState()

def drawLaterSpecialPortrait(canv, doc):
    """
    This is the Template of any following Portrait Oriented Page
    """
    canv.saveState()
    #set Page Size

    frame, pagesize = doc.getFrame('LaterSP', orientation="Portrait")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="Later")

    canv.restoreState()


def drawLaterSpecialLandscape(canv, doc):
    """
    This is the Template of any later drawn Landscape Oriented Page
    """
    canv.saveState()

    #set Page Size and
    #some variables

    frame, pagesize = doc.getFrame('LaterSL', orientation="Landscape")

    canv.setPageSize(pagesize)
    canv.setFont(base_fonts()["normal"], doc.fontSize)

    doc.centerM = (frame._width -
                   (frame._leftPadding + frame._rightPadding)) / 2
    doc.leftM = frame._leftPadding
    doc.rightM = frame._width - frame._rightPadding
    doc.headM = (frame._height - frame._topPadding) + doc.topM
    doc.bottomM = frame._bottomPadding - doc.topM

    addPlugin(canv, doc, frame="Later")

    canv.restoreState()

class PageInfo(object):
    """
    a Class to handle header and footer elements, that raster into a frame::

        l    c    r

    :param typ: header/footer
    :param pos: 'l'/'c'/'r'
    :param text: text of header or footer element
    :param image: image preferrably as pdf Image
    :param addPageNumber: True/False

    As of now we consider either text or image, and will not handle these cases separately.

    """

    def __init__(self, typ, pos, text, image, line, frame, addPageNumber,
                 rightMargin=None, shift=None):
        self.typ = typ
        self.pos = pos
        self.text = text
        self.image = image
        self.line = line
        self.frame = frame
        self.addPageNumber = addPageNumber
        if rightMargin is not None:
            setattr(self, "rightMargin", rightMargin)
        if shift is not None:
            setattr(self, "shift", shift)


class AutoDocTemplate(BaseDocTemplate):
    """
    This is our Document Template, here we want to add our special formatting, that we need for our Document Creation

    We derive from BaseDocTemplate, we don't want to and cannot superclass here...

    We have one unique way inside afterFlowable to create one outline entry for each flowable by:

    - adding the <a name=outlineName> to text within the paragraph flowable.
    - using self.notify(), self.canv.bookmarkPage() and self.canv.addOutlineEntry() inside a function afterFlowable() which is overloaded in an own Template class that inherits from BaseDocTemplate

    For a basic example, please see in TOC with clickable links by rptlab.
    we implemented a special action flowable class called Bookmark, that has no actions! please see modifications in afterFlowable().
    Unlike with paragraphs we are also abled to store many outline entries from one Table.
    This is the best way to do this for multible bookmarks in one table flowable without having to write too much overhead code.

    We discovered this workaround that was postet in ReportLab-users Group back in 2004 by Marc Stober. This workaround suggests using a class Bookmark.
    We have ported this to use an ActionFlowable, to do the bookmarking, because this flowable is not doing anything at all, but storing some values, so that afterFlowable() can see them.

    To define Template settings for your pages you can use three stages, override the default values::

        onFirstPage=_doNothing
        onLaterPages=_doNothing
        onLaterSPages=_doNothing

    The stages are:

    - `onFirstPage` template for the first page
    - `onLaterPages` template of any following page
    - `onLaterSPages` template on any later switchable special page

    To define a scheme, where all pages are Portrait but special pages are landscape pages::

        onFirstPage=drawFirstPage
        onLaterPages=drawLaterPage
        onLaterSPages=drawLaterLPage

    To define a scheme, where all pages are Portrait/Landscape and there are no special pages::

        onFirstPage=drawFirstPage/drawFirstLPage
        onLaterPages=drawLaterPage/drawLaterLPage
        onLaterSPages=_doNothing

    """

    def __init__(self,
                 filename,
                 onFirstPage=(_doNothing, 0),
                 onLaterPages=(_doNothing, 0),
                 onLaterSPages=(_doNothing, 0),
                 templates = [],
                 leftMargin=2.5 * cm,
                 rightMargin=2.5 * cm,
                 topMargin=2.5 * cm,
                 bottomMargin=2.5 * cm,
                 title=None,
                 author=None,
                 subject=None,
                 producer=None,
                 creator=None,
                 keywords=[],
                 debug=False):

        if producer is not None:
            PDFInfo.producer = producer

        super(AutoDocTemplate, self).__init__(filename,
            pagesize=A4,
            leftMargin=leftMargin,
            rightMargin=rightMargin,
            topMargin=topMargin,
            bottomMargin=bottomMargin,
            title=title,
            author=author,
            subject=subject,
            producer=producer,
            creator=creator,
            keywords=keywords)

        self.debug = debug
        if self.debug:
            self.showBoundary = 1
        else:
            self.showBoundary = 0

        #Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='F1')

        """
        Here we populate our page templates
        Page templates are separated into three stages:

        - on first page
        - on later page
        - on later special page

        """

        # can be Landscape or Portrait
        self.onFirstPage, self.framesFirst = onFirstPage
        # Later Portrait or Landscape
        self.onLaterPages, self.framesLater = onLaterPages
        # Later Landscape to change the Format from Landscape to Portrait or vice versa
        self.onLaterSPages, self.framesLaterS = onLaterSPages

        self.bottomTableHeight = 0

        self.figCount = 0
        self.PageDecorated = False

        self.pageInfos = OrderedDict()

        self.lineWidth = 0.15
        self.fontSize = 9
        self.topM = self.fontSize * 1.2

        self.templates_maker()

        if self.debug:
            print("PDF Inhalte werden erzeugt...")
            print("on First Page: ", (onFirstPage))
            print("on Later Pages: ", (onLaterPages))
            print("on Later Special Pages: ", (onLaterSPages))


    def templates_maker(self):
        """
        register page templates and functions

        returns a list, that simplified looks like this::

            [PageTemplate(id='First',
                          frames=frameT,
                          onPage=onFirstPage,
                          pagesize=self.pagesize),
             PageTemplate(id='Later',
                          frames=frameT,
                          onPage=onLaterPages,
                          pagesize=self.pagesize)])

        """
        function_name = attrgetter("__name__")

        templates = []
        ### on first page
        frame_count = self.framesFirst
        tId="FirstP"
        pagesizeL=False
        if self.onFirstPage is not _doNothing:
            firstTemplateName = function_name(self.onFirstPage)
            if firstTemplateName.startswith("drawFirst"):
                if firstTemplateName.endswith("Portrait"):
                    tId="FirstP"
                    pagesizeL=False
                elif firstTemplateName.endswith("Landscape"):
                    pagesizeL=True
                    tId="FirstL"

        templates.append(self.getMultiColumnTemplate(frameCount=frame_count,
                                                tId=tId,
                                                onPager=self.onFirstPage,
                                                pagesizeL=pagesizeL))
        ### on later page
        frame_count = self.framesLater
        tId="LaterP"
        pagesizeL=False

        if self.onLaterPages is not _doNothing:
            laterTemplateName = function_name(self.onLaterPages)
            if laterTemplateName.startswith("drawLater"):
                if laterTemplateName.endswith("Portrait"):
                    tId="LaterP"
                    pagesizeL=False
                elif laterTemplateName.endswith("Landscape"):
                    pagesizeL=True
                    tId="LaterL"

        templates.append(self.getMultiColumnTemplate(frameCount=frame_count,
                                                tId=tId,
                                                onPager=self.onLaterPages,
                                                pagesizeL=pagesizeL))
        ### on later special page
        frame_count = self.framesLaterS
        tId="LaterSP"
        pagesizeL=False

        if self.onLaterSPages is not _doNothing:
            laterTemplateName = function_name(self.onLaterSPages)
            if laterTemplateName.startswith("drawLater"):
                if laterTemplateName.endswith("Portrait"):
                    tId="LaterSP"
                    pagesizeL=False
                elif laterTemplateName.endswith("Landscape"):
                    pagesizeL=True
                    tId="LaterSL"

            templates.append(self.getMultiColumnTemplate(frameCount=frame_count,
                                                    tId=tId,
                                                    onPager=self.onLaterSPages,
                                                    pagesizeL=pagesizeL))
        else:
            print("on later special page is not defined", vars(self.onLaterSPages))

        self.addPageTemplates(templates)


    def updatePageInfo(self, pI):
        """
        addPageInfo, using the PageInfo type object

        :param pI: PageInfo() object
        """
        typ = pI.typ

        if pI.line:
            typ += "_"
        if not pI.image is None:
            typ += "___"
        if not pI.text is None:
            typ += "____"
        pI.typ = typ
        self.pageInfos.update({pI.frame + pI.typ + pI.pos: pI})

    def addPageInfo(self,
                    typ="header",
                    pos="l",
                    text=None,
                    image=None,
                    line=False,
                    frame="First",
                    addPageNumber=False,
                    rightMargin=None,
                    shift=None):
        """
        add header and footer elements, that raster into the frame::

                l            c            r

            +---------------------------------+
            | l  header                     r |
            | e +------------+------------+ i |
            | f |                         | g |
            | t |                         | h |
            |   |                         | t |
            | p |                         |   |
            | a |                         | p |
            | d |                         | a |
            |   |                         | d |
            |   +------------+------------+   |
            |    footer                       |
            +---------------------------------+

        :param frame: "First"/"Later"
        :param typ: header/footer
        :param pos: "l"/"c"/"r"
        :param text: ""
        :param image: preferrably a PDF Image
        :param addPageNumber: True/False
        :param rightMargin: shift of 'r' ancor towards centre (only for line).
        :param shift: shifts the image in (x,y) direction (only for image).
        :param line: True/False if true, draw a line from 'l' to 'r'

        creates a PageInfo object:
            PageInfo(typ,pos,text,image,line,frame,addPageNumber,rightMargin,shift)

        As of now we consider either text or image and optionaly a line
        and will not handle these cases separately.
        """
        self.updatePageInfo(
            PageInfo(typ, pos, text, image, line, frame, addPageNumber,
                     rightMargin, shift))

    def createFrame(self, orientation="Portrait",
                    horizontal_lower=0.,
                    vertical_lower=0.,
                    width=0.,
                    height=0.,
                    left_padding=0.,
                    bottom_padding=0.,
                    right_padding=0.,
                    top_padding=0.,
                    overlap=None):
        """
        Frame reportlab internal signature::

                        width                    x2,y2
                +---------------------------------+
                | l  top_padding                r | h
                | e +-------------------------+ i | e
                | f |                         | g | i
                | t |                         | h | g
                |   |                         | t | h
                | p |                         |   | t
                | a |                         | p |
                | d |                         | a |
                |   |                         | d |
                |   +-------------------------+   |
                |    bottom padding               |
                +---------------------------------+
                (x1,y1) <-- lower left corner

        """
        return Frame(horizontal_lower,
                     vertical_lower,
                     width,
                     height,
                     leftPadding=left_padding,
                     bottomPadding=bottom_padding,
                     rightPadding=right_padding,
                     topPadding=top_padding,
                     id=orientation,
                     showBoundary=self.showBoundary,
                     overlapAttachedSpace=overlap,
                     _debug=None)

    def getFrame(self, temp_name, orientation="Portrait", last=False):
        """
        returns frame
        frame._x1,frame._y1
        frame._width,frame._height
        frame._leftPadding,frame._bottomPadding
        frame._rightPadding,frame._topPadding
        and pagesize:
        (x,y)
        """

        f = attrgetter("id")
        frame = None

        if last:
            for temp in self.pageTemplates[::-1]:
                if f(temp).startswith(temp_name):
                    pageTemplate = temp
                    break

        else:
            for temp in self.pageTemplates:
                if f(temp).startswith(temp_name):
                    pageTemplate = temp
                    break

        for frame in pageTemplate.frames:
            print(f(frame))
            if f(frame).startswith(orientation):
                return frame, (frame._getAvailableWidth(), frame._height)

        if frame is None:
            print("Error occured accessing self.pageTemplates", temp_name)
            raise Exception
            #            #print ( thisTemplate.frames[0].id )
            #            return thisTemplate.frames[0],thisTemplate.pagesize
            #
            #        else:


    def getLastTemplate(self, temp_name="Later"):
        """
        Return last page template that is a 'Later' template
        """
        f = attrgetter("id")

        for temp in self.pageTemplates[::-1]:
            if f(temp).startswith(temp_name):
                return f(temp)

    def getFirstTemplate(self, temp_name="Later"):
        """
        Return first page template with an id that starts with frame_name
        """
        f = attrgetter("id")

        for temp in self.pageTemplates:
            if f(temp).startswith(temp_name):
                return f(temp)

    def getSpecialTemplate(self, temp_name="Later"):
        """
        get the next page action flowable template that starts with temp_name
        """
        return NextPageTemplate(self.getLastTemplate(temp_name=temp_name))

    def getMultiColumnTemplate(self,
                               frameCount=2,
                               tId="LaterL",
                               onPager=_doNothing,
                               pagesizeL=True,
                               fId="Portrait"):
        """
        create a TwoColumn Frame

        This is customized for landscape format pages.
        if you want portrait, set pagesizeL to False

        Frame vals::

            x1,
            y1,
            width,
            height,
            leftPadding=6,
            bottomPadding=6,
            rightPadding=6,
            topPadding=6,
            id=None,
            showBoundary=0,
            overlapAttachedSpace=None,
            _debug=None

        Template Style for Two Frames::

                    width          (x2,y2)
            +-----------------------------+-----------------------------+
            | l  top padding            r | h                           |
            | e +---------------------+ i | e +---------------------+   |
            | f |                     | g | i |                     |   |
            | t |                     | h | g |                     |   |
            |   |                     | t | h |     Second          |   |
            | p |                     |   | t |     frame           |   |
            | a |                     | p |   |                     |   |
            | d |                     | a |   |                     |   |
            |   |                     | d |   |                     |   |
            |   +---------------------+   |   +---------------------+   |
            |    bottom padding           |                             |
            +-----------------------------+-----------------------------+
            (x1,y1) <-- lower left corner

        """
        #self._calc()
        if pagesizeL:
            width, height = landscape(self.pagesize)
            fF = "Landscape"
        else:
            width, height = self.pagesize
            fF = "Portrait"

        fullWidth = width - (self.leftMargin + self.rightMargin)

        print(f">>>> {frameCount} {fF} fullWidth: {fullWidth} width={width} left={self.leftMargin} right={self.rightMargin}")

        if frameCount > 0:
            frameWidth = fullWidth / float(frameCount)

        frameHeight = height - (self.bottomMargin + self.topMargin)
        frames = []
        #construct a frame for each column
        for frame in range(frameCount):
            leftMargin = self.leftMargin + frame * frameWidth
            print(">>>>>>>>", leftMargin, frameWidth)
            frames.append(self.createFrame(orientation=fId,
                                      horizontal_lower=leftMargin,
                                      vertical_lower=self.bottomMargin,
                                      width=frameWidth,
                                      height=frameHeight,
                                      left_padding=0.,
                                      bottom_padding=0.,
                                      right_padding=0.,
                                      top_padding=0.,
                                      overlap=None))

        frames.append(self.createFrame(orientation=fF,
                                  horizontal_lower=0.,
                                  vertical_lower=0.,
                                  width=width,
                                  height=height,
                                  left_padding=0.,
                                  bottom_padding=0.,
                                  right_padding=0.,
                                  top_padding=0.,
                                  overlap=None))
        return PageTemplate(id=tId,
                            frames=frames,
                            onPage=onPager,
                            pagesize=(width, height))

    def handle_pageBegin(self):
        """
        override base method to add a change of page template after the firstpage.
        """
        self._handle_pageBegin()
        template = self.getFirstTemplate(temp_name="Later")
        self._handle_nextPageTemplate(template)

    def scaleImage(self, thisImage, scaleFactor=None):
        """
        Function to allow user scaling of factor.
        A scaling greater than 0, lesser than 1 is
        allowed. By default a scaling of 0.7071 is
        applied to thisImage
        """
        if scaleFactor is None:
            setattr(thisImage, "_userScaleFactor", 0.7071)
            #thisImage._userScaleFactor=(1./np.sqrt(2))
        else:
            #if scaleFactor<=1.:
            #   thisImage._userScaleFactor=scaleFactor
            setattr(thisImage, "_userScaleFactor", scaleFactor)

        return thisImage

    def _scaleApply(self, Img, scaling):
        """
        scales width and height of an Image
        """
        Img.drawWidth = Img.drawWidth * scaling
        Img.drawHeight = Img.drawHeight * scaling

        return Img

    def handle_flowable(self, flowables):
        """
        overriding base method!!!

        try to handle one flowable from the front of list flowables.

        added a dirty workaround to scale images
        if their boundingBox exceeds the borders of the frame.
        """

        #allow document a chance to look at, modify or ignore
        #the object(s) about to be processed
        self.filterFlowables(flowables)
        self.handle_breakBefore(flowables)
        self.handle_keepWithNext(flowables)
        f = flowables[0]
        del flowables[0]
        if f is None:
            return
        if isinstance(f, PageBreak):
            npt = f.nextTemplate
            if npt and not self._samePT(npt):
                npt = NextPageTemplate(npt)
                npt.apply(self)
                self.afterFlowable(npt)
            if isinstance(f, SlowPageBreak):
                self.handle_pageBreak(slow=1)
            else:
                #print( f.__class__.__name__, self.frame.id )
                self.handle_pageBreak()
            self.afterFlowable(f)
        elif isinstance(f, ActionFlowable):
            f.apply(self)
            self.afterFlowable(f)
        else:
            frame = self.frame
            canv = self.canv
            if self.debug:
                frame.drawBoundary(canv)
            #handle scaling to fit a PdfImage on self.frame
            if isinstance(f, Table):
                pass  # controls default behaviour for Table typed flowables
                #f.setStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)])
            elif isinstance(f, Spacer):
                pass
                """
                elif isinstance(f,Spacer):
                    pass
                elif isinstance(f,Flowable):
                    if self.debug:
                        f._showBoundary()
                        print(#f.getSpaceBefore(),
                            frame._aH,"<--")
                            #frame._y1p)
                """
            if isinstance(f, ap.PdfImage):
                #print("height of image:",f.drawHeight)
                #print("height of frame:",frame._aH)
                xfactor = getattr(f, "_userScaleFactor", None)
                factor = 1.

                if not xfactor is None:
                    #print( "applying scale", xfactor)
                    factor = xfactor
                    f = self._scaleApply(f, factor)
                    setattr(f, "_userScaleFactor", None)

                #resizing image if drawWidth is exceeding the available frame Width _aW
                if f.drawWidth > frame._aW:
                    factor = frame._aW / f.drawWidth
                    f = self._scaleApply(f, factor)
                    if self.debug:
                        print("PdfImage exceeds available width on frame:",
                              frame.id, frame._aW / cm, frame._aH / cm,
                              f.drawWidth / cm, f.drawHeight / cm,
                              "rescaling to fit frame geometry.")

                #resizing image if drawHeight is exceeding the available frame Width _aH
                if f.drawHeight > frame._aH:

                    #print("PdfImage height exceeds height of available space on frame:",
                    #      frame.id,
                    #      "rescaling to fit frame geometry..." )

                    factor = frame._aH / f.drawHeight
                    f = self._scaleApply(f, factor)
                #print("spaceBelow:",frame._aH-f.drawHeight )
                #print("spaceBesides:",frame._aW-f.drawWidth )
                #print(f.drawHeight)

                #try to fit it then draw it
            if frame.add(f, canv, trySplit=self.allowSplitting):
                if not isinstance(f, FrameActionFlowable):
                    self._curPageFlowableCount += 1
                    self.afterFlowable(f)
                _addGeneratedContent(flowables, frame)
            else:
                if self.allowSplitting:
                    # see if this is a splittable thing
                    S = frame.split(f, canv)
                    n = len(S)
                else:
                    n = 0
                if n:
                    if not isinstance(S[0], (PageBreak, SlowPageBreak,
                                             ActionFlowable, DDIndenter)):
                        if not frame.add(S[0], canv, trySplit=0):
                            ident = "Splitting error(n==%d) on page %d in\n%s\nS[0]=%s" % \
                            (n,
                             self.page,
                             self._fIdent(f, 60, frame),
                             self._fIdent(S[0], 60, frame))
                            #leave to keep apart from the raise
                            raise LayoutError(ident)
                        self._curPageFlowableCount += 1
                        self.afterFlowable(S[0])
                        flowables[0:0] = S[
                            1:]  # put rest of splitted flowables back on the list
                        _addGeneratedContent(flowables, frame)
                    else:
                        flowables[
                            0:0] = S  # put splitted flowables back on the list
                else:
                    if hasattr(f, '_postponed'):
                        #print( f.__class__.__name__, self.frame.id, f.drawWidth, f.drawHeight, )

                        ident = "Flowable %s%s too large on page %d in frame %r%s of template %r" % \
                        (self._fIdent(f, 60, frame),
                         _fSizeString(f),
                         self.page,
                         self.frame.id,
                         self.frame._aSpaceString(),
                         self.pageTemplate.id)
                        #leave to keep apart from the raise
                        raise LayoutError(ident)
                    # this ought to be cleared when they are finally drawn!
                    f._postponed = 1
                    mbe = getattr(self, '_multiBuildEdits', None)
                    if mbe:
                        mbe((delattr, f, '_postponed'))
                    # put the flowable back
                    flowables.insert(0, f)
                    self.handle_frameEnd()


    # def build(self, flowables):
    #     """
    #     build the document using the flowables.  Annotate the first page using the onFirstPage
    #     function and later pages using the onLaterPages function.  The onXXX pages should follow
    #     the signature::
    #         def myOnFirstPage(canvas, document):
    #             # do annotations and modify the document
    #             ...
    #     The functions can do things like draw logos, page numbers,
    #     footers, etcetera. They can use external variables to vary
    #     the look (for example providing page numbering or section names).
    #     """
    #     self._calc()  #in case we changed margins sizes etc
    #     AutoDocTemplate.build(self, flowables)
    #     self.PageDecorated = True

    def afterFlowable(self, flowable):
        """
        Registers TOC entries.
        and outline entries

        Entries to the table of contents can be done either manually by
        calling the addEntry method on the TableOfContents object or automatically
        by sending a 'TOCEntry' notification in the afterFlowable method of
        the DocTemplate you are using. The data to be passed to notify is a list
        of three or four items containing a level number, the entry text, the page
        number and an optional destination key which the entry should point to.
        This list will usually be created in a document template's method like
        afterFlowable(), making notification calls using the notify() method
        with appropriate data.
        """

        cln = None
        try:
            cln = flowable.cln()

        except:
            pass

        if cln == "Header":
            pass

        if cln == "Footer":
            pass

        if cln == "Bookmark":
            #print("Bookmark",flowable.title,"created at level:",flowable.level)

            #This seems to be not necessary
            entity_info = flowable.level, flowable.title, self.page, flowable.key
            self.notify('TOCEntry', entity_info)

            self.currSpaceToBottom = self.frame._y + self.frame._y1p  # <-- not necessary

            self.canv.bookmarkPage(
                flowable.key, fit='XYZ', top=self.currSpaceToBottom)
            ##            if flowable.fullpage:
            ##                flowable.key='Diagramm'+flowable.key
            #self.canv.bookmarkPage(flowable.key, fit='FitH', top=800)
            #self.canv.bookmarkPage(flowable.key, fit='XYZ')

            # print(self.getFrame()[1][1])

            self.canv.addOutlineEntry(
                flowable.title,
                flowable.key,
                level=flowable.level,
                closed=True)
            self.canv.showOutline()

    def figcounter(self):
        """
        a simple figure counter, this is a very dirty way
        to control the number of figures
        """
        self.figCount += 1
        return str(self.figCount)


class BottomSpacer(Spacer):
    """
    a spacer that fills the current doc unto the bottom
    """
    def wrap(self, availWidth, availHeight):
        height = availHeight - self._doc.bottomTableHeight

        if height <= 0:
            return (self.width, availHeight)
        else:
            return (self.width, height)


# A Class to control the behaviour of the styles object
_stylesheet1_undefined = object()


class StyleSheet:
    """
    This may or may not be used.  The idea is to:

    1. slightly simplify construction of stylesheets;

    2. enforce rules to validate styles when added
       (e.g. we may choose to disallow having both
       'heading1' and 'Heading1' - actual rules are
       open to discussion);

    3. allow aliases and alternate style lookup
       mechanisms

    4. Have a place to hang style-manipulation
       methods (save, load, maybe support a GUI
       editor)

    Access is via getitem, so they can be
    compatible with plain old dictionaries.
    """

    def __init__(self):
        self.byName = {}
        self.byAlias = {}

    def __getitem__(self, key):
        try:
            return self.byAlias[key]
        except KeyError:
            try:
                return self.byName[key]
            except KeyError:
                raise KeyError("Style '%s' not found in stylesheet" % key)

    def get(self, key, default=_stylesheet1_undefined):
        try:
            return self[key]
        except KeyError:
            if default != _stylesheet1_undefined: return default
            raise

    def __contains__(self, key):
        return key in self.byAlias or key in self.byName

    def has_key(self, key):
        return key in self

    def add(self, style, alias=None):
        key = style.name
        if key in self.byName and key in self.byAlias:
            raise KeyError("Style key '%s' already defined in stylesheet" %
                           key)

        if alias:
            if alias in self.byName:
                raise KeyError("Style '%s' already defined in stylesheet" %
                               alias)
            if alias in self.byAlias:
                raise KeyError(
                    "Alias name '%s' is already an alias in stylesheet" %
                    alias)

            style.alias = alias
        #passed all tests?  OK, add it
        self.byName[key] = style
        if alias:
            self.byAlias[alias] = style

    def list(self):
        styles = list(self.byName.items())
        styles.sort()
        alii = {}
        for (alias, style) in list(self.byAlias.items()):
            alii[style] = alias
        for (name, style) in styles:
            alias = alii.get(style, None)
            print(name, alias)


# Define Styles
class Styles(object):
    """
    default styles definition

    provides a function to easily register more styles
    """
    def __init__(self):

        self.stylesheet = StyleSheet()

        self.addStyle(
            ParagraphStyle(
                name='Normal',
                fontName=base_fonts()["normal"],
                fontSize=10,
                bulletFontName=base_fonts()["normal"],
                leading=12))
        self.addStyle(
            ParagraphStyle(
                name='BodyText',
                parent=self.stylesheet['Normal'],
                spaceBefore=6),
            alias='normal')

        self.addStyle(
            ParagraphStyle(
                name='Table', parent=self.stylesheet['Normal'], spaceBefore=0),
            alias='table')

        self.addStyle(
            ParagraphStyle(
                name='Italic',
                parent=self.stylesheet['BodyText'],
                fontName=base_fonts()["italic"]),
            alias='italic')

        self.addStyle(
            ParagraphStyle(
                name='Bold',
                parent=self.stylesheet['BodyText'],
                fontName=base_fonts()["bold"]),
            alias='bold')

        self.addStyle(
            ParagraphStyle(
                name='Centered',
                parent=self.stylesheet['BodyText'],
                alignment=TA_CENTER),
            alias='centered')

        self.addStyle(
            ParagraphStyle(
                name='Right',
                parent=self.stylesheet['BodyText'],
                alignment=TA_RIGHT,
                wordWrap=False),
            alias='right')

        self.addStyle(
            ParagraphStyle(
                name='Title',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=18,
                leading=22,
                alignment=TA_CENTER,
                spaceAfter=6),
            alias='title')

        self.addStyle(
            ParagraphStyle(
                name='Heading1',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=18,
                leading=22,
                spaceAfter=6),
            alias='h1')

        self.addStyle(
            ParagraphStyle(
                name='Heading2',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=14,
                leading=18,
                spaceBefore=12,
                spaceAfter=6),
            alias='h2')

        self.addStyle(
            ParagraphStyle(
                name='Heading3',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=12,
                leading=14,
                spaceBefore=12,
                spaceAfter=6),
            alias='h3')

        self.addStyle(
            ParagraphStyle(
                name='Heading4',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=10,
                leading=12,
                spaceBefore=10,
                spaceAfter=4),
            alias='h4')

        self.addStyle(
            ParagraphStyle(
                name='Heading5',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=9,
                leading=10.8,
                spaceBefore=8,
                spaceAfter=4),
            alias='h5')

        self.addStyle(
            ParagraphStyle(
                name='Heading6',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                fontSize=7,
                leading=8.4,
                spaceBefore=6,
                spaceAfter=2),
            alias='h6')

        self.addStyle(
            ParagraphStyle(
                name='Heading6',
                parent=self.stylesheet['Normal'],
                fontName=base_fonts()["bold"],
                alignment=TA_CENTER,
                fontSize=12,
                leading=8.4,
                spaceBefore=14,
                spaceAfter=2),
            alias='caption')

        self.addStyle(
            ParagraphStyle(
                name='Bullet',
                parent=self.stylesheet['Normal'],
                firstLineIndent=0,
                spaceBefore=3),
            alias='bu')

        self.addStyle(
            ParagraphStyle(
                name='Definition',
                parent=self.stylesheet['Normal'],
                firstLineIndent=0,
                leftIndent=36,
                bulletIndent=0,
                spaceBefore=6,
                bulletFontName=base_fonts()["bold_italic"]),
            alias='df')

        self.addStyle(
            ParagraphStyle(
                name='Code',
                parent=self.stylesheet['Normal'],
                fontName='Courier',
                alignment=TA_LEFT,
                fontSize=8,
                leading=8.8,
                firstLineIndent=0,
                leftIndent=36),
            alias='code')

        self.addStyle(
            ParagraphStyle(
                name='ConsoleText',
                parent=self.stylesheet['Normal'],
                fontName='Courier',
                alignment=TA_LEFT,
                fontSize=11,
                leading=14,  #16
                firstLineIndent=0,
                leftIndent=0,
                spaceBefore=2,
                spaceAfter=0),
            alias='console')

        self.addStyle(
            ParagraphStyle(
                name='Warning',
                parent=self.stylesheet['Normal'],
                fontName='Courier',
                alignment=TA_LEFT,
                fontSize=11,
                textColor='red',
                leading=14,  #16
                firstLineIndent=0,
                leftIndent=10,
                spaceBefore=0,
                spaceAfter=0),
            alias='warning')
        # Fixed Notation
        self.p2 = ParagraphStyle(
            name='Heading2',  # must be according to TOC depth
            parent=self.stylesheet['Normal'],
            fontSize=10,
            leading=12)

        self.p3 = ParagraphStyle(
            name='Heading3',  # must be according to TOC depth
            parent=self.stylesheet['Normal'],
            fontSize=10,
            leading=12)

    def addStyle(self, PS, alias=None):
        """
        add a ParagraphStyle to stylesheet
        """
        self.stylesheet.add(PS, alias=alias)

    def registerStyles(self):
        """
        register all stylesheets by their respective aliases
        """
        for style_name in self.stylesheet.byAlias:
            setattr(self, style_name, self.stylesheet[style_name])

    def listAttrs(self, style, indent=''):
        """
        print all registered styles
        """
        print(indent + 'name = ' + str(style.name))
        print(indent + 'parent = ' + str(style.parent))
        keylist = sorted(list(vars(style).keys()))
        keylist.remove('name')
        keylist.remove('parent')
        for key in keylist:
            value = vars(style).get(key, None)
            print(indent + '%s = %s' % (key, value))

    def listStyles(self):
        """
        return list of styles in object
        """
        keylist = sorted(list(vars(self)))
        keylist.remove('stylesheet')

        return keylist

    def StyleInfoByAlias(self, alias):
        """
        prints all attributes of a style matching the alias
        """
        style = self.__getattribute__(alias)
        try:
            print("test", style.name)
            self.listAttrs(style, indent="   ")
        except AttributeError:
            pass


#styles = Styles()
#styles.registerStyles()


def doTabelOfContents():
    """
    returns toc with 3 customized headings level styles
    """
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            fontSize=12,
            name='TOCHeading1',
            leftIndent=4,
            firstLineIndent=0,
            spaceBefore=0,
            leading=13),
        ParagraphStyle(
            fontSize=10,
            name='TOCHeading2',
            leftIndent=8,
            firstLineIndent=0,
            spaceBefore=0,
            leading=11),
        ParagraphStyle(
            fontSize=9,
            name='TOCHeading3',
            leftIndent=12,
            firstLineIndent=0,
            spaceBefore=0,
            leading=10),
        ]
    return toc

class Header(NullActionFlowable):
    _ids = count(0)

    @classmethod
    def cln(cls):
        return cls.__name__

class Footer(NullActionFlowable):
    _ids = count(0)

    @classmethod
    def cln(cls):
        return cls.__name__

class Bookmark(NullActionFlowable):
    """
    Utility class to display PDF bookmark.

    :param title: Title of the bookmark
    :param level: Level entry in the outline

    """
    _ids = count(0)

    @classmethod
    def cln(cls):
        return cls.__name__

    def __init__(self, title, level=0):
        NullActionFlowable.__init__(self)

        self.title = title
        self.level = level

        if is_python3:
            self.id = self._ids.__next__()
        else:
            self.id = self._ids.next()
        self.key = self.createBookmarkKey()

    def createBookmarkKey(self):
        """
        creates a Bookmark Key using title, level and the identity of this ActionFlowable
        """
        key = self.title
        key += str(self.level)
        key += str(self.id)

        key = key.encode(encoding="utf-8")

        return sha1(key).hexdigest()


def getBookmarkLast(contents):
    """
    return last bookmark in contents or None
    """
    for f in contents[::-1]:
        if isinstance(f, Bookmark):
            return f


def getBaseFont(fonttype):
    if fonttype in base_fonts():
        return base_fonts()[fonttype]
    else:
        return None


def doHeading(title, sty, outlineText=None, bookmarkFullpage=False):
    """
    function that makes a Flowable for a heading
    :param title: title of the paragraph
    :param sty: style for the paragraph
    :param outlineText: with specifying an "ancortext" we can control the output to the bookmark name in the outline of the PDF
    """

    if outlineText is None:
        outlineText = title

    style = sty.name
    if style == 'Heading1':
        level = 0
    elif style == 'Heading2':
        level = 1
    elif style == 'Heading3':
        level = 2
    else:
        level = 0

    bm = Bookmark(outlineText, level)

    #create bookmarkname
    key = bm.key
    an = '<a name="%s"/>' % key
    if bookmarkFullpage:
        h = Paragraph(title, sty)
    else:
        h = Paragraph(an + title, sty)

# heading must stay with next paragraph or table
##    h.keepWithNext = True
    return (bm, h)


def addHeading(title, sty, page):
    """
    demux function that adds bookmark and heading to page list
    """
    for flowable in doHeading(title, sty):
        page.append(flowable)


def doImage(Img, doc, titlename, sty):
    """
    Here we simplify the process of inserting an Image to the pdf story

    :param doc: an instance of autobasedoc

    #TODO make it more general, the doc.width is not reliable
    """
    if not Img is None:

        factor = doc.width / Img.drawWidth
        Img.drawHeight = Img.drawHeight * factor
        Img.drawWidth = Img.drawWidth * factor
        para = Paragraph(
            u"Fig. " + doc.figcounter() + u" " + titlename + u" Vertikal",
            sty.caption)

        return (Img, para)
    else:
        return ""


def PageNext(contents, nextTemplate):
    """
    switch to Landscape on next page
    """
    if isinstance(contents[-1], PageBreak):
        contents.insert(-1, nextTemplate)
    else:
        contents.append(nextTemplate)
        contents.append(PageBreak())
    return contents


###############################################################################

if __name__ == "__main__":

    print("this is a module")
    #print Paragraph styles added to the styles.stylesheet
    #print(styles.stylesheet.list() )

    #print(color_dict)
