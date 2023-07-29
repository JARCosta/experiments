import json
import requests

def load_year(year: int):

    api_url = f"https://nba-stats-db.herokuapp.com/api/playerdata/season/{year}"

    response = requests.get(api_url)
    response = response.json()

    players = {}

    while (response["next"] != None):

        response = requests.get(api_url)
        response = response.json()

        page_num = api_url.split('page')
        page_num = page_num[1].split('=')[1] if len(page_num) > 1 else "1"
        # print(f"Loading page {page_num} ({response['count']} players)")
        print(f"Loading page {page_num}")

        for i in response:
            if i != "results":
                # print(i + ":", response[i])
                pass
            else:
                for j in response["results"]:
                    # print(j)
                    # break
                    players[j["player_name"]] = j
        
        api_url = response["next"]

    with open(f"data/{year}.json", "w") as outfile:
        json.dump(dict(sorted(players.items())), outfile, indent=4)

    print(f"Loaded  year {year}, {len(players)} players")

    return players

for i in range(2023, 2009, -1):
    load_year(i)
