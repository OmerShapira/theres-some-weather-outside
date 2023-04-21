#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------ 

from typing import Dict, Optional, Iterable
import os
import traceback
import toml
import argparse

import requests
import dateutil.parser
import datetime

from weather_code import meteo2owm

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------------------ 

try:
    from waveshare_epd import epd7in5_V2
except ModuleNotFoundError as e:
    logging.info("Waveshare modules not found. Only dry run is possible")


# ------------------------------------------------------------------------------ 


class Display:

    w = 800
    h = 480

    def init_driver(self):
        self.epd = epd7in5_V2.EPD()
        self.w = self.epd.width
        self.h = self.epd.height

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

# ------------------------------------------------------------------------------ 

settings:dict = toml.load('settings.toml')

station = settings['api']['nws']['station']
grid_x = settings['api']['nws']['grid']['x']
grid_y = settings['api']['nws']['grid']['y']
WEATHER_API_NWS:str = f"https://api.weather.gov/gridpoints/{station}/{grid_x},{grid_y}/forecast/hourly"

lat =  settings['api']['openmeteo']['grid']['lat']
long = settings['api']['openmeteo']['grid']['long']
WEATHER_API_OPENMETEO:str = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&hourly=temperature_2m,relativehumidity_2m,apparent_temperature,precipitation_probability,precipitation,weathercode,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max&forecast_days=3&timezone=America%2FNew_York"

fonts = {}
for key, value in settings['text'].items():
    path = os.path.join(os.getcwd(), 'resources', value['source_file'])
    logging.debug(f"loading font at { path }")
    fonts[key] = ImageFont.truetype(path, value['size'])

graphics = {}
for key, value in settings['graphics'].items():
    path = os.path.join(os.getcwd(), 'resources', value['source_file'])
    logging.debug(f"loading graphic '{key}' at { path }")
    graphics[key] = Image.open(path)


ITEMS = settings['feed']['items']
MAX_INTERVAL = 3

colors = settings['color']

W,H = Display.w, Display.h
ICON_PAD_RATIO = 0.85
MARGIN_H = 30
MARGIN_V = 22
DIM_COL = (W - MARGIN_H * 2) // ITEMS
DIM_ICON = int(DIM_COL * ICON_PAD_RATIO)
DIM_COL_PAD = DIM_COL * (1 - ICON_PAD_RATIO) * 0.5
Y_HEADER = MARGIN_V + 40
Y_BASELINE = 130
Y_ICON = Y_BASELINE - 20
Y_LINE1 = int(Y_ICON + DIM_COL - DIM_COL_PAD) - 30
Y_LINE2 = Y_LINE1 + 20
Y_LINE3 = Y_LINE2 + 30
Y_LINE4 = Y_LINE3 + 30
TAB = DIM_COL / 10

Y_GRAPH_TOP = Y_LINE4 + 60
Y_GRAPH_BOTTOM = H - MARGIN_V

# ------------------------------------------------------------------------------ 

class RenderItem:
    def __init__(self, op, *args, **kwargs) -> None:
        self.op = op
        self.args = args
        self.kwargs = kwargs
    
    def exec(self):
        self.op(*self.args, **self.kwargs)

class RenderList:
    def __init__(self) -> None:
        self.queue = []

    def add(self, op, *args, **kwargs):
        self.queue.append(RenderItem(op, *args, **kwargs))
    
    def exec(self):
        for item in self.queue:
            item.exec()


class RenderContext:
    render_buffer: Optional[Image.Image]
    draw_buffer: Optional[ImageDraw.Draw]

    def line(self, *args, **kwargs):
        self.draw_buffer.line(*args, **kwargs)

    def regular_polygon(self, *args, **kwargs):
        self.draw_buffer.regular_polygon(*args, **kwargs)

    def polygon(self, *args, **kwargs):
        self.draw_buffer.polygon(*args, **kwargs)
    
    def text(self, *args, **kwargs):
        self.draw_buffer.text(*args, **kwargs)
    
    def paste(self, *args, **kwargs):
        self.render_buffer.paste(*args, **kwargs)

render = dict(
    gray=RenderList(),
    mono=RenderList()
)

ctx = RenderContext()    

