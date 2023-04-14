# Stupid Little E-Ink Weather Display 
![image of the thing](https://pbs.twimg.com/media/Ftm8qT0WABIxj3q?format=jpg&name=small)

Displays the weather on an e-ink panel. 
I don't even like this thing. I built it because a _certain_ major provider of mobile phones killed all weather services on its' operating system, then had major outages in their weather app, and I *really* needed to know if there's some fucking weather outside.

## Stuff Needed
1. A Raspberry Pi. This tutorial was written with a Pi Zero 2 W
2. A Waveshare E-Ink hat and display
3. A microSD card with the latest [ Raspian ](https://www.raspberrypi.com/software/).


## Setup
1. Install the waveshare e-ink library. [Full instructions here](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual). This step will also require you to install Pillow
```
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
sudo python setup.py install
```
2. Customize the `settings.toml` file. You'll need to find your [National Weather Service Tile](https://weather-gov.github.io/api/gridpoints)
3. Run this repo's setup: `python setup.py`. Setup will automatically check and download all missing files. 
4. If you're running this on an embedded device, you may want to add a cron job to run this once an hour. Your `crontab -e` should look something like this:
```
# run once an hour
0 * * * * python theres-some-weather-outside/weather.py > theres-some-weather-outside/weather.log
```


## Running
Running `python weather.py` will display the weather on your device.
If you just want to prototype but don't have a device handy, you can use `python weather.py --simulate`, which will dump the image onto `preview.png`