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

def fetch_all(query, min):
    for e in query:
        filter_by_channel(e)
    print("Awaiting for next fetch at " +(datetime.now() + timedelta(minutes=min)).strftime("%d-%m-%Y %H:%M"))

if __name__ == "__main__":
    # Load Conf files
    conf = json.load(open('conf.json'))

    fetch_all(conf['query'], conf['timer'])

    schedule.every(conf['timer']).minutes.do(fetch_all, conf['query'], conf['timer'])
    if conf['persistent']:
        while(True):
            schedule.run_pending()
            time.sleep(1)