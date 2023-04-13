import os
import argparse
import logging

log = logging.getLogger(__file__)
log.setLevel(logging.INFO)
# Set up resources dir
cwd = os.path.dirname(__file__)
resource_dir = os.path.join(cwd, 'resources')
logging.info(f"Creating resources directory at {resource_dir}")
if not os.path.exists(resource_dir):
    os.mkdir(resource_dir)

