import requests
import time
import xmltodict
import os
from datetime import datetime, timedelta
from pathlib import Path    
import json
import schedule


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

    dir_name = channel.replace(".", "_").replace("/", "_")
    today = datetime.now()
    d1 = today.strftime("%d-%m-%Y-%H-%M")
    file_name = dir_name + d1 + ".json"

    full_path = os.path.join("./results", dir_name)
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
    print(response.json())

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

    dir_name = ch_name.replace(".", "_").replace("/", "_").replace(" ", "-")
    today = datetime.now()
    d1 = today.strftime("%d-%m-%Y-%H-%M")
    file_name = dir_name + '' + d1 + ".json"

    full_path = os.path.join("./results", dir_name)
    Path(full_path).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(full_path, file_name), 'w') as fp:
        json.dump(new_json, fp, indent=3)

def fetch_all(query, min, source):
    for e in query:
        if source == 'IPTV':
            filter_by_channel(e)
        elif source == 'Vidio':
            fetch_vidio_epg(e)
        
    print("Awaiting for next fetch at " +(datetime.now() + timedelta(minutes=min)).strftime("%d-%m-%Y %H:%M"))

if __name__ == "__main__":
    # Load Conf files
    conf = json.load(open('conf.json'))

    scrape = True

    if scrape:
        fetch_all(conf['query'], conf['timer'], conf['source'])

        schedule.every(conf['timer']).minutes.do(fetch_all, conf['query'], conf['timer'], conf['source'])
        if conf['persistent']:
            while(True):
                schedule.run_pending()
                time.sleep(1)