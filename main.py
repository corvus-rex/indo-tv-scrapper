import requests
import time
import xmltodict
import os
from datetime import datetime, timedelta
from pathlib import Path    
import json
import schedule
from dotenv import load_dotenv


def get_variable(name: str, default_value: bool | None = None) -> bool:
    true_ = ('true', '1', 't')  # Add more entries if you want, like: `y`, `yes`, `on`, ...
    false_ = ('false', '0', 'f')  # Add more entries if you want, like: `n`, `no`, `off`, ...
    value: str | None = os.getenv(name, None)
    if value is None:
        if default_value is None:
            raise ValueError(f'Variable `{name}` not set!')
        else:
            value = str(default_value)
    if value.lower() not in true_ + false_:
        raise ValueError(f'Invalid value `{value}` for variable `{name}`')
    return value in true_

def filter_by_channel(channel):
    url = "https://iptv-org.github.io/epg/guides/id/vidio.com.xml"
    ts = time.time()
    print("Performing fetch request at " + str(ts) + "...")
    response = requests.get(url)
    data = xmltodict.parse(response.content)
    programs = data['tv']['programme']
    query = [channel]
    list = [d for d in programs if d['@channel'] in query]
    new_json = {
        'channel': channel,
        'fetched': ts,
        'source': 'IPTV',
        'programme': []
    }
    for e in list:
        new_json['programme'].append({
            'start': e['@start'],
            'stop': e['@stop'],
            'title': e['title']['#text']
        })

    dir_name = channel.replace(".", "-").replace("/", "-")
    today = datetime.now()
    d1 = today.strftime("%d-%m-%Y-%H-%M")
    file_name = dir_name + d1 + ".json"

    full_path = os.path.join(os.getenv("WRITE_DIR"), dir_name)
    Path(full_path).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(full_path, file_name), 'w') as fp:
        json.dump(new_json, fp, indent=3)

def fetch_vidio_epg(ch_name):
    sess = requests.session()
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    }

    # Fetch the X-API-KEY
    req = requests.Request("POST", 'https://www.vidio.com/auth', headers=header)
    prepped = req.prepare()
    response = sess.send(prepped)
    print(response.json()['api_key'])

    # Append the API Key to header
    header['X-API-KEY'] = response.json()['api_key']

    # Query Channel ID
    req = requests.Request("GET", "https://api.vidio.com/livestreamings?stream_type=tv_stream", headers=header)
    prepped = req.prepare()
    response = sess.send(prepped)
    print(response)
    channel_list = response.json()['data']
    id = ''
    for ch in channel_list:
        if ch_name in ch['attributes']['title']:
            id = ch['id']
            break
    if id == '':
        print('No channel name found')
        return

    # Perform GET REQUEST for the EPG schedule
    print("Channel ID ", id)
    req = requests.Request("GET", 'https://api.vidio.com/livestreamings/' + id + '/schedules?filter[date]=2023-04-05', headers=header)
    prepped = req.prepare()
    response = sess.send(prepped)

    # Write the EPG into JSON file
    ts = time.time()
    new_json = {
        'channel': ch_name,
        'fetched': ts,
        'source': 'Vidio API',
        'programme': []
    }
    for e in response.json()['data']:
        new_json['programme'].append({
            'title': e['attributes']['title'],
            'start': e['attributes']['start_time'],
            'stop': e['attributes']['end_time'],
            'description': e['attributes']['description']
        })

    dir_name = ch_name.replace(".", "-").replace("/", "-").replace(" ", "-")
    today = datetime.now()
    d1 = today.strftime("%d-%m-%Y-%H-%M")
    file_name = "Vidio_" + dir_name + '_' + d1 + ".json"

    full_path = os.path.join(os.getenv("WRITE_DIR"), dir_name)
    Path(full_path).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(full_path, file_name), 'w') as fp:
        json.dump(new_json, fp, indent=3)

    with open(os.path.join(full_path, "today.json"), 'w') as fp:
        json.dump(new_json, fp, indent=3)

def fetch_all(query, min, source):
    for e in query:
        if source == 'IPTV':
            filter_by_channel(e)
        elif source == 'Vidio':
            fetch_vidio_epg(e)
        time.sleep(3)
    print("Awaiting for next fetch at " +(datetime.now() + timedelta(minutes=min)).strftime("%d-%m-%Y %H:%M"))

if __name__ == "__main__":
    load_dotenv()
    # Load Conf files
    scrape = True

    query = os.getenv('QUERY').split(", ")
    print(type(int(os.getenv('TIMER'))))
    print(int(os.getenv('TIMER')))

    if scrape:
        fetch_all(query, int(os.getenv('TIMER')), os.getenv('SOURCE'))
        schedule.every(int(os.getenv('TIMER'))).minutes.do(fetch_all, query, int(os.getenv('TIMER')), os.getenv('SOURCE'))
        if get_variable('PERSISTENT'):
            while(True):
                schedule.run_pending()
                time.sleep(1)