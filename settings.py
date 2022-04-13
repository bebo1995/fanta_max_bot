import csv
from enum import Enum

class Status(Enum):
    STARTED = 1,
    STOPPED = 2  

class Settings:
    def __init__(self, mute, checkMatchInterval, reminderStatus, chatID, matchRemindered):
        self.__mute = mute
        self.__checkMatchInterval = checkMatchInterval
        self.__reminderStatus = reminderStatus
        self.__matchRemindered = matchRemindered
        self.chatID = chatID
        self.save(self.chatID)
    
    #add set-add to group event- active sessions
    def toCSVrow(self):
        m = 1
        if self.__mute == False:
            m = 0
        started = 1
        if self.__reminderStatus == Status.STOPPED:
            started = 0
        remindered = 1
        if self.__matchRemindered == False:
            remindered = 0
        return str(m) + "," + str(self.__checkMatchInterval) + ',' + str(started) + ',' + str(remindered)
    
    def save(self, userID):
        with open("sets/settings" + str(userID) + ".csv", 'w+') as writeFile:
                writeFile.write(self.toCSVrow())
                
    def getMute(self):
        return self.__mute
        
    def getCheckMatchInterval(self):
        return self.__checkMatchInterval
        
    def getReminderStatus(self):
        return self.__reminderStatus

    def getMatchRemindered(self):
        return self.__matchRemindered
        
    def setMute(self, value):
        self.__mute = value
        self.save(self.chatID)
        
    def setCheckMatchInterval(self, value):
        self.__checkMatchInterval = value
        self.save(self.chatID)
        
    def setReminderStatus(self, value):
        self.__reminderStatus = value
        self.save(self.chatID)

    def setMatchRemindered(self, value):
        self.__matchRemindered = value
        self.save(self.chatID)
        
    @staticmethod
    def fromCSVrow(row, chatID):
        mute = True
        remindered = True
        started = Status.STARTED
        if int(row[0]) == 0:
            mute = False
        if int(row[2]) == 0:
            started = Status.STOPPED
        if int(row[3]) == 0:
            remindered = False
        return Settings(mute, int(row[1]), started, chatID, remindered)