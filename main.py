#coding:utf-8
'''
Created on 2015年5月13日

@author: root
'''
from PyQt4.QtCore import QThread, SIGNAL, QByteArray, QTimer, QTime, QString, QMutex
from PyQt4.QtNetwork import QUdpSocket, QHostAddress, QAbstractSocket
from PyQt4.QtGui import QMessageBox, QApplication, QCursor
import sys, gc
import time
import uuid
import datetime
import logging.handlers
import os

LOG_PATH = "/opt/morningcloud/massclouds/record.log"

class SocketThread(QThread):
    def __init__(self,parent=None):
        super(SocketThread,self).__init__(parent)
        self.clientuuid = str(uuid.uuid4())
        self.port = 5555
        self.broadFlag = False 
        self.currentStudent = False
        self.porttwo = 5556
        
        self.framedata = {}
        self.currentframe = ""
        
        self.dataframelist = {}
        
        self.udpSocket = QUdpSocket(self)
        self.udpSocket.setReadBufferSize(1024*1024)
        
        self.connect(self.udpSocket,SIGNAL("readyRead()"),self.dataReceive)
        self.results = self.udpSocket.bind(self.port)
        self.mcast_addr = QHostAddress("224.0.0.17")
        
        self.mcast_addr_two = QHostAddress("224.0.0.18")
        self.udpSocketTwo = QUdpSocket(self)
        self.udpSocketTwo.setReadBufferSize(1024)
        self.connect(self.udpSocketTwo,SIGNAL("readyRead()"),self.dataReceiveTwo)
        self.result = self.udpSocketTwo.bind(self.porttwo)
        if self.result:
            self.joinGroupTwo = self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
            print("joinmulticastGroup %d" % self.joinGroupTwo)
            
       
        if not os.path.exists(os.path.dirname(LOG_PATH)):
            os.makedirs(os.path.dirname(LOG_PATH))
        handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes = 1024*1024, backupCount = 5) # ?????????handler
        fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
		       
        formatter = logging.Formatter(fmt)   # ?????????formatte
        handler.setFormatter(formatter)      # ???handler??????format

        self.logger = logging.getLogger(LOG_PATH)    # ????????tst???logger 
        self.logger.addHandler(handler)           # ???logger??????handle
        self.logger.setLevel(logging.DEBUG)

        self.timer = QTimer()
        self.connect(self.timer, SIGNAL("timeout()"), self.bindUdpPort)
        self.timer.start(1000)

        self.mutex = QMutex()

        gc.set_debug(gc.DEBUG_STATS|gc.DEBUG_LEAK)

    def bindUdpPort(self):
        if not self.joinGroupTwo: 
            self.joinGroupTwo = self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
            self.logger.info("joinGroupTwo:%d" % self.joinGroupTwo) 
        else:
            self.timer.stop()

    def dataReceive(self):
        while self.udpSocket.hasPendingDatagrams():
            try:
                if self.broadFlag == False:
                    continue

                datagram = QByteArray()
                datagram.resize(self.udpSocket.pendingDatagramSize())

                msglist = self.udpSocket.readDatagram(datagram.size())
                msg = msglist[0]
                if len(msg) <= 21:
                    print "msg data smaller" 
                    continue
                timetemp = msg[0:17]
                datanumth = msg[17:19]
                datatotalnum = msg[19:21]
                datacontent = msg[21:]

                self.addToLocal(timetemp,datanumth,datatotalnum,datacontent)

                #del msg 
                #del datacontent 
            except Exception, e:
                #del datacontent 
                self.logger.error(e.message) 

    def addToLocal(self,timetemp,datanumth,datatotalnum,datacontent):
        try:
            if len(self.framedata) > 80:
                self.framedata.clear()
                return
            self.mutex.lock()
            if self.framedata.has_key(timetemp):
                self.framedata[timetemp][datanumth] = datacontent
                if len(self.framedata[timetemp]) == int(datatotalnum):
                    #self.dataframelist[timetemp] = self.framedata[timetemp]
                    self.framedata.pop(timetemp)
                
            else:
               self.framedata[timetemp] = {}
               self.framedata[timetemp][datanumth] = datacontent
            self.mutex.unlock()
        except Exception, e:
            self.mutex.unlock()
            self.logger.error("addToLocal") 
            self.logger.error(e.message) 
            
    def sortAddLocalList(self):
        self.mutex.lock()
        if len(self.dataframelist) > 30:
            self.dataframelist.clear()
            #return
        #if len(self.framedata) > 100:
        #    self.framedata.clear()
            #return
        self.mutex.unlock()

        if len(self.dataframelist) > 2:
            keylist = []
            for key in self.dataframelist:
                keylist.append(int(key))
            keylist.sort()
            imgdata = ""
            for i in range(0,len(self.dataframelist[("%017d"%(keylist[0]))])):
                keys = "%02d"%i
                imgdata = imgdata + self.dataframelist[("%017d"%(keylist[0]))][keys]
        
            self.currentframe = imgdata
            self.dataframelist.pop(("%017d"%(keylist[0])))

            del keylist 
            del imgdata
        else:
            self.currentframe = None
            
    def dataReceiveTwo(self):
        while self.udpSocketTwo.hasPendingDatagrams():
            datagram = QByteArray()
            datagram.resize(self.udpSocketTwo.pendingDatagramSize())

            msglist = self.udpSocketTwo.readDatagram(datagram.size())
            msg = str(msglist[0])

        self.parseMsg(msg)
        

    def slotStartAllBroadcast(self,msgs):
        self.udpSocket.joinMulticastGroup(self.mcast_addr)
        self.emit(SIGNAL("startbroadcast"))
        self.broadFlag = True
        #self.start()

    
    def slotStopBroadcast(self):
        self.udpSocket.leaveMulticastGroup(self.mcast_addr)
        self.emit(SIGNAL("stopbroadcast"))
        self.broadFlag = False
        self.currentStudent = False
        self.framedata.clear()
        self.dataframelist.clear()
        self.currentframe = None


    def parseMsg(self,msg):
            if msg.split("#")[0] == "startbroadcast":
                print "startbroadcast"
                self.logger.info("startbroadcast") 
                self.slotStartAllBroadcast(msg)
                
            elif msg.split("#")[0] == "stopbroadcast":
                print "stopbroadcast"
                self.logger.info("stopbroadcast") 
                self.udpSocket.leaveMulticastGroup(self.mcast_addr)
                    
                self.emit(SIGNAL("stopbroadcast"))
                self.broadFlag = False
                
                self.framedata.clear()
                self.dataframelist.clear()
                self.currentframe = None

    def run(self):
        while self.broadFlag:
            self.sortAddLocalList()

            if self.currentframe == None:
                time.sleep(0.01)
                continue
            
            #msg = self.currentframe
            self.emit(SIGNAL("imgsignal"), self.currentframe)
            #self.msginfo = msg
            time.sleep(0.01)
            del self.currentframe
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    thread = SocketThread()
    app.exec_()


