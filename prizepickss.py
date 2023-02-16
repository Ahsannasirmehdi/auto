import requests
from datetime import datetime
import json
from multiprocessing import freeze_support
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os
os.chdir(os.path.dirname(__file__))

# ------- User Settings -------
SLEEP_TIMEOUT = 5
WEBHOOK_DISCORD_BOT = 'https://discord.com/api/webhooks/1013183637568618507/3UY6O-8A0nW9lqZnJNZV74gNcZH5CLsK67HBfbpBzZgi1i5RbD2u2cg2_luF77oZeGU7'
SPORTS = {
    '7': {

        'data': {},
        'id': '7',
        'name': 'NBA'
    },
    '124': {

        'data': {},
        'id': '124',
        'name': 'CSGO'
    },
    '121': {

        'data': {},
        'id': '121',
        'name': 'LOL'
    },
    '3': {

        'data': {},
        'id': '3',
        'name': 'WNBA'
    },
    '15': {

        'data': {},
        'id': '15',
        'name': 'CFB'
    },
    '9': {

        'data': {},
        'id': '9',
        'name': 'NFL'
    },
    '2': {

        'data': {},
        'id': '2',
        'name': 'MLB'
    },
    '231': {

        'data': {},
        'id': '231',
        'name': 'MLB LIVE'
    }
}

# ------- User Settings -------


def sendMessage(sport_name, player_name, attr, old_score, new_score, vs, image):
    r = requests.post(WEBHOOK_DISCORD_BOT, json={"embeds": [
        {
            "title": '%s BUMP' % sport_name,
            "description": '',
            "thumbnail": {
                "url": image
            },
            "color": 1347902,
            'fields': [
                {
                    "name": "Player",
                    "value": player_name
                },
                {
                    "name": "Opponent",
                    "value": vs
                },
                {
                    "name": "Prop",
                    "value": attr
                },
                {
                    "name": "Previous / Current",
                    "value": '%s / %s' % (str(old_score), str(new_score))
                }

            ],
            "footer": {"text": 'Powered By lagripe',
                       'icon_url': 'https://i.imgur.com/vN2FRj6.png'},
            'timestamp': str(datetime.utcnow())
        }

    ]
    })


def getStats(drive, sport_id):
    players_out = {}

    def getFilters(included):
        return {filter['id']: filter['attributes']['name'] for filter in included if filter['type'] == "stat_type"}

    def getPlayers(included):
        return {filter['id']: {"id": filter['id'], "name": filter['attributes']['name'], "team": filter['attributes']['team'], "position": filter['attributes']['position'], 'image': filter['attributes']['image_url']} for filter in included if filter['type'] == "new_player"}
    try:
        drive.get(
            'https://api.prizepicks.com/projections?league_id=%s&per_page=500&single_stat=true' % sport_id)
        # sleep(2)
        data = json.loads(drive.find_element(
            by=By.XPATH, value="/html/body").text)
        # print(data.keys())
        if data.get('included') is None:
            return {}
        included = data['included']
        filters = getFilters(included)
        # print(filters)
        players = getPlayers(included)
        # Get Player Scores
        for event in data['data']:
            player_id = event['relationships']['new_player']['data']['id']
            start_id = event['attributes']['description']
            if(players_out.get(player_id)) is None:
                players_out[player_id] = {start_id:
                                          {**players[player_id],
                                           **{event['attributes']['stat_type']: event['attributes']['line_score'], "vs": event['attributes']['description']}}}
            else:
                if players_out[player_id].get(start_id) is None:
                    players_out[player_id][start_id] = {**players[player_id],
                                                        **{event['attributes']['stat_type']: event['attributes']['line_score'], "vs": event['attributes']['description']}}
                else:
                    players_out[player_id][start_id] = {
                        **players_out[player_id][start_id],
                        **{event['attributes']['stat_type']: event['attributes']['line_score'], "vs": event['attributes']['description']}}

        return players_out
    except Exception as e:
        # print(str(e)[:250])
        return None


if __name__ == '__main__':
    freeze_support()
    closed_attrs = ['name', 'id', 'vs', 'position', 'team', 'image']
    print('[-] Prizepicks Sniffer..')
    print('[-] Sports : %s' % len(SPORTS.keys()))
    counter = 1
    while True:
        try:
            opts = uc.ChromeOptions()
            opts.add_argument(f'--headless')
            prefs = {"profile.managed_default_content_settings.images": 2}
            opts.add_argument('--no-sandbox')
            # opts.add_argument('--disable-gpu')
            opts.add_experimental_option("prefs", prefs)
            drive = uc.Chrome(options=opts)
            drive.get('https://app.prizepicks.com/')
            for sport_id in list(SPORTS.keys()):
                #print('Checking %s' % SPORTS[sport_id]['name'])
                stats = getStats(drive, sport_id)
                if stats is None:
                    continue
                if len(SPORTS[sport_id]['data'].keys()) > 0:
                    # Compare data
                    for player_id in stats.keys():
                        player = stats[player_id]
                        if SPORTS[sport_id]['data'].get(player_id) is None:
                            continue
                        for opponent_id in player.keys():
                            opponent = player[opponent_id]
                            opponent_cache_exist = SPORTS[sport_id]['data'][player_id].get(
                                opponent_id) is not None
                            if opponent_cache_exist:
                                for attr in opponent.keys():
                                    if attr in closed_attrs:
                                        continue
                                    attr_cache_exist = SPORTS[sport_id]['data'][player_id].get(
                                        opponent_id).get(attr) is not None
                                    if opponent_cache_exist and attr_cache_exist and opponent[attr] != SPORTS[sport_id]['data'][player_id].get(opponent_id)[attr]:
                                        # Send Discord Message
                                        sendMessage(SPORTS[sport_id]['name'], opponent['name'], attr, SPORTS[sport_id]['data'][player_id].get(
                                            opponent_id).get(attr), opponent[attr], opponent_id, opponent['image'])

                SPORTS[sport_id]['data'] = stats
            print('[-] Iterations done : %s' % str(counter))
            counter += 1
            try:
                drive.close()
            except:
                pass
            sleep(SLEEP_TIMEOUT)
        except KeyboardInterrupt as k:
            print('[-] Stopped by User.')
            exit(0)
        except Exception as e:
            print(str(e)[:150])
