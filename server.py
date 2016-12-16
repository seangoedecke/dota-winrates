from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# https://developer.valvesoftware.com/wiki/Steam_Web_API#License_and_further_documentation
# https://github.com/joshuaduffy/dota2api/blob/master/dota2api/src/urls.py
# https://wiki.teamfortress.com/wiki/WebAPI#Dota_2

API_KEY = "4E8E3E7A328FAA7814C46E719092F581"
FRIENDS_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
NAMES_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
MATCH_HISTORY_ENDPOINT = "http://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/"

def fetch_friends(steamid):
    payload = { 'key': API_KEY, 'steamid': steamid, 'relationship': 'friend'}
    response = requests.get(FRIENDS_ENDPOINT, params=payload)
    friends = response.json()['friendslist']['friends']
    ids = []
    for friend in friends:
        ids.append(friend['steamid'])
    return ids

def fetch_names(ids):
    ids_str = ''
    for id in ids:
        ids_str = ids_str + id + ','
    payload = { 'key': API_KEY, 'steamids': ids_str}
    response = requests.get(NAMES_ENDPOINT, params=payload)
    profiles = response.json()['response']['players']
    names = []
    for profile in profiles:
        names.append(profile['personaname'])
    return names


@app.route("/api/v1/friends", methods=['GET'])
def friends():
    args = request.args.to_dict()
    friends = fetch_friends(args['steamid'])
    return jsonify(friends)

@app.route("/api/v1/friends/names", methods=['GET'])
def names():
    args = request.args.to_dict()
    friends = fetch_friends(args['steamid'])
    names = fetch_names(friends)
    return jsonify(names)

if __name__ == "__main__":
    app.run()
