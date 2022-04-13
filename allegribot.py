
from telegram.ext import MessageHandler, Filters, CommandHandler, Updater, ConversationHandler
import logging
from enum import Enum
import csv
from match import Match
from mybot import MyBot
from mybot import ConversationState
from datetime import datetime, timedelta, time
from settings import Settings
from instance import Instance
from instance import parseDatasetToMatch
from instance import Gufata
from settings import Status
import urllib.request
from bs4 import BeautifulSoup
import re

datasetPath = "serieA_calendario.csv"
activeInstancesPath = "activeInsts.csv"
bot_username = 'hontemax_bot'
INTERVALSTATE = range(4)
checkNextTurnInterval = 30

def getNextMatch(turn):
    #loading html
    opener = urllib.request.FancyURLopener({})
    url = "https://www.legaseriea.it/it/serie-a/calendario-e-risultati/2021-22/UNICO/UNI/% s" % turn
    f = opener.open(url)
    content = f.read()
    #parsing html
    soup = BeautifulSoup(content, 'html.parser')
    risultati = soup.main.div.section.section
    boxpartitaSoup = risultati.find_all("div", class_="box-partita col-xs-12 col-sm-4 col-md-3")[0]
    datipartitaSoup = boxpartitaSoup.find_all("div", class_="datipartita")[0]
    risultatosxSoup = boxpartitaSoup.find_all("div", class_="col-xs-6 risultatosx")[0]
    risultatodxSoup = boxpartitaSoup.find_all("div", class_="col-xs-6 risultatodx")[0]
    date = datipartitaSoup.span.text.split(' ')[0]
    time = datipartitaSoup.span.text.split(' ')[1]
    stadium = str(datipartitaSoup.text.replace('  ', '').split('\n')[3].split(': ')[1].split('(')[0])
    live = str(datipartitaSoup.text.replace('  ', '').split('\n')[5].split(': ')[1])
    dateTime=datetime(
        year = int(date.split('/')[2]),
        month = int(date.split('/')[1]),
        day = int(date.split('/')[0]),
        hour = int(time.split(':')[0]),
        minute = int(time.split(':')[1]))
    homeTeam = str(risultatosxSoup.h4.text)
    awayTeam = str(risultatodxSoup.h4.text)
    match = Match(dateTime, homeTeam, awayTeam, stadium, live, turn)
    return match

def checkNextTurn(context):
    allegriBot = context.job.context
    actualMatch = allegriBot.actualMatch
    if actualMatch != None and actualMatch.dateTime - datetime.now() < timedelta(hours=0):
        match = getNextMatch(1 + actualMatch.turn)
        allegriBot.actualMatch = match
        with open(datasetPath, 'w') as writeFile:
            writeFile.write(match.toCSVrow())
        for key in allegriBot.instances:
            allegriBot.instances[key].nextMatch = match
            allegriBot.instances[key].settings.setMatchRemindered(False)

