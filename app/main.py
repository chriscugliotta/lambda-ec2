# External imports
import logging
import logging.config
import os
import time
import shutil

# Internal imports
from config import Config

# Logger
log = logging.getLogger()



if __name__ == '__main__':

    # Initialize logger
    logging.config.dictConfig(Config.log)
    log.info('Begin')

    # Verify input zip exists
    assert os.path.isfile(Config.root + '/app/input.zip'), 'Input zip does not exist!'
    log.info('Found input file')

    # Simulate processing time
    time.sleep(1)
    log.info('Processing complete')

    # Simulate an output file
    shutil.copy(Config.root + '/app/input.zip', Config.root + '/app/output.zip')
    log.info('Created output file')

    # Exit
    log.info('End')