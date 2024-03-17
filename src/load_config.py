import logging
import toml
import sys
import json
import discord

logging.debug('Completed imports, starting setup.')

CONFIG_FP = 'config/config.toml'

try:
    config = toml.load(CONFIG_FP)
except FileNotFoundError:
    logging.error(f'Failed loading {CONFIG_FP}, exiting.')
    sys.exit()

try:

    TEST_MODE = config['modes']['test_mode']

    # IMAP settings
    IMAP_SERVER = config['imap']['imap_server']
    IMAP_PORT   = config['imap']['imap_port']

    # filepath settings
    CHANNELS_FP      = config['filepaths']['channels_fp']
    EMAIL_FP         = config['filepaths']['email_fp']
    QUOTES_FP        = config['filepaths']['quotes_fp']
    SITES_FP         = config['filepaths']['sites_fp']
    SUBSCRIPTIONS_FP = config['filepaths']['subscriptions_fp']

    # auth settings
    EMAIL_ADDRESS  = config['auth']['email_address']
    EMAIL_PASSWORD = config['auth']['email_password']
    DISCORD_TOKEN  = config['auth']['test_discord_token'] if TEST_MODE else config['auth']['prod_discord_token']

    # color settings and converting to Disocrd format
    RED    = discord.Color.from_rgb(*config['colors']['red'])
    YELLOW = discord.Color.from_rgb(*config['colors']['yellow'])
    GREEN  = discord.Color.from_rgb(*config['colors']['green'])
    BLUE   = discord.Color.from_rgb(*config['colors']['blue'])
    ACCENT = discord.Color.from_rgb(*config['colors']['accent'])

    # feature enabling settings
    ENABLED_ATTACHMENTS    = config['features']['attachments']
    ENABLED_QUOTES         = config['features']['quotes']
    ENABLED_STRIP_END      = config['features']['strip_end']
    ENABLED_SHOW_SUBJECT   = config['features']['show_subject']
    ENABLED_SHOW_TIME      = config['features']['show_time']
    ENABLED_SHOW_SENDER    = config['features']['show_sender']
    ENABLED_SHOW_TLDR      = config['features']['show_tldr']
    ENABLED_CREATE_THREAD  = config['features']['create_thread']
    ENABLED_SHOW_THUMBNAIL = config['features']['show_thumbnail']
    ENABLED_SHOW_AUTHOR    = config['features']['show_author']
    ENABLED_SHOW_SITE      = config['features']['show_site']
    ENABLED_SHOW_PORTLET   = config['features']['show_portlet']
    ENABLED_SHOW_EVENT     = config['features']['show_event']

    # notable strings
    STRIP_END_STRING = config['strings']['strip_end_string']

    # miscelanious settings
    CHECK_INTERVAL_MINUTES = config['misc']['check_interval_minutes']
    CHAR_LIMIT             = config['misc']['char_limit']
    SEARCH_CRITERIA        = config['misc']['search_criteria']

    # setting up debug modes, always in debug mode if testing
    DEBUG_MODE = True  if TEST_MODE else config['debug']['debug_mode']
    QUIET_MODE = False if TEST_MODE else config['debug']['quiet_mode']

    # enable legacy mode to stop using some newer features
    LEGACY_MODE = config['modes']['legacy_mode']

    # OpenAI settings
    OPENAI_API_KEY = config['openai']['api_key']
    MODEL = config['openai']['model']
    SYSTEM_MESSAGE = config['openai']['system_message']
    MAX_TOKENS = config['openai']['max_tokens']
    TEMPERATURE = config['openai']['temperature']

    # subscribe a newly created channel to these announcements
    try:
        with open(SUBSCRIPTIONS_FP, 'r', encoding='utf-8') as file:
            default_subscriptions = json.load(file)
    except Exception as e:
        logging.error(f'Exiting. Failed loading {SUBSCRIPTIONS_FP}; {e}')
        sys.exit()

    DEFAULT_SUBSCRIPTIONS = default_subscriptions

    THUMBNAIL_URL = config['misc']['thumbnail_url']

    try:
        with open(SITES_FP, 'r', encoding='utf-8') as file:
            valid_sites: dict = json.load(file)
    except Exception as e:
        logging.error(f'Exiting. Failed loading {SITES_FP}; {e}')
        sys.exit()

    SITES = valid_sites
    SITE_NAMES = SITES.keys()

except KeyError as e:
    logging.error(f'Exiting. Failed to extract settings, check config files; {e}')
    sys.exit()

logging.debug('Completed setup.')
