import random
import quopri
import logging

from load_config import QUOTES_FP, DEBUG_MODE, QUIET_MODE


def get_random_quote() -> str:
    with open(QUOTES_FP, 'r', encoding='utf-8', errors='replace') as file:
        quotes = file.read().split('\n')
    return random.choice(quotes)


def quopri_decode(text: str) -> str:
    logging.debug('Quopri decoding string.')
    parts = text.split("=?UTF-8?")

    decoded_text = ""
    for part in parts:
        if part:
            decoded_part = quopri.decodestring(part.encode("utf-8")).decode("utf-8")
            decoded_text += decoded_part

    decoded_text.replace('Q?', '')
    decoded_text.replace('?', '')
    decoded_text.replace(' ', '')
    decoded_text.replace('_', ' ')

    return decoded_text


def logging_setup(debug: bool = DEBUG_MODE, quiet: bool = QUIET_MODE) -> None:
    """
    Sets up logging.
    
    Three modes are available:
    - Default logging
    - Debug mode: everything is logged
    - Quiet mode: only errors are logged
    """
    logging.basicConfig(format='%(asctime)s %(message)s')
    root = logging.getLogger()
    
    if debug and quiet:
        logging.warning('Both debug mode and quiet mode set.\nUsing debug mode.')
        root.setLevel(logging.DEBUG)
    elif quiet:
        root.setLevel(logging.ERROR)
    elif debug:
        logging.info('Using debug mode.')
        root.setLevel(logging.DEBUG)
