#coding:utf-8
'''
Created on 2015???5???13?

@author: root
'''
from PyQt4.QtCore import QThread, SIGNAL, QByteArray, QTimer, QTime, QString 
from PyQt4.QtNetwork import QUdpSocket, QHostAddress, QAbstractSocket
from PyQt4.QtGui import QMessageBox, QApplication, QCursor 
import sys
import time
import uuid
import datetime
import logging.handlers
import os
import commands 

LOG_PATH = "/opt/morningcloud/massclouds/"

class SavaFile(QThread):
    def __init__(self,parent=None):
        super(SavaFile,self).__init__(parent)
        self.clientuuid = str(uuid.uuid4())
        self.stopFlag = False 
       
    def savaLog(self):
        commandsOutput = commands.getstatusoutput("ping 192.168.0.1 -c 3")
        print commandsOutput
        if commandsOutput[0] == 0:
            if QString(commandsOutput[1]).contains("64 bytes from"):
                pass			
            else:
                os.system("cp -rf /var/log/messages /opt/morningcloud/massclouds/messages")
                self.writeFile()
                self.stopFlag = True
        else:
            print "save file"
            os.system("cp -rf /var/log/messages /opt/morningcloud/massclouds/messages")
            self.writeFile()
            print "save file end"
            self.stopFlag = True


    def writeFile(self):
        commandsOutput = commands.getstatusoutput("dmesg")
        fw = open("/opt/morningcloud/massclouds/dmessage", "w")
        fw.write(commandsOutput[1])
        fw.close()

    def run(self):
        while True:
            self.savaLog()
            time.sleep(1)
            if self.stopFlag:
                break;

if __name__ == "__main__":
    app = QApplication(sys.argv)
    thread = SavaFile()
    thread.start()
    app.exec_()

