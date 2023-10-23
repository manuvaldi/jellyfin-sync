import os
import copy
from datetime import datetime
import dateutil.parser as parser
from jellyfin_api_client import jellyfin_login, jellyfin_logout


def get_user_id(client=None, username=''):
    if client is None or username == '':
        return
    try:
        users = client.jellyfin.get_users()
        for user in users:
            if 'Name' not in user:
                continue
            if user['Name'] == username:
                print('matched id for username %s' % username)
                return user['Id']
    except BaseException as err:
        print(err)
        return ''
    return ''


def query_items(client=None, userId=None, limit=100, startIndex=0, includeItemTypes=('Episode'), fields=('ProviderIds', 'UserData')):
    if client is None:
        return []

    if userId is None:
        return []

    items = []

    '''
    SortBy=SeriesSortName,SortName
    SortOrder=Ascending
    IncludeItemTypes=Episode
    Recursive=true
    Fields=ProviderIds,UserData
    IsMissing=false
    StartIndex=0
    Limit=100
    '''

    try:
        result = client.jellyfin.items(params={
            'UserId': userId,
            'Recursive': True,
            'includeItemTypes': includeItemTypes,
            'SortBy': 'DateCreated,SortName,Type,Id',
            'SortOrder': 'Ascending',
            'enableImages': False,
            'enableUserData': True,
            'Fields': fields,
            'Limit': limit,
            'StartIndex': startIndex
        })

        if 'Items' in result and result['Items']:
            for item in result['Items']:
                # if item['UserData']['Played'] or item['Id'] == result['Items'][0]['Id']:
                newItem = {}
                newItem['Name'] = item['Name']
                newItem['Id'] = item['Id']
                newItem['Type'] = copy.deepcopy(item['Type'])
                newItem['ProviderIds'] = copy.deepcopy(item['ProviderIds'])
                newItem['UserData'] = copy.deepcopy(item['UserData'])
                items.append(newItem)
    except BaseException as err:
        print(err)
        return []
    return items


def get_items(client=None, userId=None, includeItemTypes=('Episode')):
    if client is None:
        return []
    limit = os.environ['QUERY_LIMIT'] if 'QUERY_LIMIT' in os.environ else 5000
    items = []
    startIndex = 0
    previousCount = -1

    while previousCount != 0:
        newItems = query_items(client=client, userId=userId, limit=limit, startIndex=startIndex, includeItemTypes=includeItemTypes)
        previousCount = len(newItems)
        print(includeItemTypes, '+=', previousCount)
        startIndex += previousCount
        if newItems:
            items.extend(newItems)

    return items


def get_episodes(client=None, userId=None):
    return get_items(client=client, userId=userId, includeItemTypes=('Episode'))


def get_movies(client=None, userId=None):
    return get_items(client=client, userId=userId, includeItemTypes=('Movie'))


def update_item(client, userId, matchedItem, data_item):
    if matchedItem is None or data_item is None or client is None:
        return
    # print("Updating Item: " + str(data_item['Id']) + " - " + data_item['Name'])

    if data_item['UserData']['Played'] is True and matchedItem['UserData']['Played'] is False:
        request_for_user(client, userId, '%s/%s' % ('PlayedItems', matchedItem['Id']))
        print(" Updated played "+ str(data_item['Id']) + " - " + data_item['Name'])

    if data_item['UserData']['PlaybackPositionTicks'] != matchedItem['UserData']['PlaybackPositionTicks']:
        if 'LastPlayedDate' in data_item['UserData'].keys():
            date1 = datetime.timestamp(parser.parse(data_item['UserData']['LastPlayedDate']))
        else:
            date1 = 0

        if 'LastPlayedDate' in matchedItem['UserData'].keys():
            date2 = datetime.timestamp(parser.parse(matchedItem['UserData']['LastPlayedDate']))
        else:
            date2 = 0
            
        if date1 > date2:
            request_for_user_playing(client, userId, matchedItem['Id'], data_item['UserData']['PlaybackPositionTicks'] )
            print(" Updated position ticks "+ str(data_item['Id']) + " - " + data_item['Name'])

    if data_item['UserData']['IsFavorite'] is True:
        request_for_user(client, userId, '%s/%s' % ('FavoriteItems', matchedItem['Id']))
        print(" Updated favorite "+ str(data_item['Id']) + " - " + data_item['Name'])


def request_for_user(client, userId, path, json=None, params=None):
    client.jellyfin._post("Users/%s/%s" % (userId, path), json=json, params=params)

def request_for_user_playing(client, userId, id, ticks):
    new_item = {}
    new_item['PositionTicks'] = ticks
    client.jellyfin._delete("Users/%s/PlayedItems/%s" % (userId, id), params=None)
    client.jellyfin._delete("Users/%s/PlayingItems/%s" % (userId, id), params=new_item)

def query_jellyfin(username='', server_url='', server_username='', server_password=''):
    if username == '' or server_url == '' or server_username == '' or server_password == '':
        print('missing server info')
        return

    client = jellyfin_login(server_url, server_username, server_password, "Jelly Find")
    userId = get_user_id(client, username)
    items = {}
    items['User'] = username
    items['Items'] = []
    episodes = get_episodes(client, userId)
    movies = get_movies(client, userId)
    items['Items'].extend(episodes)
    items['Items'].extend(movies)
    print('user %s has %s episodes, %s movies' % (username, len(episodes), len(movies)))
    jellyfin_logout()
    return items