class AllegriBot(MyBot):
        
    def __start_bot(self, update, context):
        #add this conversation to active instances
        if self.instances.get(update.effective_chat.id) == None:
            with open(activeInstancesPath, 'w+') as writeFile:
                activeInstances = str(update.effective_chat.id) + '\n'
                for key in self.instances:
                    activeInstances = activeInstances + str(key) + '\n'
                writeFile.write(activeInstances)
                self.instances[update.effective_chat.id] = Instance(self.updater, update.effective_chat.id)
            
    def __stop_bot(self, update, context):
        #remove this conversation from active instances
        if self.instances.get(update.effective_chat.id) != None:
            self.instances[update.effective_chat.id].reset()
            del self.instances[update.effective_chat.id]
            with open(activeInstancesPath, 'w+') as writeFile:
                activeInstances = ''
                for key in self.instances:
                    if not update.effective_chat.id == key:
                        activeInstances = activeInstances + str(key)+ '\n'
                writeFile.write(activeInstances)
                
    def __start(self, update, context):
        self.__start_bot(update, context)
        self.__printHelp(update, context)
        
    def __stop(self, update, context):
        #if execution comes here, the bot has been blocked or unblocked
        if self.instances.get(update.effective_chat.id) != None: #The bot was not already blocked
            self.__stop_bot(update, context)
        
    def __start_group(self, update, context):
        for member in update.message.new_chat_members:
            if member.username == bot_username:
                self.__start_bot(update, context)
                context.bot.send_message(chat_id=update.effective_chat.id, text = "Ve ne intendete di ippica?")
                break
            
    def __stop_group(self, update, context):
        for member in update.message.left_chat_members:
            if member.username == bot_username:
                self.__stop_bot(update, context)
                break
            
    def __start_reminder(self, update, context):
        instance = self.instances[update.effective_chat.id]
        if instance.settings.getReminderStatus() == Status.STOPPED:
            instance.settings.setReminderStatus(Status.STARTED)
            instance.settings.setMatchRemindered(False)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Boia dè non shordatevi la formazione")
            instance.startFormationReminder()
            
    def __stop_reminder(self, update, context):
        instance = self.instances[update.effective_chat.id]
        if instance.settings.getReminderStatus() == Status.STARTED:
            instance.settings.setReminderStatus(Status.STOPPED)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Eh mò me ne vò")
            instance.stopFormationReminder()
                
    def __echo_bot(self, update, context):
        instance = self.instances[update.effective_chat.id]
        receivedText = update.message.text.lower()
        isGufata = (("perso" in receivedText
            or "vinci" in receivedText
            or "vinto" in receivedText
            or "vinco" in receivedText
            or "perdo" in receivedText
            or "perdi" in receivedText
            or "perderò" in receivedText
            or "vincerò" in receivedText
            or "perderà" in receivedText
            or "vincerà" in receivedText
            or "perderai" in receivedText
            or "vincerai" in receivedText
            or "complimenti" in receivedText
            or "congratulazioni" in receivedText
            or "vince" in receivedText
            or "perde" in receivedText)
            and not ("vincere" in receivedText
            or "perdere" in receivedText))
        if not instance.settings.getMute():
            if isGufata:
                update.message.reply_text('Gran gufata')
                self.__updateGufateRanking(context, update)
            if "belotti" in receivedText:
                update.message.reply_text('Un ottimo portiere in effetti')
            if "rabiot" in receivedText:
                update.message.reply_text('Il mio Cavallo Pazzo')
            if "horto muso" in receivedText or 'corto muso' in receivedText:
                update.message.reply_text('Approvo')
            if "ronaldo" in receivedText:
                update.message.reply_text('Il miglior mediano che abbia mai avuto')
            if "morata" in receivedText:
                update.message.reply_text('Il mio miglior terzino')
            if ("bel gioco" in receivedText
            or "gioco pessimo" in receivedText
            or "brutto gioco" in receivedText
            or "gioco di merda" in receivedText
            or "calcio champaigne" in receivedText):
                update.message.reply_text('Il bel gioco serve solo ai teorici')
        else:
            if isGufata:
                self.__updateGufateRanking(context, update)
            
    def __updateGufateRanking(self, context, update):
        instance = self.instances[update.effective_chat.id]
        newGufateRows = []
        newGufate = []
        path = 'gufate/gufate' + str(update.effective_chat.id) + '.csv'
        actualGufate = instance.gufate
        username = update.message.from_user['username']
        if username != None:
            found = False
            for gufata in actualGufate:
                if gufata.nome == username:
                    found = True
                    gufata.gufate = gufata.gufate + 1
                newGufateRows.append(gufata.toCSVrow())
                newGufate.append(gufata)
            if not found:
                newGufata = Gufata(username, 1)    
                newGufateRows.append(newGufata.toCSVrow())
                newGufate.append(newGufata)
            instance.gufate = newGufate
            with open(path, 'w+') as writeFile:
                for row in newGufateRows:
                    writeFile.write(row + '\n')
            
    def __printGufateRanking(self, update, context):
        instance = self.instances[update.effective_chat.id]
        gufate = instance.gufate
        gufateStr = 'Conteggio attuale delle gufate \n'
        for gufata in gufate:
            gufateStr = gufateStr + '\n'
            gufateStr = gufateStr + gufata.nome + ': ' + str(gufata.gufate)
        context.bot.send_message(
                chat_id=update.effective_chat.id, text=gufateStr)
        
    def __printHelp(self, update, context):
        text = "Sono qui per rihordare di mettere la formazione al fantahalcio prima che inizino le partite. In più faccio caciara \n\n"
        text = text + "Lista dei comandi: \n"
        text = text + "\n/start: attiva il bot in questa conversazione"
        text = text + "\n/reminderon: attiva le notifiche per l'inserimento delle formazioni"
        text = text + "\n/reminderoff: disattiva le notifiche per l'inserimento delle formazioni"
        text = text + "\n/mute: disattiva le risposte automatiche del bot"
        text = text + "\n/unmute: attiva le risposte automatiche del bot"
        text = text + "\n/setinterval: seleziona con quante ore di preavviso vuoi che il bot notifichi di inserire le formazioni"
        text = text + "\n/help: visualizza questa guida"
        #text = text + "\n/gufate: mostra la classifica delle gufate (solo per gli utenti con username impostato)"
        context.bot.send_message(
                chat_id=update.effective_chat.id, text=text)
        
    def __mute(self, update, context):
        instance = self.instances[update.effective_chat.id]
        if instance.settings.getMute() == False:
            context.bot.send_message(
                    chat_id=update.effective_chat.id, text="Tutti teorici")
            instance.settings.setMute(True)
        
    def __unmute(self, update, context):
        instance = self.instances[update.effective_chat.id]
        if instance.settings.getMute() == True:
            context.bot.send_message(
                    chat_id=update.effective_chat.id, text="Rieccomi")
            instance.settings.setMute(False)
        
    def __startMatchIntervalConv(self, update, context):
        context.bot.send_message(
                chat_id=update.effective_chat.id, text="Dimmi quante ore. Digita /cancel per annullare")
        return INTERVALSTATE
        
    def __stopMatchIntervalConv(self, update, context):
        context.bot.send_message(
                chat_id=update.effective_chat.id, text="Ok ciao")
        return ConversationHandler.END
        
    def __waitForInterval(self, update, context):
        instance = self.instances[update.effective_chat.id]
        instance.settings.setCheckMatchInterval(int(update.message.text))
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Salvato")
        return ConversationHandler.END
        
    def __initializeActiveInstances(self):
        self.instances = {}
        try:
            with open(activeInstancesPath, 'r') as readFile:
                reader = csv.reader(readFile)
                for row in reader:
                    chatID = int(row[0])
                    self.instances[chatID] = Instance(self.updater, chatID)
        except:
            self.instances = {}

    def __init__(self, token):
        super().__init__(token)
        self.__initializeActiveInstances()
        self.actualMatch = parseDatasetToMatch()
        self.addCommand('start', self.__start)
        self.addCommand('reminderon', self.__start_reminder)
        self.addCommand('reminderoff', self.__stop_reminder)
        self.addCommand('gufate', self.__printGufateRanking)
        self.addCommand('mute', self.__mute)
        self.addCommand('unmute', self.__unmute)
        self.addCommand('help', self.__printHelp)
        self.addEventHandler(self.__start_group)
        self.addEventHandler(self.__stop_group)
        self.addChatMemberHandler(self.__stop)
        self.addOnCommandConversation('setinterval', self.__startMatchIntervalConv,
                                      [ConversationState(INTERVALSTATE, self.__waitForInterval, Filters.regex('^[1-9]+[0-9]*$'))],
                                      'cancel', self.__stopMatchIntervalConv)
        self.addEcho(self.__echo_bot)
        self.updater.job_queue.run_repeating(checkNextTurn, interval=checkNextTurnInterval, context = self)
