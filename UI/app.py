import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore
import DB
import re
import main as parser

class mainScreen(QWidget):
    #
    # Calling the super to initialize the window
    #
    dic={}
    def __init__(self, parent=None):
        super(mainScreen, self).__init__()
        self.initMainWindow()
        self.dbobject = DB.DATABASE()
        self.parserclass= parser.ClassParser()
        self.directory = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','code-files'))


    def initMainWindow(self):
        # Window sepc
        self.resize(1000, 600)
        self.setFixedSize(self.size())
        self.setWindowTitle("Auto Compelete Code")
        # Centering the screen

        # Connect CSS File
        self.styleSheet = ''
        cssFile = open('style.css', 'r')
        self.styleSheet = cssFile.read()
        cssFile.close()
        self.setStyleSheet(self.styleSheet)

        # initialize main widget
        mainLayout = QGridLayout()

        # Creating main widget
        self.setLayout(mainLayout)
        self.initTextEditor(mainLayout)
        self.initsuggestionList()
        self.show()

    def initTextEditor(self, mainLayout):
        self.codeEditor = QPlainTextEdit()
        mainLayout.addWidget(self.codeEditor, 0, 0)
        self.codeEditor.resize(self.codeEditor.document().size().width(),
                               self.codeEditor.document().size().height() + 10)
        self.font = QFont()
        self.font.setFamily('OperatorMono-Light')
        self.font.setFixedPitch(True)
        self.font.setPointSize(12)
        self.codeEditor.setFont(self.font)
        self.codeEditor.setTabStopWidth(20)
        self.codeEditor.keyReleaseEvent = self.keyReleaseEvent
        self.cursor = self.codeEditor.textCursor()

    #Show the list when Control is entered
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.showList()
            importedModules = self.dbobject.getAll_modules()
            if importedModules:
                for x in importedModules:
                 self.parserclass.parse(self.directory + os.sep + x + ".py")
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.parse(self.selectPreviousLine())
        else:
            self.suggestionList.hide()

    def initsuggestionList(self):
        self.suggestionList = QListWidget(self)
        self.suggestionList.resize(200, 200)
        self.suggestionList.hide()
        self.suggestionList.itemClicked.connect(self.itemSelect)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setOffset(0)
        self.shadow.setColor(QColor(0, 0, 0))
        self.suggestionList.setGraphicsEffect(self.shadow)

    # suggestionListList Functions`
    def showList(self):  # Show AutoComleteList
        rect = self.codeEditor.cursorRect()
        self.clearWidget(self.suggestionList)
        arr = []
        arr = self.get(self.selectCurrentLine())
        if arr :
            self.fillList(arr)
        self.suggestionList.move(rect.x() + 7, rect.y() + 33)
        self.suggestionList.setCurrentRow(0)
        self.suggestionList.show()

    #Clear widget elements
    def clearWidget(self, widget):
        widget.clear()

    def fillList(self,item):
        #Retrieve suggestion from selectCurrentWord()
        for i in item:
            self.suggestionList.addItem(i)
        numOfSuggestions = QLabel("There are " + str(self.suggestionList.count()) + "Suggestions")
        numOfSuggestions.move(50, 40)

    def itemSelect(self, item):
        self.selectCurrentWord()
        x=item.text()
        self.dbobject.incrementCount(x)
        self.cursor.insertText(x)
        self.suggestionList.hide()

    def selectCurrentWord(self):
        self.cursor.select(QTextCursor.WordUnderCursor)
        self.codeEditor.setTextCursor(self.cursor)
        word = self.cursor.selectedText()
        return word
    def selectCurrentLine(self):
        self.cursor.movePosition(QTextCursor.StartOfBlock)
        self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        line = self.cursor.selectedText()
        return line

    def selectPreviousLine(self):
        self.cursor.movePosition(QTextCursor.PreviousBlock)
        self.cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
        line = self.cursor.selectedText()
        return line

    def saveIntoFile(self):
        file_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code-files'))
        with open(file_dir + os.sep + "current-tab.py", 'w') as codeFile:
            codeFile.write(self.codeEditor.toPlainText())

    def get(self,line):
        arr = []
        if re.search(r'import ', line):
            arr = [self.parserclass.getTail(x).replace('.py', '') for x in self.parserclass.findAllPythonFiles(self.directory)]
            if re.search(r'import (.+)', line):
                modules = re.findall(r'import (.+)', line)[0].split(',')
                arr = [x for x in arr if modules[-1] in x]


        elif re.search(r'\.', line):
            importedModules=self.dbobject.getAll_modules()
            MoaduleOrObject=re.findall(r'(:?(:?.+?)\s*=\s*)?(.+?)\.', line)[0][2]

            if MoaduleOrObject in importedModules:
                arr=self.dbobject.getmoduleData(MoaduleOrObject)
                word=self.selectCurrentWord()
                arr = [x for x in arr if word in x]

            elif MoaduleOrObject in self.dic.keys():
                arr=self.dbobject.selectClassData(self.dic[MoaduleOrObject][1])
                word = self.selectCurrentWord()
                arr = [x for x in arr if word in x]
        else:
            word=self.selectCurrentWord()
            importedModules = self.dbobject.getAll_modules()
            arr = [x for x in importedModules if word in x]
        return arr

    def parse(self, item):
        if re.search(r'import (.+)', item):
            for x in re.findall(r'import (.+)', item)[0].replace('\u2029', '').split(','):
                self.parserclass.parse(self.directory + os.sep + x + ".py")

        elif re.search(r'(.+?)\s*\=\s*(.+)\.(.+)', item):
            groups = re.findall(r'\s*(.+?)\s*=\s*(.+)\.(.+)',item)[0]
            classes=self.dbobject.getmoduleClasses(groups[1])
            className = groups[2].replace('\u2029', '')
            if className in classes:
                value=(groups[1],className)
                key=groups[0]
                self.dic[key]=value





def main():
    app = QApplication(sys.argv)
    # Creating object from mainScreen
    main = mainScreen()
    sys.exit((app.exec_(),main.dbobject.truncate()))


if __name__ == "__main__":
    main()