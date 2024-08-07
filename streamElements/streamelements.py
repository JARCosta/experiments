
import datetime
from math import sqrt
import requests
import json
import time

import telegramBot
import twitch_message_sender

balance_url = "https://api.streamelements.com/kappa/v2/points/5a2ae33308308f00016e684e/el_pipow?providerId=462756951"
bets_url = "https://api.streamelements.com/kappa/v2/contests/5a2ae33308308f00016e684e/active"

CHAT_ID = "6449165312"

def get_balance():
    response = requests.get(balance_url)
    response_json = response.json()
    return response_json['points']

def calculate_bet(options):

    for i in options.keys():
        options[i] += 1

    bet_option = "win" if options["win"] < options["lose"] else "lose"
    oposite_option = "lose" if bet_option == "win" else "win"

    current_balance_ratio_on_our_option = options[bet_option] / options[oposite_option]

    our_bet_ratio = -current_balance_ratio_on_our_option + sqrt(current_balance_ratio_on_our_option)

    bet_ammount = our_bet_ratio * options[oposite_option]
    bet_ammount = round(bet_ammount)


    # diff_options = abs(options["win"] - options["lose"])
    # bet_ammount = min(diff_options, 5000)

    bet_ratio = bet_ammount/(options[bet_option]+bet_ammount)

    # if bet_ratio > 0.9:
    #     # lower bet to equalize the bet ration to 0.9
    #     bet_ammount = int(9*(options[bet_option]+1))
    # elif bet_ratio < 0.1:
    #     return bet_option, 0

    # if 100 * round(bet_ammount / 100) != 0:
    #     bet_ammount = 100 * round(bet_ammount / 100)

    print("Betting {} on {}, representing {}% of the winning pot".format(bet_ammount, bet_option, round(100*bet_ratio)))
    return bet_option, bet_ammount



def get_bets():

    wst, ws = twitch_message_sender.launch()

    try:
        while True:
            response = requests.get(bets_url)
            response_json = response.json()
            
            if response_json["contest"] == None:
                print("No contest found")
                print("\n")
                time.sleep(60)
                continue
            
            with open('resources/bets.json', 'w') as f:
                json.dump(response_json, f, indent=4)
            
            start = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1)
            end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1, minutes=response_json["contest"]["duration"])
            now = datetime.datetime.now()


            if start < now < end and (end - now).total_seconds() > 6:

                print("Bets are open")
                print("Time left: {} seconds".format(round((end - now).total_seconds())))
                print("You have {} points".format(get_balance()))
                print("\n")

                telegram_message = "Contest found\n"
                telegram_message += "Time left: {} seconds\n".format(round((end - now).total_seconds()))
                telegram_message += "Follow it through: {}\n".format("https://streamelements.com/runah/contest/" + response_json["contest"]["_id"])
                telegram_message += "You have {} points\n".format(get_balance())
                telegramBot.sendMessage(telegram_message)

                time.sleep(int((end - now).total_seconds() - 3))
            
            elif start < now < end and (end - now).total_seconds() <= 5:
                
                print("Time to place your bets")
                print("The pot is at {} points".format(response_json["contest"]["totalAmount"]))
                for option in response_json["contest"]["options"]:
                    print("Option {}: {} points".format(option["title"], option["totalAmount"]))
                print("Time left: {} seconds".format(round((end - now).total_seconds())))
                print("\n")


                telegram_message = "Time to place your bets\n"
                telegram_message += "The pot is at {} points\n".format(response_json["contest"]["totalAmount"])
                for option in response_json["contest"]["options"]:
                    telegram_message += "Option {}: {} points\n".format(option["title"], option["totalAmount"])
                telegram_message += "Time left: {} seconds\n".format(round((end - now).total_seconds()))
                telegramBot.sendMessage(telegram_message)
                
                options = {}
                for option in response_json["contest"]["options"]:
                    options[option["command"]] = int(option["totalAmount"])
                
                bet_option, bet_ammount = calculate_bet(options)
                oposite_option = "lose" if bet_option == "win" else "win"

                if bet_ammount > 0:
                    twitch_message_sender.bet(ws, bet_option, str(bet_ammount))

                telegram_message = "Betting {} on {}, representing {}% of the winning pot\n".format(bet_ammount, bet_option, round(100*bet_ammount/(options[bet_option]+bet_ammount)))
                return_ammount = options[oposite_option] * (bet_ammount/(options[bet_option]+bet_ammount))
                telegram_message += "The odd of this bet is {}\n".format((return_ammount + bet_ammount)/bet_ammount)
                telegramBot.sendMessage(telegram_message)

                time.sleep(5)

            elif start < end < now:
                print("Bets closed {}:{}:{} ago".format( int((now - end).total_seconds()//3600),int((now - end).total_seconds()//60), int((now - end).total_seconds()%60)))
                print("The pot is at {} points".format(response_json["contest"]["totalAmount"]))

                options = {}
                for option in response_json["contest"]["options"]:
                    print("{} points were bet on {}".format(option["totalAmount"], option["title"]))
                    options[option["command"]] = int(option["totalAmount"])
                print("You have {} points".format(get_balance()))
                print("\n")

                time.sleep(60)

            else:
                print("Bets are not open yet")
                print("Something is off")
                print("Check out what's going on")
                print("\n")

                telegram_message = "Bets are not open yet\n"
                telegram_message += "Something is off\n"
                telegram_message += "Check out what's going on"
                telegramBot.sendMessage(telegram_message)

                time.sleep(60)

    except KeyboardInterrupt:
        twitch_message_sender.close(wst, ws)


if __name__ == "__main__":
    get_bets()

