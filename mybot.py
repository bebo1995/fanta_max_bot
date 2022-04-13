from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ChatMemberHandler, ConversationHandler
import logging

class ConversationState():
    def __init__(self, name, function, filters):
        self.name = name
        self.function = function
        self.filters = filters

class MyBot:

    def addCommand(self, command, function):
        command_handler = CommandHandler(command, function)
        self.dispatcher.add_handler(command_handler)
        
    def addEcho(self, function):
        echo_handler = MessageHandler(Filters.text & (~Filters.command), function)
        self.dispatcher.add_handler(echo_handler)
        
    def addEventHandler(self, function):
        handler = MessageHandler(Filters.status_update, function)
        self.dispatcher.add_handler(handler)
        
    def addChatMemberHandler(self, function):
        handler = ChatMemberHandler(function)
        self.dispatcher.add_handler(handler)
        
    def addOnCommandConversation(self, command, entryCommandFunction, states, stopCommand, stopCommandFunction):
        startConversationHandler = CommandHandler(command, entryCommandFunction)
        stopConversationHandler = CommandHandler(stopCommand, stopCommandFunction)
        stateHandlers = {}
        for state in states:
            stateHandlers[state.name] = [MessageHandler(state.filters, state.function)]
        handler = ConversationHandler(entry_points = [startConversationHandler], states = stateHandlers, fallbacks = [stopConversationHandler])
        self.dispatcher.add_handler(handler)
    
    def addErrorHandler(self, function):
        self.dispatcher.add_error_handler(function)
        
    def run(self):
        self.updater.start_polling()
        self.updater.idle()

    def __init__(self, token):
        self.updater = Updater(
            token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
