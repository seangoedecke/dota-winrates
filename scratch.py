# scratch API methods I don't need yet

# https://developer.valvesoftware.com/wiki/Steam_Web_API#License_and_further_documentation
# https://github.com/joshuaduffy/dota2api/blob/master/dota2api/src/urls.py
# https://wiki.teamfortress.com/wiki/WebAPI#Dota_2

FRIENDS_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
NAMES_ENDPOINT = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

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

@app.route("/api/v1/friends", methods=['GET'])
def friend_ids():
    args = request.args.to_dict()
    friends = fetch_friend_ids(args['steamid'])
    return jsonify(friends)

@app.route("/api/v1/friends/names", methods=['GET'])
def friends():
    args = request.args.to_dict()
    ids = fetch_friend_ids(args['steamid'])
    friends = fetch_friends(ids)
    return jsonify(friends)

@app.route("/api/v1/friends/matches", methods=['GET'])
def friends_matches():
    args = request.args.to_dict()
    print "Fetching friends..."
    ids = fetch_friend_ids(args['steamid'])
    print "Getting names..."
    friends = fetch_friends(ids)
    friends_with_matches = []
    for friend in friends:
        print "Getting matches for " + friend['name'] + "..."
        friends_with_matches.append({
            'id': friend['id'],
            'name': friend['name'],
            'matches': fetch_matches(friend['id'])
        })
    return jsonify(friends_with_matches)

@app.route("/api/v1/match_details", methods=['GET'])
def match_details():
    args = request.args.to_dict()
    details = fetch_match_details(args['matchid'], args['steamid'])
    return jsonify(details)
