#coding:utf-8
'''
Created on 2015年5月13日

@author: root
'''
from PyQt4.QtCore import QThread, SIGNAL, QByteArray, QTimer, QTime, QString
from PyQt4.QtNetwork import QUdpSocket, QHostAddress, QAbstractSocket
from PyQt4.QtGui import QMessageBox, QApplication, QCursor
#from logrecord import LogRecord
#from broadclient.waitingteacher import WaitingTeacher
import sys
import time
import uuid
import datetime

class SocketThread(QThread):
    def __init__(self,parent=None):
        super(SocketThread,self).__init__(parent)
        self.clientuuid = str(uuid.uuid4())
        self.list = []
        self.timetemp = ""
        self.msginfo = QByteArray()
        self.port = 5555
        self.broadFlag = False 
        self.currentStudent = False
        self.porttwo = 5556
        
        self.datagramcount = 40
        
        self.localframenum = 0
        self.avilableframenum = 0
        self.necnum = 0
        
        self.framedata = {}
        self.framelist = {}
        self.framedatalist = []
        self.currentframe = ""
        
        self.dataframelist = {}
        
        #self.mouseTimer = QTimer()
        #self.connect(self.mouseTimer, SIGNAL("timeout()"),self.broadTheMousePos)

        #self.teacherIp = ""

        #self.waitingTimer = QTimer()
        #self.waitingTimer.start(10000)
        #self.connect(self.waitingTimer, SIGNAL("timeout()"),self.slotStopBroadcastTimeout)
 
        #self.waitingTeacher = WaitingTeacher()
        #self.connect(self.waitingTeacher, SIGNAL("receive_data"),self.operateTeacherMsg)
        
        self.udpSocket = QUdpSocket(self)
        #self.udpSocket.setReadBufferSize(1024*1024*2)
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
            self.joinGroup = self.udpSocketTwo.joinMulticastGroup(self.mcast_addr)
            self.joinGroupTwo = self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
            print("joinmulticastGroup %d" % self.joinGroup)
            
        self.mcast_addr_own = QHostAddress("224.0.0.19")
        self.bindUdpPort()
        
    def bindUdpPort(self):
        if not self.results:
            self.results = self.udpSocket.bind(self.port)
            self.udpSocket.joinMulticastGroup(self.mcast_addr)
        if not self.result:
            self.result = self.udpSocketTwo.bind(self.porttwo)   
            self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
        if not self.joinGroup: 
            self.udpSocket.joinMulticastGroup(self.mcast_addr)
        if not self.joinGroupTwo:
            self.udpSocketTwo.joinMulticastGroup(self.mcast_addr_two)
            
    def dataReceive(self):
        while self.udpSocket.hasPendingDatagrams():
            #starttime = datetime.datetime.now().microsecond
            datagram = QByteArray()
            datagram.resize(self.udpSocket.pendingDatagramSize())

            msglist = self.udpSocket.readDatagram(datagram.size())
            if self.broadFlag == False:
                continue
            msg = msglist[0]
            timetemp = msg[0:17]
            datanumth = msg[17:19]
            datatotalnum = msg[19:21]
            datacontent = msg[21:]
            #endtime = datetime.datetime.now().microsecond 
            #print (endtime-starttime) 
            
            self.addToLocal(timetemp,datanumth,datatotalnum,datacontent)
            
    def addToLocal(self,timetemp,datanumth,datatotalnum,datacontent):
        if self.framedata.has_key(timetemp):
            self.framedata[timetemp][datanumth] = datacontent
            if len(self.framedata[timetemp]) == int(datatotalnum):
                self.localframenum+=1
                self.dataframelist[timetemp] = self.framedata[timetemp]
                self.framedata.pop(timetemp)
                
        else:
            self.framedata[timetemp] = {}
            self.framedata[timetemp][datanumth] = datacontent
            
            
    def sortAddLocalList(self):
        if len(self.dataframelist) > 100:
            self.dataframelist.clear()
            return
        if len(self.framedata) > 100:
            self.framedata.clear()
            return

        if len(self.dataframelist) >= 5:
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
        self.emit(SIGNAL("startbroadcast"))
        self.localframenum = 0
        self.avilableframenum = 0
        self.necnum = 0
        self.broadFlag = True
        self.start()

    
    def slotStopBroadcast(self):
        self.udpSocket.leaveMulticastGroup(self.mcast_addr_own)
        self.emit(SIGNAL("stopbroadcast"))
        self.broadFlag = False
        self.currentStudent = False
        self.framedata.clear()
        self.dataframelist.clear()
        self.currentframe = None


    def parseMsg(self,msg):
            if msg.split("#")[0] == "startbroadcast":
                print "startbroadcast"
                self.slotStartAllBroadcast(msg)
                
            elif msg.split("#")[0] == "stopbroadcast":
                self.udpSocket.leaveMulticastGroup(self.mcast_addr_own)
                    
                self.emit(SIGNAL("stopbroadcast"))
                self.broadFlag = False
                
                self.framedata.clear()
                self.dataframelist.clear()
                self.currentframe = None

    def run(self):
        while self.broadFlag:
            #starttime = datetime.datetime.now().microsecond
            self.sortAddLocalList()

            if self.currentframe == None:
                time.sleep(0.01)
                continue
            
            #endtime = datetime.datetime.now().microsecond 
            #print (endtime-starttime) 
            msg = self.currentframe
            self.necnum+=1
            self.avilableframenum+=1
            self.emit(SIGNAL("imgsignal"),msg)
            self.msginfo = msg
                    
            time.sleep(0.01)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    thread = SocketThread()
    app.exec_()


