from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

API_KEY = "4E8E3E7A328FAA7814C46E719092F581"
MATCH_HISTORY_ENDPOINT = "http://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/"
MATCH_DETAILS_ENDPOINT = "http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1"

CLUSTERS = {    # nicked from https://github.com/odota/dotaconstants
  "111": 1,
  "112": 1,
  "113": 1,
  "121": 2,
  "122": 2,
  "123": 2,
  "124": 2,
  "131": 3,
  "132": 3,
  "133": 3,
  "134": 3,
  "135": 3,
  "136": 3,
  "137": 3,
  "138": 3,
  "144": 19,
  "145": 19,
  "151": 5,
  "152": 5,
  "153": 5,
  "154": 5,
  "155": 5,
  "156": 5,
  "161": 6,
  "171": 7,
  "172": 7,
  "181": 8,
  "182": 8,
  "183": 8,
  "184": 8,
  "185": 8,
  "186": 8,
  "187": 8,
  "188": 8,
  "191": 9,
  "192": 9,
  "193": 9,
  "201": 10,
  "202": 10,
  "204": 10,
  "211": 11,
  "212": 11,
  "213": 11,
  "223": 18,
  "224": 12,
  "225": 17,
  "227": 20,
  "231": 13,
  "232": 25,
  "241": 14,
  "242": 14,
  "251": 15,
  "261": 16
}

REGIONS = { # again, nicked from dotaconstants
  "0": "AUTOMATIC",
  "1": "US WEST",
  "2": "US EAST",
  "3": "EUROPE",
  "5": "SINGAPORE",
  "6": "DUBAI",
  "7": "AUSTRALIA",
  "8": "STOCKHOLM",
  "9": "AUSTRIA",
  "10": "BRAZIL",
  "11": "SOUTHAFRICA",
  "12": "PW TELECOM SHANGHAI",
  "13": "PW UNICOM",
  "14": "CHILE",
  "15": "PERU",
  "16": "INDIA",
  "17": "PW TELECOM GUANGDONG",
  "18": "PW TELECOM ZHEJIANG",
  "19": "JAPAN",
  "20": "PW TELECOM WUHAN",
  "25": "PW UNICOM TIANJIN"
}

# Helpers

def fetch_matches(steamid):
    # grab the final match_id and request again if you want more than 100
    payload = {
        'key': API_KEY,
        'account_id': steamid,
        'matches_requested': 100  # 100 max
        }
    response = requests.get(MATCH_HISTORY_ENDPOINT, params=payload)

    if response.json()['result']['status'] != 1: # check if player match history is public
        return []

    matches = response.json()['result']['matches']
    match_ids = []
    for match in matches:
        match_ids.append(match['match_id'])
    return match_ids

def fetch_match_details(match_id, steamid):
    # grab the final match_id and request again if you want more than 100
    payload = {
        'key': API_KEY,
        'match_id': match_id,
        }
    response = requests.get(MATCH_DETAILS_ENDPOINT, params=payload)

    details = response.json()['result']

    # did the player win?
    player_is_radiant = True
    for player in details['players']:
        if str(steamid) == str(player['account_id']):
            if player['player_slot'] < 5:
                player_is_radiant = True
            else:
                player_is_radiant = False
    if (player_is_radiant and details['radiant_win']) or (not player_is_radiant and not details['radiant_win']):
        player_won = True
    else:
        player_won = False

    data = {
        "player_won": player_won,
        "server_cluster": details['cluster'],
        "ranked?": str(details['lobby_type']) == "7"
        }

    return data

def calculate_winrate_by_server(match_details):
    server_list = {}
    for item in match_details:

        region_code = CLUSTERS[str(item['server_cluster'])]   # show regions rather than data centers
        region = REGIONS[str(region_code)]

        if region not in server_list:
            server_list[region] = []

        server_list[region].append({
            'won': item['player_won'],
            'ranked': item['ranked?']
        })

    winrate_list = []
    for server in server_list:
        ranked = {
            'wins': 0,
            'losses': 0,
            'games': 0
        }
        unranked = {
            'wins': 0,
            'losses': 0,
            'games': 0
        }

        for result in server_list[server]:
            if result['ranked']:
                ranked['games'] = ranked['games'] + 1
                if result['won']:
                    ranked['wins'] = ranked['wins'] + 1
                else:
                    ranked['losses'] = ranked['losses'] + 1
            else:
                unranked['games'] = unranked['games'] + 1
                if result['won']:
                    unranked['wins'] = unranked['wins'] + 1
                else:
                    unranked['losses'] = unranked['losses'] + 1

        ranked_winrate_for_server = float(ranked['wins'])/(ranked['games']) if ranked['games'] > 0 else None
        unranked_winrate_for_server = float(unranked['wins'])/(unranked['games']) if unranked['games'] > 0 else None

        winrate_list.append({
            'server': server,
            'stats': {
                'ranked': {
                    'games': ranked['games'],
                    'winrate': ranked_winrate_for_server,
                    'wins': ranked['wins'],
                    'losses': ranked['losses']
                },
                'unranked': {
                    'games': unranked['games'],
                    'winrate': unranked_winrate_for_server,
                    'wins': unranked['wins'],
                    'losses': unranked['losses']
                }
            }
        })

    return winrate_list

# Routes

# @app.route("api/v1/fetch_matches", methods=['GET'])
# def fetch_matches():
#     args = request.args.to_dict()
#     matches = fetch_matches(args['steamid'])
#     return jsonify(matches)
#
# @app.route("api/v1/fetch_match_details", methods=['GET'])
# def fetch_ranked_matches():
#     args = request.args.to_dict()
#     matches = fetch_ranked_matches(args['steamid'])
#     return jsonify(matches)

@app.route("/api/v1/server_winrates", methods=['GET'])
def server_winrates():
    args = request.args.to_dict()
    matches = fetch_matches(args['steamid'])

    match_details = []
    for match_id in matches:
        print "Fetching match: " + str(match_id)
        match_details.append(fetch_match_details(match_id, args['steamid']))
    winrates = calculate_winrate_by_server(match_details)

    return jsonify(winrates)

if __name__ == "__main__":
    app.run()
