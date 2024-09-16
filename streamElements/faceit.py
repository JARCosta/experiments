import requests
import json

# Replace with your API key
API_KEY = 'c014ea1f-8ad2-482f-aab0-2d7a8ddd3144'
headers = {
    'Authorization': f'Bearer {API_KEY}'
}

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
