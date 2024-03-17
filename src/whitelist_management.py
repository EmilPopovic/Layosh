from channel_management import get_channels, set_channels


def get_whitelist(channel_id: int) -> list[int]:
    try:
        retval = get_channels()[str(channel_id)]['whitelist']
    except KeyError:
        retval = []
    return retval


def add_to_whitelist(user_id: int, channel_id: int) -> (bool | None):
    try:
        channel_whitelist = get_whitelist(channel_id)
    except KeyError:
        return None

    if user_id in channel_whitelist:
        return False
    
    channels = get_channels()
    channels[str(channel_id)]['whitelist'].append(user_id)
    set_channels(channels)

    return True


def remove_from_whitelist(user_id: int, channel_id: int) -> (bool | None):
    try:
        channel_whitelist = get_whitelist(channel_id)
    except KeyError:
        return None
    
    if user_id not in channel_whitelist:
        return False
    
    channels = get_channels()
    channels[str(channel_id)]['whitelist'].remove(user_id)
    set_channels(channels)

    return True
