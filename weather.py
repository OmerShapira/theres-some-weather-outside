#!/usr/bin/python
# -*- coding:utf-8 -*-
from typing import Dict
import sys
import os
import logging
import time
import traceback
import math
import toml

import requests
import dateutil.parser
from urllib.parse import urlencode, urlparse, urlunparse
from io import BytesIO

# ------------------------------------------------------------------------------ 

# picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
# libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')

# if os.path.exists(libdir):
#    sys.path.append(libdir)
from waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont

# ------------------------------------------------------------------------------ 

logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------ 

settings:dict = toml.load('settings.toml')
station = settings['nws']['station']
grid_x = settings['nws']['grid']['x']
grid_y = settings['nws']['grid']['y']

WEATHER_API:str = f"https://api.weather.gov/gridpoints/{station}/{grid_x},{grid_y}/forecast/hourly"

fonts = {}
for key, value in settings['text'].items():
    path = os.path.join(os.getcwd(), 'resources', value['source_file'])
    logging.debug(f"loading font at { path= }")
    fonts[key] = ImageFont.truetype(path, value['size'])


ITEMS = 7
MAX_INTERVAL = 3
MARGIN = 30

colors = settings['color']

ICON_PAD_RATIO = 0.85

# ------------------------------------------------------------------------------ 

class Weather:
    headers = {
        'User-Agent': 'Weather Panel By Omershapira'
        }

    def get_current_weather(self) -> Dict:
        r = requests.get(WEATHER_API, headers=self.headers)
        if not r.status_code == 200:
            logging.error(f"Weather API returned status {r.status_code}:{r.content}")
            return {}
        return r.json()['properties']['periods']

    def generate_message(self):
        disp = Display.get()

        periods = self.get_current_weather()
        # 'number', 'name', 'startTime', 'endTime', 'isDaytime', 'temperature', 'temperatureUnit', 'temperatureTrend', 'probabilityOfPrecipitation', 'dewpoint', 'relativeHumidity', 'windSpeed', 'windDirection', 'icon', 'shortForecast', 'detailedForecast'
        w,h = disp.epd.width, disp.epd.height
        img = Image.new('L', (w, h), colors['bg'])
        draw = ImageDraw.Draw(img)


        icon_dim = int(((w - MARGIN * 2) // ITEMS) * ICON_PAD_RATIO)

        def get_image_scaled(url):
           url_small = f"{url.split(',')[0]}?size=small"
           r = requests.get(url_small)
           b = BytesIO(r.content)
           img = Image.open(b)
           scaled = img.resize((icon_dim, icon_dim))
           return scaled

        def ftoc(f) -> int:
            f = int(f)
            return int((f-32)*5/9)

        def lerp(a, b, x) -> int:
            return int(a + x * (b-a))

        #TODO : filter icons
        icons_to_download = set([p['icon'] for p in periods])
        icons = { addr:get_image_scaled(addr) for addr in icons_to_download }

        Y_HEADER = 65
        Y_BASELINE = 130
        Y_ICON = Y_BASELINE
        Y_TIME = Y_ICON + 100
        Y_TEMP = Y_TIME + 24
        Y_WIND = Y_TEMP + 24

        Y_GRAPH_TOP = Y_WIND + 45
        Y_GRAPH_BOTTOM = Y_GRAPH_TOP + 150

        now = periods[0]
        x = w // 2
        y = Y_HEADER
        t = dateutil.parser.parse(now['startTime'])
        temptext = f"{t.hour:02}:00 : {ftoc(now['temperature'])} c"
        draw.text((x,y), temptext, font=fonts['h1'], fill=colors['h1'], anchor='mm')

        mintemp = min([ftoc(x['temperature']) for x in periods])
        maxtemp = max([ftoc(x['temperature']) for x in periods])

        interval = min(MAX_INTERVAL, len(periods) * 1.0 / ITEMS)
        samples = [math.floor(i * interval) for i in range(ITEMS)]

        # construct fine graph

        COL_DIM = (w - MARGIN * 2) // ITEMS
        X_BEGIN = MARGIN + (0 + 0.5) * COL_DIM
        X_END = MARGIN + (ITEMS - 1 + 0.5) * COL_DIM
        graph_sample_count = min(samples[-1] + 1, len(periods)) # need to get the last sample in

        graph_points = []
        for i in range(graph_sample_count):
            temp = ftoc(periods[i]['temperature'])
            temp_norm = (temp - mintemp) / (maxtemp - mintemp)
            X_TEMP_POINT = lerp(X_BEGIN, X_END, i/(graph_sample_count - 1))
            Y_TEMP_POINT = lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 1-temp_norm)
            graph_points.append((X_TEMP_POINT,  Y_TEMP_POINT))

        draw.line(graph_points, fill=colors['h1'], width=5)
        midpoint = lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 0.5)
        draw.line([(graph_points[0][0], midpoint), (graph_points[-1][0],midpoint)], fill=colors['h2'], width=1)

        for i, sample_idx in enumerate(samples):

            period = periods[sample_idx]

            t = dateutil.parser.parse(period['startTime'])
            timetext = f"{t.hour:02}:00"
            x = int(MARGIN + i * COL_DIM)
            y = Y_TIME
            draw.text((x,y), timetext, font=fonts['h3'], fill=colors['h2'])

            temp = ftoc(period['temperature'])
            temptext = f"{temp} c"
            x = int(MARGIN + i * COL_DIM)
            y = Y_TEMP
            draw.text((x,y), temptext, font=fonts['h2'], fill=colors['h2'])

            windtext = f"{period['windSpeed']}"
            x = int(MARGIN + i * COL_DIM)
            y = Y_WIND
            draw.text((x,y), windtext, font=fonts['h4'], fill=colors['h2'])

            x = int(MARGIN + i * COL_DIM) 
            y = Y_ICON
            img.paste(icons[period['icon']],(x,y)) 

            y = Y_WIND + 24
            x1 = MARGIN + (i + 0.5) * COL_DIM - icon_dim * 0.5
            x2 = MARGIN + (i + 0.5) * COL_DIM + icon_dim * 0.5
            xmid = (x1 + x2) * 0.5
            temp_norm = (temp - mintemp) / (maxtemp - mintemp)
            ygraph = lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 1-temp_norm)

            draw.line((x1, y, x2, y), fill=colors['h1'], width=1)
            draw.line((xmid, y + 10, xmid, ygraph-10), fill=colors['h1'], width=1)




        bw = img.convert(mode='1')
        disp.init()
        #disp.clear()
        buf = disp.epd.getbuffer(bw)
        # time.sleep(5)
        logging.debug("display device")
        disp.epd.display(buf)
        # time.sleep(5)
        disp.sleep()


