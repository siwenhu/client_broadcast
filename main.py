# -*- coding: utf-8 -*-
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
from PyQt4.QtNetwork import *
#from socketthreadtwo import SocketThread
from socketthread import SocketThread
import time

QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))

class UdpClient(QWidget):
    def __init__(self,parent=None):
        super(UdpClient,self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Dialog)
        
        self.pale = QPalette(Qt.black)
        #self.setAutoFillBackground(True)
        self.setPalette(self.pale)
        
        self.broadflag = False
        
        
        self.setFixedSize(QSize(QApplication.desktop().width(),QApplication.desktop().height()))
        #self.setAttribute(Qt.WA_TranslucentBackground,True)
        
        self.showlabel = 0
        
        self.socketThread = SocketThread()
        self.connect(self.socketThread, SIGNAL("imgsignal"),self.paintLabel)
        #self.connect(self.socketThread, SIGNAL("receiveteacherip"),self.slotGetTeacherIp)
        self.connect(self.socketThread, SIGNAL("startbroadcast"),self.slotStartBroadcast)
        self.connect(self.socketThread, SIGNAL("stopbroadcast"),self.slotStopBroadcast)
        #self.connect(self.socketThread, SIGNAL("mousepos"),self.slotSetMousePos)
        self.imgstr = "000000"
        self.framplat = "jpg"
        self.imgLabel = QLabel(self)
        self.imgLabel.setFixedSize(QSize(QApplication.desktop().width(),QApplication.desktop().height()))
        
        self.imgLabelTwo = QLabel(self)
        #self.imgLabelTwo.setFixedSize(QSize(QApplication.desktop().width(),QApplication.desktop().height()))
        #self.imgLabelTwo.lower()
        
        #self.mouseLabel = QLabel(self)
        #self.mouseLabel.setFixedSize(QSize(30,30))
        #self.mousepix = QPixmap("images/mousetwo.ico").scaled(30,30)
        #self.mouseLabel.setPixmap(self.mousepix)
        #self.mouseLabel.raise_()
        
#         self.scene = QGraphicsScene()
#         view = QGraphicsView(self.scene,self)
#         view.setFixedSize(QSize(1440,900))
#         
        #self.imgLabel.hide()

    def bindUdpPort(self):
        self.socketThread.bindUdpPort()
        
    def slotStartBroadcast(self):
        self.broadflag = True
        self.emit(SIGNAL("start"))
        
        
    def slotStopBroadcast(self):
        self.broadflag = False
        self.emit(SIGNAL("stop"))
        #self.pale.setColor(QPalette.Background,QColor(Qt.black))
        self.imgLabelTwo.clear()
        #self.imgLabelTwo.setAutoFillBackground(True)
        #self.imgLabelTwo.setPalette(self.pale)
        
    def paintLabel(self,imgstr):
#         pixmap = QPixmap()
#         pixmap.loadFromData(imgstr, self.framplat)
#         self.scene.addPixmap(pixmap)
#         return
        if self.broadflag:
        
            #if self.showlabel == 0:
            #self.showlabel = 1
            pixmap = QPixmap()
            pixmap.loadFromData(imgstr, self.framplat)
            
            
            self.imgLabelTwo.resize(pixmap.size())
            self.imgLabelTwo.move(QPoint((self.width() - self.imgLabelTwo.width())/2,(self.height() - self.imgLabelTwo.height())/2))
            self.imgLabelTwo.setAlignment(Qt.AlignCenter)
            self.imgLabelTwo.setPixmap(pixmap)
            #self.imgLabel.lower()
                
    #         else:
    #             #image0=QImage.fromData(imgstr,self.framplat)
    #             #pixmap = QPixmap(image0).scaled(1366,768)
    #             self.showlabel = 0
    #             pixmap = QPixmap()
    #             pixmap.loadFromData(imgstr, self.framplat)
    #             self.imgLabel.setAlignment(Qt.AlignCenter)
    #             self.imgLabel.setPixmap(pixmap)
    #             self.imgLabelTwo.lower()
    #             
            
            
    #def slotSetMousePos(self,x,y):
        
    #    self.mouseLabel.move(self.imgLabelTwo.pos() + QPoint(x,y))
        
        
    def slotGetTeacherIp(self,teacherip):
        pass
        
    def slotButton(self):
        self.close()
        
        
class MainWindow(QWidget):
    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        self.setWindowTitle(u"UDP Client")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(QSize(300,300))
        self.udpClient = UdpClient()
        self.connect(self.udpClient, SIGNAL("start"),self.startB)
        self.connect(self.udpClient, SIGNAL("stop"),self.stopB)
        
        #self.startB()
        
    def startB(self):
        self.udpClient.show()
        self.udpClient.setFixedSize(QSize(QApplication.desktop().width(),QApplication.desktop().height()))
        self.udpClient.imgLabel.setFixedSize(QSize(QApplication.desktop().width(),QApplication.desktop().height()))
        
    def stopB(self):
        self.udpClient.close()
        
if __name__ == "__main__":
    app=QApplication(sys.argv)
    dialog=MainWindow()
    dialog.show()
    app.exec_()
