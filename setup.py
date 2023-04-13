import os
import argparse
import logging
import requests
import toml

settings = toml.load('settings.toml')

logging.basicConfig(level=logging.INFO)
cwd = os.path.dirname(__file__)

# ------------------------------------------------------------------------------ 

errors: int=0
warnings: int=0

def error(*args, **kwargs) -> None:
    global errors
    logging.error(*args, **kwargs)
    errors += 1

def warning(*args, **kwargs) -> None:
    global warnings
    logging.warn(*args, **kwargs)
    warnings += 1

def info(*args, **kwargs) -> None:
    logging.info(*args, **kwargs)

# ------------------------------------------------------------------------------ 

info(f"Locating Dependencies")

try:
    from waveshare_epd import epd7in5_V2
    info("Found Waveshare display modules")
except ModuleNotFoundError as e:
    error("Waveshare modules not found. Only dry run is possible")

try:
    import PIL
    info("Found Pillow")
except ModuleNotFoundError as e:
    error("PIL / Pillow not found.")

# ------------------------------------------------------------------------------ 

try:
    info("Checking NWS settings")
    assert settings['nws']
    nws = settings['nws']
    assert nws['station']
    assert nws['grid']
    assert type(nws['grid']['x']) == int
    assert type(nws['grid']['y']) == int
except AssertionError:
    error("NWS settings and grid information not configured. See README.md for details")

# ------------------------------------------------------------------------------ 

# Set up resources dir
resource_dir = os.path.join(cwd, 'resources')
if not os.path.exists(resource_dir):
    try:
        info(f"Creating resources directory at {resource_dir}")
        os.mkdir(resource_dir)
    except IOError:
        error(f"Error creating resources directory at {resource_dir}. Do you have permissions?")

# Set up cache dir
cache_dir = os.path.join(cwd, 'cache')
if not os.path.exists(cache_dir):
    try:
        info(f"Creating cache directory at {cache_dir}")
        os.mkdir(cache_dir)
    except IOError:
        error(f"Error creating cache directory at {cache_dir}. Do you have permissions?")

# ------------------------------------------------------------------------------ 

# Get fonts
for k, v in settings['text'].items():
    filename = v['source_file']
    path = os.path.join(resource_dir, filename)

    # Don't download if it's already there
    if os.path.exists(path):
        info(f"File {filename} already exists for text type {k}. Skipping download")
        continue

    link = v.get('web_source', None)
    if not link:
        error(f"No web source exists for text type {k}. Check if you're missing {filename} ?")
        continue

    try:
        info(f"Downloading {link}")
        r = requests.get(link, allow_redirects=True) 
        with open(path, 'wb') as f:
            f.write(r.content)
    except e:
        error(f"Error while downloading {link} : {repr(e)}")
        

info(f"Completed with {errors} errors and {warnings} warnings.")
exit(errors > 0)