# ------------------------------------------------------------------------------ 
class WeatherV2:
    """Uses the openmeteo API
    """
    headers = {
            'User-Agent': settings['app']['useragent']
        }

    def get_current_weather(self) -> Dict:
        r = requests.get(WEATHER_API_OPENMETEO, headers=self.headers)
        if not r.status_code == 200:
            logging.error(f"Weather API returned status {r.status_code}:{r.content}")
            return {}
        return r.json()

    def cache_and_scale_icons(self, icons:Iterable[str]) -> Dict[str, Image.Image]:

        def get_image_scaled(filename):
           b = os.path.join(os.getcwd(), 'cache', filename)
           img = Image.open(b)
           scaled = img.resize((DIM_ICON, DIM_ICON))
           return scaled

        self.icons =  {url:get_image_scaled(url) for url in icons}
        
        return self.icons


    def generate_message(self) -> Image:

        global ctx, render

        forecast = self.get_current_weather()
        daily = forecast['daily']
        hourly = forecast['hourly']

        days = [(dateutil.parser.parse(x), True) for x in daily['sunrise']]
        nights = [(dateutil.parser.parse(x), False) for x in daily['sunset']]
        sun = sorted(days + nights, key=lambda x: x[0])

        first_sample = 0
        time_now = datetime.datetime.now()
        for i, t in enumerate(hourly['time']):
            if dateutil.parser.parse(t) > time_now:
                first_sample = max(0, i - 1)
                break

        def lerp(a, b, x) -> int:
            return int(a + x * (b-a))

        interval = min(MAX_INTERVAL, len(hourly['time']) * 1.0 / ITEMS)
        samples = [i for i in range(first_sample, len(hourly['time']), interval)][:ITEMS]
        last_sample = samples[-1] + 1
        mintemp = min(hourly['temperature_2m'][first_sample:last_sample])
        maxtemp = max(hourly['temperature_2m'][first_sample:last_sample])

        def is_day(time) -> bool:
            # Silly search
            time = dateutil.parser.parse(time)
            for x in sun :
                day_flag = not x[1] 
                if time < x[0]:
                    break
            return day_flag

        def get_weathercode_url(code:int, time)->str: 
            day_flag = 'd' if is_day(time) else 'n'
            meteo = int(code)
            weathercode_url = f"{ meteo2owm.get(meteo,0) }{day_flag}.png"
            return weathercode_url

        weathercode_urls = {i:get_weathercode_url(hourly['weathercode'][i], hourly['time'][i]) for i in samples}
        icons = self.cache_and_scale_icons(set(weathercode_urls.values()))

        x = W // 2
        y = Y_HEADER

        t = dateutil.parser.parse(hourly['time'][first_sample])
        temptext = f"{t.hour:02}:00 : {hourly['temperature_2m'][first_sample]:.0f}°c"
        render['gray'].add(ctx.text,
                           (x,y),
                           temptext,
                           font=fonts['h1'], 
                           fill=colors['h1'], 
                           anchor='mm')

        # construct fine graph

        x_begin = MARGIN_H + (0 + 0.5) * DIM_COL
        x_end = MARGIN_H + (ITEMS - 1 + 0.5) * DIM_COL
        graph_sample_count = last_sample - first_sample

        temp_graph_points = []
        for i, sample in enumerate(range(first_sample, last_sample)):
            temp = hourly['temperature_2m'][sample]
            feels = hourly['temperature_2m'][sample]
            temp_norm = (temp - mintemp) / (maxtemp - mintemp)
            x_temp_point = lerp(x_begin, x_end, i/(graph_sample_count - 1))
            y_temp_point = lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 1-temp_norm)
            temp_graph_points.append((x_temp_point,  y_temp_point))

        midpoint = lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 0.5)
        render['gray'].add(ctx.line, 
                           temp_graph_points, 
                           fill=colors['h1'], 
                           width=3)
        render['mono'].add(ctx.line, 
                           [(temp_graph_points[0][0], midpoint), (temp_graph_points[-1][0],midpoint)], 
                           fill=colors['h2'], 
                           width=1)

        # Add Sampled Hours
        for i, sample in enumerate(samples):

            # Render Time
            t = dateutil.parser.parse(hourly['time'][sample])
            timetext = f"{t.hour:02}:00"
            x = int(MARGIN_H + i * DIM_COL)
            y = Y_LINE1
            render['mono'].add(ctx.text, 
                               (x,y), 
                               timetext, 
                               font=fonts['h3'], 
                               fill=colors['h2'],
                               anchor='lt')

            # Render Temperature
            temp = hourly['temperature_2m'][sample]
            feels = hourly['apparent_temperature'][sample]
            rh = hourly['relativehumidity_2m'][sample]
            temptext = f"{temp:.0f}°"
            feelstext = f"({feels:.0f}°), {rh:.0f}%"
            x = int(MARGIN_H + i * DIM_COL)
            y = Y_LINE2
            render['mono'].add(ctx.text,
                               (x,y), 
                               temptext, 
                               font=fonts['h2'], 
                               fill=colors['h2'],
                               anchor='lt')

            y = Y_LINE3
            # x = int(MARGIN_H + (i + 0.5) * DIM_COL)
            render['mono'].add(ctx.text,
                               (x,y), 
                               feelstext, 
                               font=fonts['h3'], 
                               fill=colors['h2'],
                               anchor='lt')

            # Render Wind and Rain
            wind_speed = hourly['windspeed_10m'][sample]
            pp = int(hourly['precipitation_probability'][sample])
            windtext = f"{wind_speed:.0f}km/h"
            raintext = f"{pp:.0f}%"

            x = int(MARGIN_H + i * DIM_COL)
            y = Y_LINE4
            dim = 20
            wind_small = graphics['wind'].resize((dim,dim))
            render['gray'].add(ctx.paste, 
                               wind_small, 
                               (x,y),
                               wind_small)
            render['mono'].add(ctx.text, 
                               (x + 2 * TAB ,y), 
                               windtext, 
                               font=fonts['h4'], 
                               fill=colors['h2'])
            if pp > 0:
                render['mono'].add(ctx.text,
                                   (x + TAB *5,y),
                                   '☔',
                                   font=fonts['h4_symbols'],
                                   fill=colors['h2'])
                render['mono'].add(ctx.text,
                                   (x + TAB * 7,y),
                                   raintext,
                                   font=fonts['h4'],
                                   fill=colors['h2'])

            # Render Icon
            x = int(MARGIN_H + i * DIM_COL) 
            y = Y_ICON
            code = hourly['weathercode'][sample]
            time = hourly['time'][sample]
            icon = icons[get_weathercode_url(code, time)]
            render['gray'].add(ctx.paste,
                               icon,
                               (x,y),
                               icon)

            # Render Graph Lines
            y = Y_LINE3 + 24
            x1 = MARGIN_H + (i + 0.5) * DIM_COL - DIM_ICON * 0.5
            x2 = MARGIN_H + (i + 0.5) * DIM_COL + DIM_ICON * 0.5
            xmid = (x1 + x2) * 0.5
            temp_norm = (temp - mintemp) / (maxtemp - mintemp)
            ygraph = int(lerp(Y_GRAPH_TOP, Y_GRAPH_BOTTOM, 1 - temp_norm))

            render['gray'].add(ctx.line,
                               (x1, y, x2, y),
                               fill=colors['h1'],
                               width=1)
            render['gray'].add(ctx.line,
                               (xmid, y + 10, xmid, ygraph - 8),
                               fill=colors['h1'],
                               width=1)
            #points
            render['mono'].add(ctx.regular_polygon,
                               (xmid, ygraph, 5),
                               n_sides=10,
                               fill=colors['h2'],
                               outline=colors['h2'])


def reset():
    Display.get().shutdown()

def main():

    parser = argparse.ArgumentParser("There's some weather outside")
    parser.add_argument('--simulate', action='store_true')

    args = parser.parse_args()

    weather = WeatherV2()
    weather.generate_message()
    
    ctx.render_buffer = Image.new('L', (W, H), colors['bg'])
    ctx.draw_buffer = ImageDraw.Draw(ctx.render_buffer)
    render['gray'].exec()

    ctx.render_buffer = ctx.render_buffer.convert(mode='1')
    ctx.draw_buffer = ImageDraw.Draw(ctx.render_buffer)
    render['mono'].exec()

    if settings['display']['rotate']:
        ctx.render_buffer = ctx.render_buffer.rotate(180)

    if args.simulate:
        ctx.render_buffer.save('preview.png', 'png')
        exit()

    disp = Display.get()
    disp.init()
    #disp.clear()
    buf = disp.epd.getbuffer(ctx.render_buffer)
    # time.sleep(5)
    logging.debug("display device")
    disp.epd.display(buf)
    # time.sleep(5)
    disp.sleep()
    Display.get().shutdown()

    try:
        pass

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
