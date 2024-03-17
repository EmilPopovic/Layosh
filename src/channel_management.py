import logging
import json

from load_config import CHANNELS_FP, DEFAULT_SUBSCRIPTIONS


def get_channels() -> dict:
    with open(CHANNELS_FP, 'r') as file:
        channels_dict = json.load(file)
    return channels_dict


def set_channels(channels: dict) -> None:
    with open(CHANNELS_FP, 'w') as file:
        json.dump(channels, file)


def get_channel_ids() -> list[int]:
    channels = get_channels()
    
    channels_int = []
    for channel_str in channels.keys():
        if channels[channel_str]['enabled']:
            channels_int.append(int(channel_str))
    
    return channels_int


def channel_enabled(channel_id: int) -> bool:
    channel_ids = get_channel_ids()

    if channel_ids == []:
        logging.debug('Channel not enabled, no channels.')
        return False
    elif channel_id in channel_ids:
        logging.debug('Channel enabled.')
        return True
    else:
        logging.debug('Channel not enabled, checked all.')
        return False


def delete_channel(channel_id: int) -> bool:
    channel_id_str = str(channel_id)
    channels = get_channels()

    if channel_id_str in channels.keys() and channels[channel_id_str]['enabled']:
        channels[channel_id_str]['enabled'] = False
        
        set_channels(channels)
        
        return True
    
    else:
        return False


def add_channel(channel_id: int) -> bool:
    channel_id_str = str(channel_id)
    channels = get_channels()
    
    if channel_id_str in channels.keys():
        if channels[channel_id_str]['enabled']:
            return False
        
        channels[channel_id_str]['enabled'] = True
    
    else:
        channel_to_add = {
            channel_id_str: {
                'enabled': True,
                'language': 'hrvatski',
                'sites': DEFAULT_SUBSCRIPTIONS,
                'whitelist': []
            }
        }
        channels.update(channel_to_add)

    set_channels(channels)
    
    return True
