import requests
import json

# Replace with your API key
API_KEY = 'c014ea1f-8ad2-482f-aab0-2d7a8ddd3144'
headers = {
    'Authorization': f'Bearer {API_KEY}'
}

"https://www.faceit.com/api/stats/v1/stats/users/lifetime?match_id=1-affde9fe-e35b-40ff-bb96-132c64050fbc&game=cs2&player_ids=3234c7d4-9103-4596-9277-eb28de6af0de&player_ids=9d65cd1b-199a-46a5-ac6c-653c8b541b13&player_ids=757315ae-43c3-4fe8-8229-e1b5f65cc7dd&player_ids=1866a510-b0e9-47eb-b8f6-2001551cf14b&player_ids=469427d6-9cf4-418d-bf12-2c021ea5e52e&player_ids=77dce6df-0823-4703-aa62-5b1270c6c8ec&player_ids=94e0bb7a-c2ce-4d26-bd77-4b49ca112e54&player_ids=b77bb087-99f3-45ad-9dbc-94c514dd1b4f&player_ids=c30a6261-44f9-4a32-ab13-ec87e040f004&player_ids=7b9c494d-6463-45c4-8952-1fb9f1216e8c"

# Step 1: Get your friend's FACEIT ID
def get_player_id(nickname):
    url = f'https://open.faceit.com/data/v4/players?nickname={nickname}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data['player_id']

# Step 2: Get the latest match ID
def get_latest_match_id(player_id):
    url = f'https://open.faceit.com/data/v4/players/{player_id}/history'
    response = requests.get(url, headers=headers)
    data = response.json()
    with open('streamElements/resources/match_history.json', 'w') as f:
        f.write(json.dumps(data, indent=4))
    return data['items'][0]['match_id']

# Step 3: Get match details
def get_match_details(match_id):
    url = f'https://open.faceit.com/data/v4/matches/{match_id}'
    response = requests.get(url, headers=headers)
    return response.json()

# Step 4: Get player statistics
def get_player_stats(player_id):
    url = f'https://open.faceit.com/data/v4/players/{player_id}/stats/cs2'
    response = requests.get(url, headers=headers)
    return response.json()

def get_latest_match_players_stats(friend_nickname):
    # Example usage:
    player_id = get_player_id(friend_nickname)
    print(player_id)
    match_id = get_latest_match_id(player_id)
    match_details = get_match_details(match_id)

    # Collect stats for all players in the match
    player_stats = {}
    for team in match_details['teams'].values():
        for player in team['roster']:
            stats = get_player_stats(player['player_id'])
            player_stats[player['nickname']] = stats

    # with open('streamElements/resources/player_stats.json', 'w') as f:
    #     f.write(json.dumps(player_stats, indent=4))

    return player_stats


def get_latest_match_players_list(username):
    stats = get_latest_match_players_stats(username)
    player_list = list(stats.keys())
    return [player_list[:5], player_list[5:]] 

if __name__ == '__main__':
    print(get_latest_match_players_list("DaddyRunah"))
