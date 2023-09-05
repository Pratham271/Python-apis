import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask import jsonify, Flask
from flask_cors import CORS
from apscheduler.schedulers.background import BlockingScheduler
from flask_apscheduler import APScheduler
from datetime import datetime, time

csv = pd.read_csv("Indian_Cities_Database.csv")

app = Flask(__name__)
CORS(app)
sched = BlockingScheduler()

def scrape():
    URL = "https://news.google.com/search?q=Delhi|Agra&hl=en-IN&gl=IN&ceid=IN%3Aen"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    webpage = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "html.parser")
    data = soup.find_all(
        class_='MQsxIb xTewfe R7GTQ keNKEd j7vNaf Cc0Z5d EjqUne')
    records = []
    for _ in data:
        href = str(_.find('h3').find('a')['href'])
        href = href[1:]
        href = 'https://news.google.com' + href
        items = {
            'title': _.find('h3').find('a').getText(),
            'href': href
        }
        records.append(items)
    return records


def city():
    cities = csv['City'].tolist()
    return cities


def state():
    states = csv['State'].tolist()
    return states


def extractLocation(records, states=state(), cities=city()):
    records['location'] = {}
    for _ in states:
        if _ in records['title']:
            records['location'][_] = ['0', '0']
    for _ in cities:
        if _ in records['title']:
            records['location'][_] = ['0', '0']

    return records

def getLat(location):
    createIndex('state')
    lat= []
    try:
        lat = list(csv.loc[location, 'Lat'])[0]

    except:
        pass
    createIndex('city')
    try:
        lat = csv.loc[location, 'Lat']

    except:
        pass
    if lat :
        return lat

def getLong(location):
    createIndex('state')
    lon = []
    try:
        lon = list(csv.loc[location, 'Long'])[0]

    except:
        pass
    createIndex('city')
    try:
        lon = csv.loc[location, 'Long']
    except:
        pass
    if lon:
        return lon

def createIndex(which='state'):
    if (which == 'state'):
        indexState = state()
        csv.index = indexState
    if (which == 'city'):
        indexCity = city()
        csv.index = indexCity

newsdata = []
def populateData():
    try :
        data = scrape()
        locatedData = []
        for i in data:
            locatedData.append(extractLocation(i))
        for i in locatedData:
            for j in i['location'].keys():
                i['location'] = j
                i['latitude' ] = getLat(j)
                i['longitude'] = getLong(j)
            newsdata.append(i)
        return newsdata
    except Exception as e:
        print(e)


@app.route('/news')
def list_news():
    return jsonify(newsdata)

@app.route('/heatmap', methods=['GET'])
def heatmap():
    city_counts = {}
    for item in newsdata:
        if item['location']:
            city = item['location']
            if city in city_counts:
                city_counts[city] += 1
                city_counts['latitude'] = getLat(city)
                city_counts['longitude'] = getLong(city)
            else:
                city_counts[city] = 1
                city_counts['latitude'] = getLat(city)
                city_counts['longitude'] = getLong(city)
    return jsonify(city_counts)

if __name__ == "__main__":
    populateData()
    app.run()

