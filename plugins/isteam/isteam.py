import clr
clr.AddReferenceToFile("SteamKit2.dll")
clr.AddReference('System')
import System
from SteamKit2 import *
import sys
from threading import Thread
from bin.shared.perms import Perm


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

        self.steamClient.Connect()

        self._isRunning = True
        #self._callbackthread(callbackManager)

        #start callback thread
        steamthread = Thread(target=self._steamloop, args=[callbackManager])
        #t.daemon = True  # thread dies with the program
        steamthread.start()

    def joinChatCommand(self, command, args):
        if len(args) >= 1:
            chatroom = SteamID(int(args[0]))
            log.info("Connecting to room %s" % chatroom)
            self.steamFriends.JoinChat(chatroom)
            return "Connected to %s" % args[0]

    def leaveChatCommand(self, command, args):
        if len(args) >= 1:
            try:
                chatroom = SteamID(int(args[0]))
                log.info("Disconnecting from room %s" % chatroom)
                self.steamFriends.LeaveChat(chatroom)
            except:
                return "I'm not currently there"

    def _steamloop(self, callbackManager):
        while self._isRunning:
            callbackManager.RunWaitCallbacks(System.TimeSpan.FromSeconds(1))

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
        log.info(message)
        message = message.strip().split(" ")
        try:
            if message[0] == "wb":
                if str(callback.ChatterID) == self.superuser:
                    chatperm = Perm.Super
                else:
                    chatperm = Perm.User
                source = [callback.ChatterID, chatperm]
                response = manager.commandmanager.processCommand(source, message[1:])
                if isinstance(response, tuple):
                    msgresponse = response[0]
                else:
                    msgresponse = response

                if msgresponse is False or msgresponse is None:
                    self._fireChatCallbacks(callback)
                else:
                    msgresponse = msgresponse.strip()
                    if msgresponse != "":
                        self.steamFriends.SendChatRoomMessage(callback.ChatRoomID, EChatEntryType.ChatMsg, str(msgresponse))
            else:
                self._fireChatCallbacks(callback)
        except Exception as e:
            log.error(e)

    def _fireChatCallbacks(self, chatmsg):
        for callback in self.chatcallbacks:
            callback(chatmsg)

    def registerChatCallback(self, callback):
        self.chatcallbacks.append(callback)

    def sendChatMessage(self, room, msg):
        self.steamFriends.SendChatRoomMessage(room, EChatEntryType.ChatMsg, str(msg))

    def destroy(self, callback):
        self.steamUser.LogOff()
        self._destorycallback = callback
        return True
