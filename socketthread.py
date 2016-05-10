#coding:utf-8
'''
Created on 2015年5月13日

@author: root
'''
from PyQt4.QtCore import QThread, SIGNAL, QByteArray, QTimer, QTime, QString, QMutex
#from PyQt4.QtNetwork import QUdpSocket, QHostAddress, QAbstractSocket
from PyQt4.QtGui import QMessageBox, QApplication, QCursor
import sys, gc
import time
import uuid
import datetime
import logging.handlers
import os, socket, threading
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
        
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) 
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)
        self.udpSocket.bind(("224.0.0.17",self.port))
        self.udpSocket.setblocking(0)
        #self.udpSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        
        self.udpSocketTwo = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) 
        self.udpSocketTwo.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.udpSocketTwo.bind(("224.0.0.18",self.porttwo))
        self.udpSocket.setblocking(0)
        #self.udpSocketTwo.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

        if not os.path.exists(os.path.dirname(LOG_PATH)):
            os.makedirs(os.path.dirname(LOG_PATH))
        handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes = 1024*1024, backupCount = 5) # ?????????handler
        fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
		       
        formatter = logging.Formatter(fmt)   # ?????????formatte
        handler.setFormatter(formatter)      # ???handler??????format

        self.logger = logging.getLogger(LOG_PATH)    # ????????tst???logger 
        self.logger.addHandler(handler)           # ???logger??????handle
        self.logger.setLevel(logging.DEBUG)

        #self.mutex = QMutex()

        gc.set_debug(gc.DEBUG_STATS|gc.DEBUG_LEAK)

        self.setTimer = QTimer()
        self.connect(self.setTimer, SIGNAL("timeout()"), self.setSocketOpt)
        self.setTimer.start(100)

        self.data_ready = threading.Event()
        self.pContrlCMD = threading.Thread(target=self.dataReceiveTwo)
        self.pContrlCMD.start()
        #self.pSortFrame = threading.Thread(target=self.sortFrame, args=(self.data_ready,))
        #self.pSortFrame.start()

    def bindUdpPort(self):
        if not self.joinGroupTwo: 
            self.joinGroupTwo = self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
            self.logger.info("joinGroupTwo:%d" % self.joinGroupTwo) 
        else:
            self.timer.stop()

    def setSocketOpt(self):
        try:
            self.udpSocket.setsockopt(socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton("224.0.0.17") + socket.inet_aton("0.0.0.0"));

            self.udpSocketTwo.setsockopt(socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton("224.0.0.18") + socket.inet_aton("0.0.0.0"));

            self.setTimer.stop()
        except socket.error, e:
            #self.logger.error(e.message)
            pass

    def dataReceive(self):
        try:
            #startTime = datetime.datetime.now()
            msglist,add = self.udpSocket.recvfrom(32*1024+21)
            #endTime = datetime.datetime.now()
            #print (endTime-startTime).microseconds
            msg = msglist
            timetemp = msg[0:17]
            datanumth = msg[17:19]
            datatotalnum = msg[19:21]
            datacontent = msg[21:]

            self.addToLocal(timetemp,datanumth,datatotalnum,datacontent)

        except socket.error, e:
            pass
            #f = open("/opt/morningcloud/massclouds/record.txt", 'a')
            #traceback.print_exc(file=f)
            #f.flush()
            #f.close()
            #self.logger.error(e.message)

        #time.sleep(0.01)

    def addToLocal(self,timetemp,datanumth,datatotalnum,datacontent):
        try:
            if len(self.framedata) > 60:
                self.framedata.clear()
                return
            if self.framedata.has_key(timetemp):
                self.framedata[timetemp][datanumth] = datacontent
                if len(self.framedata[timetemp]) == int(datatotalnum):
                    self.dataframelist[timetemp] = self.framedata[timetemp]
                    self.framedata.pop(timetemp)
                
            else:
               self.framedata[timetemp] = {}
               self.framedata[timetemp][datanumth] = datacontent
        except Exception, e:
            f = open("/opt/morningcloud/massclouds/record.txt", 'a')
            traceback.print_exc(file=f)
            f.flush()
            f.close()
            self.logger.error("addToLocal") 
            self.logger.error(e.message) 
            
    def sortAddLocalList(self):
        if len(self.dataframelist) > 8:
            self.dataframelist.clear()
            return

        try:
            if len(self.dataframelist) > 0:
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
    
                #del keylist 
                #del imgdata
            else:
                self.currentframe = None

        except Exception, e:
            f = open("/opt/morningcloud/massclouds/record.txt", 'a')
            traceback.print_exc(file=f)
            f.flush()
            f.close()
            self.logger.error(e.message) 

    def dataReceiveTwo(self):
        while True:
            try:
                msglist, addr = self.udpSocketTwo.recvfrom(64)

                self.parseMsg(msglist)

            except socket.error, e:
                pass
            time.sleep(0.01)
            

    def slotStartAllBroadcast(self,msgs):
        #result = self.udpSocket.joinMulticastGroup(self.mcast_addr)
        #self.logger.info("joinGroup:%d" % result) 
        self.emit(SIGNAL("startbroadcast"))
        self.broadFlag = True
        #self.start()
        self.pSortFrame = threading.Thread(target=self.sortFrame, args=(self.data_ready,))
        self.pSortFrame.start()

    
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
            print "----------startbroadcast"
            self.logger.info("startbroadcast") 
            self.slotStartAllBroadcast(msg)
            self.data_ready.set()
                
        elif msg.split("#")[0] == "stopbroadcast":
            print "stopbroadcast"
            self.logger.info("stopbroadcast") 
            #result = self.udpSocket.leaveMulticastGroup(self.mcast_addr)
                    
            #self.logger.info("leaveGroup:%d" % result) 
            self.emit(SIGNAL("stopbroadcast"))
            self.broadFlag = False
                
            self.framedata.clear()
            self.dataframelist.clear()
            self.currentframe = None

    def sortFrame(self, event):
        while not event.is_set():
            event.wait(0.01)

        while self.broadFlag:
            self.dataReceive()
            self.sortAddLocalList()

            if self.currentframe == None:
                #time.sleep(0.01)
                continue
            
            #msg = self.currentframe
            self.emit(SIGNAL("imgsignal"), self.currentframe)
            #self.msginfo = msg
            #time.sleep(0.01)
            #del self.currentframe
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    thread = SocketThread()
    app.exec_()


