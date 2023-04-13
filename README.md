# Stupid Little E-Ink Weather Display 

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
