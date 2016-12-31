from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests
from lxml import html

app = Flask(__name__)
CORS(app)

API_KEY = "4E8E3E7A328FAA7814C46E719092F581"
MATCH_HISTORY_ENDPOINT = "http://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/"
MATCH_DETAILS_ENDPOINT = "http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1"

FRIENDS_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
NAMES_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

DB_HISTORY_ENDPOINT = "https://www.dotabuff.com/players/" # 123123123
# /matches?lobby_type=ranked_matchmaking&region=india

def get_history_endpoint(steamid, region):
    return DB_HISTORY_ENDPOINT + str(steamid) + "/matches?lobby_type=ranked_matchmaking&region=" + region


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

DB_REGIONS = [
    'us_west',
    'us_east',
    'europe_west',
    'south_korea',
    'se_asia',
    'chile',
    'australia',
    'russia',
    'europe_east',
    'south_america',
    'south_africa',
    'china',
    'peru',
    'dubai',
    'india'
]

DB_TO_OD = {
    'us_west': "US WEST",
    'us_east': "US EAST",
    'europe_west': "EUROPE",
    'south_korea': "PW UNICOM",
    'se_asia': "SINGAPORE",
    'chile' : "CHILE",
    'australia': "AUSTRALIA",
    'russia': "EUROPE",
    'europe_east': "EUROPE",
    'south_america': "BRAZIL",
    'south_africa': "SOUTHAFRICA",
    'china': "PW TELECOM GUANGDONG",
    'peru': "PERU",
    'dubai': "DUBAI",
    'india': "INDIA"
}

# Helpers

def fetch_friend_ids(steamid):
    payload = { 'key': API_KEY, 'steamid': steamid, 'relationship': 'friend'}
    response = requests.get(FRIENDS_ENDPOINT, params=payload)
    friends = response.json()['friendslist']['friends']
    ids = []
    for friend in friends:
        ids.append(friend['steamid'])
    return ids

def fetch_friends(ids):
    ids_str = ''
    for id in ids:
        ids_str = ids_str + id + ','
    payload = { 'key': API_KEY, 'steamids': ids_str}
    response = requests.get(NAMES_ENDPOINT, params=payload)
    profiles = response.json()['response']['players']
    names = []
    for profile in profiles:
        names.append({'name': profile['personaname'], 'id': profile['steamid']})
    return names

def fetch_matches(steamid):
    # grab the final match_id and request again if you want more than 100
    payload = {
        'key': API_KEY,
        'account_id': steamid,
        'matches_requested': 100  # 100 max
        }
    response = requests.get(MATCH_HISTORY_ENDPOINT, params=payload)

    # try:    # make sure response is parseable
    #     response.json()
    # except ValueError:
    #     print response
    #     return []

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

    # try:    # make sure response is parseable
    #     response.json()
    # except ValueError:
    #     print response
    #     return False

    details = response.json()['result']

    # did the player win?
    player_is_radiant = True
    for player in details['players']:
        if 'account_id' not in player: # I think bots don't have account_id?
            continue
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

@app.route("/api/v1/friends/names", methods=['GET'])
def friends():
    args = request.args.to_dict()
    ids = fetch_friend_ids(args['steamid'])
    friends = fetch_friends(ids)
    return jsonify(friends)

@app.route("/api/v1/server_winrates", methods=['GET'])
def server_winrates():
    args = request.args.to_dict()
    matches = fetch_matches(args['steamid'])

    match_details = []
    for match_id in matches:
        match = fetch_match_details(match_id, args['steamid'])
        if match:
            match_details.append(match)
    winrates = calculate_winrate_by_server(match_details)

    return jsonify(winrates)

@app.route("/api/v2/server_winrates", methods=['GET'])
def server_winrates_v2():
    args = request.args.to_dict()

    # fake a 'real' request so DB doesn't hit us with a 429
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'})

    db_winrates = {}
    for region in DB_REGIONS:
        response = session.get(get_history_endpoint(args['steamid'], region))
        tree = html.fromstring(response.content)
        wr_list = tree.xpath('//span[@class="color-stat-win"]/text()')
        if len(wr_list) > 0:
            winrate = wr_list[0]
            db_winrates[region] = winrate

    winrates = []
    for server in db_winrates:
        new_name = DB_TO_OD[server]
        winrates.push = {
        'server': new_name
        'stats': {
            'ranked': {
                'winrate': db_winrates[server],
                'games': 10
                },
            'unranked': {   # mocked out 'neutral' data
                'winrate': 0.5,
                'games': 10
            }
            }
        } # massage into expected format

    return jsonify(winrates)

if __name__ == "__main__":
    app.run()
