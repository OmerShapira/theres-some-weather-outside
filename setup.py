import os
import argparse
import logging
import requests
import toml

settings = toml.load('settings.toml')

logging.basicConfig(level=logging.INFO)
cwd = os.path.dirname(__file__)

# ------------------------------------------------------------------------------ 

errors : int = 0
warnings : int = 0
def error(*args, **kwargs) -> None:
    logging.error(*args, **kwargs)
    errors += 1

def warning(*args, **kwargs) -> None:
    logging.warn(*args, **kwargs)
    errors += 1

def info(*args, **kwargs) -> None:
    logging.info(*args, **kwargs)

# ------------------------------------------------------------------------------ 

# Set up resources dir
resource_dir = os.path.join(cwd, 'resources')
info(f"Creating resources directory at {resource_dir}")
if not os.path.exists(resource_dir):
    os.mkdir(resource_dir)

# Set up cache dir
cache_dir = os.path.join(cwd, 'cache')
info(f"Creating cache directory at {cache_dir}")
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

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