class Display:


    def init_driver(self):
        self.epd = epd7in5_V2.EPD()

    def init(self):
        logging.debug("init device")
        self.epd.init()

    def clear(self):
        logging.debug("clear device")
        self.epd.Clear()

    def sleep(self):
        logging.debug("sleep device")
        self.epd.sleep()

    def shutdown(self):
        self.sleep()
        epd7in5_V2.epdconfig.module_exit()

    @classmethod
    def get(cls):
        if not hasattr(cls, '_i'):
            setattr(cls, '_i', cls.__new__(cls))
            cls._i.init_driver()
        return cls._i


def reset():
    Display.get().shutdown()

def main():

    print("Fetching weather")
    w = Weather()
    # print(w.get_current_weather())
    w.generate_message()
    time.sleep(30)
    Display.get().shutdown()
    # print(f"{Display.get().epd.width=}")
    # print(f"{Display.get().epd.height=}")

    try:
        pass

        #with DisplayContext() as d:
        #    Himage = Image.new('1', (d.epd.width, d.epd.height), 255)  # 255: clear the frame
        #    draw = ImageDraw.Draw(Himage)
        #    draw.text((10, 0), 'hello Nitzu', font = font24, fill = 0)
        #    draw.text((10, 20), 'feels like: Nitzu', font = font24, fill = 0)
        #    d.epd.display(d.epd.getbuffer(Himage))

        #time.sleep(5)

        #with DisplayContext as d:
        #    pass
    except IOError as e:
        logging.info(e)
        reset()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupted")
        reset()
    finally:
        exit()



if __name__ == '__main__':
    main()
