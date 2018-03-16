import os

class Config:
    """
    Contains miscellaneous configuration parameters.
    """

    # Root repository directory
    x = os.path.realpath(__file__)
    x = os.path.join(x, '../..')
    x = os.path.abspath(x)
    x = x.replace('\\', '/')
    root = x
    del x

    # Logging configuration dictionary
    log = {
        'version': 1,
        'formatters': {
            'simple': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(levelname)-8s %(module)-9s %(funcName)-16s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'formatter': 'simple',
                'filename': '{0}/app/log.log'.format(root),
                'mode': 'w'
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        },
    }