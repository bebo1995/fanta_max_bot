from settings import Settings
import csv
from datetime import datetime, timedelta, time
from match import Match
from settings import Status
import os

datasetPath = "serieA_calendario.csv"
settingsPath = "sets/settings"
gufatePath = "gufate/gufate"
formatPath = ".csv"
formationReminderInterval = 30

def removeTurnFromData(turn):
    lines = list()
    with open(datasetPath, 'r') as readFile:
        reader = csv.reader(readFile)
        for row in reader:
            dataTurn = row[0]
            if dataTurn != turn:
                lines.append(row)
    with open(datasetPath, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(lines)

def parseDatasetToMatch():
    with open(datasetPath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            return Match.fromCSVrow(row)
    
def checkNotifies(context):
    instance = context.job.context
    match = instance.nextMatch
    remindered = instance.settings.getMatchRemindered()
    if match != None and match.dateTime - datetime.now() < timedelta(hours=instance.settings.getCheckMatchInterval()) and remindered == False:
        #instance.nextMatch = None
        instance.settings.setMatchRemindered(True)
        matchTime = time(hour=match.dateTime.hour,
            minute=match.dateTime.minute).strftime("%H:%M")
        homeTeam = match.homeTeam
        awayTeam = match.awayTeam
        stadium = match.stadium
        live = match.live
        bonus = ""
        if live == "DAZN" or live == "DAZN/SKY":
            bonus = "con Diletta Leotta"
        if homeTeam == 'Juventus':
            instance.updater.bot.send_message(chat_id=instance.chatID, text = f"Mettete la formazione huttana maiala che alle {matchTime} "
                                + f"giochiamo noi hontro l* {awayTeam} al {stadium} in diretta su {live} {bonus}")
        else:
            if awayTeam == 'Juventus':
                instance.updater.bot.send_message(chat_id=instance.chatID, text = f"Mettete la formazione huttana maiala che alle {matchTime} "
                                    + f"gioha l* {homeTeam} hontro di noi al {stadium} in diretta su {live} {bonus}")
            else:
                instance.updater.bot.send_message(chat_id=instance.chatID, text = f"Mettete la formazione huttana maiala che alle {matchTime} "
                                    + f"giohano quei bischeri di {homeTeam} - {awayTeam} al {stadium} in diretta su {live} {bonus}")

class Gufata:
    def __init__(self, nome, gufate):
        self.nome = nome
        self.gufate = gufate
        
    def toCSVrow(self):
        return self.nome + "," + str(self.gufate)
        
    @staticmethod
    def fromCSVrow(row):
        return Gufata(str(row[0]), int(row[1]))

class Instance:
    updater = None
    chatID = None
    nextMatch = None
    formationReminder = None
    settings = None
    gufate = None

    def __init__(self, updater, chatID):
        formationNotificationStatus = Status.STOPPED
        self.updater = updater
        self.chatID = chatID
        self.nextMatch = parseDatasetToMatch()
        settingspath = settingsPath + str(chatID) + formatPath
        gufatepath = gufatePath + str(chatID) + formatPath
        try:
            with open(settingspath, 'r') as readFile:
                reader = csv.reader(readFile)
                for row in reader:
                    self.settings = Settings.fromCSVrow(row, self.chatID)
        except:
            self.settings = Settings(False, 3, formationNotificationStatus, self.chatID, False)
        if self.settings.getReminderStatus() == Status.STARTED:
            self.startFormationReminder()
        self.gufate = []
        try:
            with open(gufatepath, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    for row in csv_reader:
                        self.gufate.append(Gufata.fromCSVrow(row))
        except:
            self.gufate = []
            
    def reset(self):
        settingspath = settingsPath + str(self.chatID) + formatPath
        gufatepath = gufatePath + str(self.chatID) + formatPath
        try:
            os.remove(settingspath)
        except:
            print("no settings for this user")
        try:
            os.remove(gufatepath)
        except:
            print("no gufate for this user")
        self = None
                        
    def startFormationReminder(self):
        self.formationReminder = self.updater.job_queue.run_repeating(checkNotifies, interval=formationReminderInterval, context = self)
        
    def stopFormationReminder(self):
        self.formationReminder.schedule_removal()
