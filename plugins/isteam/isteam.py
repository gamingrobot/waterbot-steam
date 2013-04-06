import clr
clr.AddReferenceToFile("SteamKit2.dll")
clr.AddReference('System')
import System
from SteamKit2 import *
import sys
from threading import Thread
from bin.shared.perms import Perm
import traceback


class InterfaceSteam:
    def __init__(self, xml):
        self.chatcallbacks = []
        #get steamcfg from main config
        steamcfg = manager.config.getConfig('steamcfg')
        #username
        self.username = manager.config.getValue(steamcfg, 'username')
        #password
        self.password = manager.config.getValue(steamcfg, 'password')
        self.superuser = manager.config.getValue(steamcfg, 'superuser')

        manager.commandmanager.registerCommand("joinchat", self.joinChatCommand, perm=Perm.Super)
        manager.commandmanager.registerCommand("leavechat", self.leaveChatCommand, perm=Perm.Super)

        self.chatrooms = {}

        chatroomscfg = steamcfg.find('chatrooms')
        for chatroom in chatroomscfg.findall("room"):
            roomname = str(chatroom.get("name"))
            roomid = int(chatroom.get("id"))
            self.chatrooms[roomname] = roomid

        print self.chatrooms

        #connect to steam
        self.steamClient = SteamClient()
        callbackManager = CallbackManager(self.steamClient)
        self.steamUser = self.steamClient.GetHandler[SteamUser]()
        self.steamFriends = self.steamClient.GetHandler[SteamFriends]()

        #callbacks
        Callback[SteamClient.ConnectedCallback](self.OnConnected, callbackManager)
        Callback[SteamClient.DisconnectedCallback](self.OnDisconnected, callbackManager)

        Callback[SteamUser.LoggedOnCallback](self.OnLoggedOn, callbackManager)
        Callback[SteamUser.LoggedOffCallback](self.OnLoggedOff, callbackManager)

        Callback[SteamUser.AccountInfoCallback](self.OnAccountInfo, callbackManager)
        Callback[SteamFriends.ChatMsgCallback](self.OnChatMsg, callbackManager)
        Callback[SteamFriends.FriendMsgCallback](self.OnFriendMsg, callbackManager)

        self.steamClient.Connect()

        self._isRunning = True
        #self._callbackthread(callbackManager)

        #start callback thread
        steamthread = Thread(target=self._steamloop, args=[callbackManager])
        #t.daemon = True  # thread dies with the program
        steamthread.start()

        #setup logging
        log.registerLogListener(self.logCallback)

    def joinChatCommand(self, command, args, source):
        if len(args) >= 1:
            chatroom = SteamID(int(args[0]))
            log.info("Connecting to room %s" % chatroom)
            self.steamFriends.JoinChat(chatroom)
            return "Connected to %s" % args[0]

    def leaveChatCommand(self, command, args, source):
        try:
            if len(args) >= 1:
                chatroom = SteamID(int(args[0]))
            else:
                chatroom = SteamID(int(source['ChatRoomID']))
            log.info("Disconnecting from room %s" % chatroom)
            self.steamFriends.LeaveChat(chatroom)
        except:
            return "I'm not currently there"

    def _steamloop(self, callbackManager):
        while self._isRunning:
            callbackManager.RunWaitCallbacks(System.TimeSpan.FromSeconds(1))

    #log happend
    def logCallback(self, logdata):
        self.steamFriends.SendChatMessage(SteamID(str(self.superuser)), EChatEntryType.ChatMsg, logdata)

    #callbacks
    def OnConnected(self, callback):
        if callback.Result != EResult.OK:
            log.error("Unable to connect to steam %s" % callback.Result)

        log.info("Connected to steam, logging in %s" % self.username)

        logondetails = SteamUser.LogOnDetails()
        logondetails.Username = self.username
        logondetails.Password = self.password

        self.steamUser.LogOn(logondetails)

    def OnDisconnected(self, callback):
        log.info("Disconnected from steam")
        self._isRunning = False
        self._destorycallback("isteam")

    def OnLoggedOn(self, callback):
        log.info("Logged into steam as %s" % self.username)
        for chatname in self.chatrooms.keys():
            chatroom = SteamID(self.chatrooms[chatname])
            log.info("Connecting to room %s" % chatroom)
            self.steamFriends.JoinChat(chatroom)

    def OnLoggedOff(self, callback):
        log.info("Logged off from steam")

    def OnAccountInfo(self, callback):
        self.steamFriends.SetPersonaState(EPersonaState.Online)

    def OnChatMsg(self, callback):
        #log.info(callback.ChatterID)
        message = callback.Message
        if str(callback.ChatterID) == self.superuser:
            chatperm = Perm.Super
        else:
            chatperm = Perm.User
        source = {'SourceID': callback.ChatterID, 'SourceRank': chatperm, 'ChatRoomID': callback.ChatRoomID}
        self._processCommand(source, message)

    def OnFriendMsg(self, callback):
        message = callback.Message
        if str(callback.Sender) == self.superuser:
            chatperm = Perm.Super
        else:
            chatperm = Perm.User
        source = {'SourceID': callback.Sender, 'SourceRank': chatperm}
        self._processCommand(source, message)

    def _processCommand(self, source, message):
        log.info(source['SourceID'], message)
        messagesplit = message.strip().split(" ")
        try:
            if messagesplit[0] == "wb":
                response = manager.commandmanager.processCommand(source, messagesplit[1:])
                if isinstance(response, tuple):
                    msgresponse = response[0]
                else:
                    msgresponse = response

                if msgresponse is False or msgresponse is None:
                    self._fireChatCallbacks(source, message)
                else:
                    msgresponse = msgresponse.strip()
                    if msgresponse != "":
                        if 'ChatRoomID' in source.keys():
                            self.sendChatMessage(source['ChatRoomID'], msgresponse)
                        else:
                            self.sendChatMessage(source['SourceID'], msgresponse)
            else:
                self._fireChatCallbacks(source, message)
        except Exception:
            log.error("Error in ISteam Command \n %s" % traceback.format_exc())

    def _fireChatCallbacks(self, source, chatmsg):
        for callback in self.chatcallbacks:
            callback(source, chatmsg)

    def registerChatCallback(self, callback):
        self.chatcallbacks.append(callback)

    def sendChatMessage(self, steamid, msg):
        self.steamFriends.SendChatRoomMessage(steamid, EChatEntryType.ChatMsg, str(msg))

    def destroy(self, callback):
        self.steamUser.LogOff()
        self._destorycallback = callback
        return True
