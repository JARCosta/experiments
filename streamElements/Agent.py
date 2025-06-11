import os
import threading
import time
import traceback
import websocket



import telegramBot
from . import message_parser
from . import betting

class Agent:

    def __init__(self, channel:str, username:str, oauth_key:str, kill_event:threading.Event):
        self.channel = channel
        self.username = username
        self.oauth_key = oauth_key
        self.open_event = threading.Event()
        self.kill_event = kill_event

        self.bets_close_stamp = None




        self.websocket_url = "wss://irc-ws.chat.twitch.tv/"
        self.ws = websocket.WebSocketApp(
            self.websocket_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_open=self.on_open
        )

        # Run the WebSocket connection in a separate thread to avoid blocking
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

        self.open_event.wait()
        
        try:
            betting.bet(self.ws, self.username, self.channel, self.kill_event)
        except Exception as e:
            telegramBot.sendMessage(traceback.format_exc(), notification=True)


        self.kill_event.wait()
        print("Kill event received, closing websocket...")
        self.ws.close()
        
        # Give the websocket thread a moment to close gracefully
        wst.join(timeout=2)
        if wst.is_alive():
            print("WebSocket thread did not close gracefully, forcing exit...")
        
        print(f"Agent disconnected from {self.channel}")

    

    def connect(self, ws:websocket.WebSocketApp, message:str):
        if f":Welcome, GLHF!" in message:
            ws.send(f"JOIN #{self.channel}")
        
        elif f"ROOMSTATE #{self.channel.lower()}" in message:
            print(f"{self.username} connected to {self.channel} ({self.__class__.__name__.replace('launch_', '').capitalize()})")
            self.open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            telegram_message = f"Received RECONNECT message from Twitch on a {self.__class__.__name__.replace('launch_', '').capitalize()} WebSocket\n"
            telegram_message += f"Reconnecting viewer {self.username} to {self.channel}\n"
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
            self.__init__(self.channel, self.username, self.oauth_key, self.kill_event)            

        elif "PING :tmi.twitch.tv" in message:
            ws.send("PONG")
            ws.send("PING")
            # telegramBot.sendMessage(f"{creator_function.__name__.replace('launch_', '').capitalize()} returned a PING")
        
        elif ":Login authentication failed" in message:
            try:
                os.remove(self.username.upper() + '_OAUTH')
            except FileNotFoundError:
                pass
            telegramBot.sendMessage(f"{self.creator_function.__name__.replace('launch_', '').capitalize()}: Invalid {self.username}'s OAuth key", notification=True)


    def on_message(self, ws:websocket.WebSocketApp, message:str):
        self.connect(ws, message)
        
        parsed = message_parser.parse_twitch_message(message)
        if parsed and parsed['command'] == 'PRIVMSG':
            # print(message_parser.format_message_json(parsed)['message'])

            message_text = parsed['message']
            sender = parsed['source']['nick']
            mentioned = message_parser.check_if_mentioned(parsed['message'], self.username)

            if sender == 'streamelements':
                if "a new contest has started" in message_text: # New bet
                    try:
                        threading.Thread(target=betting.bet, args=[ws, self.username, self.channel, self.kill_event]).start()
                    except Exception as e:
                        telegramBot.sendMessage(traceback.format_exc(), notification=True)
                    # telegramBot.sendMessage(f"[{self.channel}] {sender}: {message_text}")

                elif "no longer accepting bets for" in message_text: # Bet's closed
                    # telegramBot.sendMessage(f"[{self.channel}] {sender}: {message_text}")
                    pass
                elif "won the contest" in message_text: # Result of the bet
                    if betting.LAST_BET:
                        winner_option = message_text.split('"')[1]
                        if winner_option.lower() == betting.LAST_BET[0]:
                            log = f"Won a bet of {betting.LAST_BET[1]} points\n"
                            log += f"b value was {round(betting.LAST_BET[3][0], 3)}\n"
                            log += f"profited {round(betting.LAST_BET[3][2])} points\n"
                            telegramBot.add_telegram_log(log)
                        else:
                            log = f"Lost a bet of {betting.LAST_BET[1]} points\n"
                            log += f"b value was {round(betting.LAST_BET[3][0], 3)}\n"
                            telegramBot.add_telegram_log(log)
                        betting.LAST_BET = None
                        telegramBot.send_telegram_log()
                elif ", you have bet" in message_text: # Someone bet
                    # telegramBot.sendMessage(f"[{self.channel}] {sender}: {message_text}")
                    print(f"[{self.channel}] {sender}: {message_text}")

                return

            elif mentioned:
                telegramBot.sendMessage(f"[{self.channel}] {sender}: {parsed['message_text']}")
                





    def on_error(self, ws:websocket.WebSocketApp, error:str):
        telegram_message = "Websocket error:\n"
        telegram_message += f"error,{error}, {error.__traceback__}, {type(error) == websocket._exceptions.WebSocketConnectionClosedException}\n"
        telegram_message += traceback.format_exc() + "\n"
        if type(error) == websocket._exceptions.WebSocketConnectionClosedException or error == websocket._exceptions.WebSocketConnectionClosedException:
            telegram_message += f"launching new {self.__class__.__name__}\n"
            self.ws.close()
            time.sleep(5)
            self.ws.run_forever()
        print(telegram_message)
        telegramBot.sendMessage(telegram_message, notification=True)


    def on_open(self, ws:websocket.WebSocketApp):
        self.open_event.set()
        print(f"Logging {self.username} {self.oauth_key}")
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send(f"PASS oauth:{self.oauth_key}")
        ws.send(f"NICK {self.username}")
        ws.send(f"USER {self.username} 8 * :{self.username}")



