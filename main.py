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
import traceback

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
        self.joinGroupTwo = False
        
        self.udpSocket = QUdpSocket(self)
        self.udpSocket.setReadBufferSize(1024*1024)
        
        #self.connect(self.udpSocket,SIGNAL("readyRead()"),self.dataReceive)
        self.connect(self.udpSocket,SIGNAL("readyRead()"),self.dataReceiveTest)
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

    def dataReceiveTest(self):
        while self.udpSocket.hasPendingDatagrams():
            try:
                datagram = QByteArray()
                datagram.resize(self.udpSocket.pendingDatagramSize())

                self.udpSocket.readDatagram(datagram.size())

            except Exception, e:
                #del datacontent 
                f = open("/opt/morningcloud/massclouds/record.txt", 'a')
                traceback.print_exc(file=f)
                f.flush()
                f.close()
                self.logger.error(e.message) 

    def dataReceive(self):
        while self.udpSocket.hasPendingDatagrams():
            try:
                datagram = QByteArray()
                datagram.resize(self.udpSocket.pendingDatagramSize())

                msglist = self.udpSocket.readDatagram(datagram.size())
                if self.broadFlag == False:
                    continue
                if len(msglist[0]) <= 21:
                    self.logger.info("msg data smaller") 
                    continue
                msg = msglist[0]
                timetemp = msg[0:17]
                datanumth = msg[17:19]
                datatotalnum = msg[19:21]
                datacontent = msg[21:]

                self.addToLocal(timetemp,datanumth,datatotalnum,datacontent)

                #del msg 
                #del datacontent 
            except Exception, e:
                #del datacontent 
                f = open("/opt/morningcloud/massclouds/record.txt", 'a')
                traceback.print_exc(file=f)
                f.flush()
                f.close()
                self.logger.error(e.message) 

    def addToLocal(self,timetemp,datanumth,datatotalnum,datacontent):
        try:
            if len(self.framedata) > 30:
                if int(datanumth) != int(datatotalnum) - 1:
                    self.framedata.clear()
                    return
            if self.framedata.has_key(timetemp):
                self.framedata[timetemp][datanumth] = datacontent
                if len(self.framedata[timetemp]) == int(datatotalnum):
                    self.mutex.lock()
                    self.dataframelist[timetemp] = self.framedata[timetemp]
                    self.mutex.unlock()
                    self.framedata.pop(timetemp)
                
            else:
               self.framedata[timetemp] = {}
               self.framedata[timetemp][datanumth] = datacontent
        except Exception, e:
            self.mutex.unlock()
            f = open("/opt/morningcloud/massclouds/record.txt", 'a')
            traceback.print_exc(file=f)
            f.flush()
            f.close()
            self.logger.error("addToLocal") 
            self.logger.error(e.message) 
            
    def sortAddLocalList(self):
        if len(self.dataframelist) > 8:
            self.mutex.lock()
            self.dataframelist.clear()
            self.mutex.unlock()

        try:
            if len(self.dataframelist) > 2:
                self.mutex.lock()
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
                self.mutex.unlock()
    
                #del keylist 
                #del imgdata
            else:
                self.currentframe = None

        except Exception, e:
            self.mutex.unlock()
            f = open("/opt/morningcloud/massclouds/record.txt", 'a')
            traceback.print_exc(file=f)
            f.flush()
            f.close()
            self.logger.error(e.message) 
            
    def dataReceiveTwo(self):
        while self.udpSocketTwo.hasPendingDatagrams():
            datagram = QByteArray()
            datagram.resize(self.udpSocketTwo.pendingDatagramSize())

            msglist = self.udpSocketTwo.readDatagram(datagram.size())
            msg = str(msglist[0])

        self.parseMsg(msg)
        

    def slotStartAllBroadcast(self,msgs):
        result = self.udpSocket.joinMulticastGroup(self.mcast_addr)
        self.logger.info("joinGroup:%d" % result) 
        self.emit(SIGNAL("startbroadcast"))
        self.broadFlag = True
        self.start()

    
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
            result = self.udpSocket.leaveMulticastGroup(self.mcast_addr)
                    
            self.logger.info("leaveGroup:%d" % result) 
            self.emit(SIGNAL("stopbroadcast"))
            self.broadFlag = False
                
            self.mutex.lock()
            self.framedata.clear()
            self.dataframelist.clear()
            self.mutex.unlock()
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
            #del self.currentframe
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    thread = SocketThread()
    app.exec_()


