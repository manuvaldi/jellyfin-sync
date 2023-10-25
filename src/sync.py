import os
import re
import sys
import getopt
import jellyfin_queries
from pathlib import Path
from datetime import datetime

from jellyfin_api_client import jellyfin_login, jellyfin_logout

env_log_level_str = os.environ['LOG_LEVEL'] if 'LOG_LEVEL' in os.environ else ''
config_path = Path(os.environ['CONFIG_DIR']) if 'CONFIG_DIR' in os.environ else Path(Path.cwd() / 'config')
data_path = Path(os.environ['DATA_DIR']) if 'DATA_DIR' in os.environ else Path(config_path / 'data')

session_timestamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")


def print_debug(a=[], log=True, log_file=False):
    # Here a is the array holding the objects
    # passed as the argument of the function
    output = ' '.join([str(elem) for elem in a])
    if log:
        print(output, file=sys.stderr)
    if log_file:
        log_path = config_path / 'logs'
        log_path.mkdir(parents=True, exist_ok=True)
        with (log_path / ('log_%s.txt' % session_timestamp)).open('a') as logger:
            logger.write(output + '\n')


def replace(s):
    return re.sub('[^A-Za-z0-9]+', '', s)


def sync_jellyfins(items1, items2, client1, client2, userId1, userId2, log_file):
    if items1 is None or items2 is None:
        return

    print_debug(a=["found %d items in jellyfin1" % len(items1['Items'])], log_file=log_file)
    print_debug(a=["found %d items in jellyfin2" % len(items2['Items'])], log_file=log_file)

    matched_items = 0
    print("Syncing ->")
    matched_items = sync_items(items1, items2, client2, userId2, matched_items, log_file)
    print("Syncing <-")
    matched_items = sync_items(items2, items1, client1, userId1, matched_items, log_file)

    print_debug(a=["matched %d items" % matched_items], log_file=log_file)


def sync_items(orig, dest, client, userId, matched_items, log_file):
    # Loop over source Items
    for data_item in orig['Items']:
        # Only played of playing items
        if data_item['UserData']['Played'] or data_item['UserData']['PlaybackPositionTicks'] > 0 or data_item['UserData']['IsFavorite']:
            matchedItem = None
            # Check by Providers (IMDB, etc)
            if len(data_item['ProviderIds'].keys()) > 0:
                for item in dest['Items']:
                    # Check by providers
                    failed_provider = 0
                    for provider in data_item['ProviderIds'].keys():
                        if provider in item['ProviderIds'] and data_item['ProviderIds'][provider] == item['ProviderIds'][provider]:
                            matchedItem = item
                        else:
                            failed_provider += 1

                    if failed_provider > 0:
                        matchedItem = None
                    else:
                        matchedItem = item
                        break
            # Check by Name and Type
            else:
                for item in dest['Items']:
                    if item['Name'] == data_item['Name'] and item['Type'] == data_item['Type']:
                        matchedItem = item
                        break

            if matchedItem is not None:
                matched_items += 1
                # print_debug(a=["matched played: %s items from backup" % data_item['Id']], log_file=log_file)
                # print_debug(a=["found item that is in backup and in jellyfin: %s" % data_item['Name']], log_file=log_file)
                jellyfin_queries.update_item(client, userId, matchedItem, data_item)

    return matched_items


def import_and_sync(username1, server_url1, server_username1, server_password1,
                    username2, server_url2, server_username2, server_password2, log_file=False):

    start = datetime.now()
    print_debug(a=["\nstarted new session at %s\n" % start])
    print_debug(a=["Syncing [%s] and [%s]\n" % (server_url1, server_url2)])

    items1 = jellyfin_queries.query_jellyfin(username1, server_url1, server_username1, server_password1)
    items2 = jellyfin_queries.query_jellyfin(username2, server_url2, server_username2, server_password2)

    client1 = jellyfin_login(server_url1, server_username1, server_password1, "Jelly Find")
    client2 = jellyfin_login(server_url2, server_username2, server_password2, "Jelly Find")

    userId1 = jellyfin_queries.get_user_id(client1, username1)
    userId2 = jellyfin_queries.get_user_id(client2, username2)

    sync_jellyfins(items1, items2, client1, client2, userId1, userId2, log_file)
    jellyfin_logout()
    end = datetime.now()
    print_debug(a=["total runtime: " + str(end - start)], log_file=log_file)


def main(argv):
    log_file = False
    username = None
    backup_path = ''

    try:
        opts, args = getopt.getopt(argv, "hl", ["help", "log",
                                                "username1=", "jellyfin_url1=", "jellyfin_username1=", "jellyfin_password1=",
                                                "username2=", "jellyfin_url2=", "jellyfin_username2=", "jellyfin_password2="])
    except getopt.GetoptError:
        print_debug(['sync.py -u username -j backup file -l (log to file)'])
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_debug(['export.py  -l (log to file)'])
            sys.exit()
        elif opt == '-l' or opt == '--log':
            log_file = True

        elif opt == '--username1':
            username1 = arg
        elif opt == '--jellyfin_url1':
            server_url1 = arg
        elif opt == '--jellyfin_username1':
            server_username1 = arg
        elif opt == '--jellyfin_password1':
            server_password1 = arg

        elif opt == '--username2':
            username2 = arg
        elif opt == '--jellyfin_url2':
            server_url2 = arg
        elif opt == '--jellyfin_username2':
            server_username2 = arg
        elif opt == '--jellyfin_password2':
            server_password2 = arg

    if username1 is None:
        username1 = server_username1
    if username2 is None:
        username2 = server_username2
    #
    # if server_url == '' or server_username == '' or server_password == '':
    #     print_debug(['you need to export env variables: JELLYFIN_URL, JELLYFIN_USERNAME, JELLYFIN_PASSWORD\n'])
    #     return
    #

    import_and_sync(username1, server_url1, server_username1, server_password1,
                    username2, server_url2, server_username2, server_password2, log_file)


if __name__ == "__main__":
    main(sys.argv[1:])
