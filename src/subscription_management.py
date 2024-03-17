import logging

from channel_management import get_channels, set_channels
from load_config import SITES


def all_site_portlets(site: str) -> list[str]:
    portlets = []
    try:
        portlets = SITES[site].keys()
    except KeyError:
        pass
    return portlets


def channel_sites(channel_id: int) -> list[str]:
    try:
        sites = get_channels()[str(channel_id)]['sites'].keys()
    except KeyError:
        sites = []
    return sites 


def channel_site_portlets(channel_id: int, site: str) -> list[str]:
    try:
        portlets = get_channels()[str(channel_id)]['sites'][site]['portlets']
    except KeyError:
        portlets = []
    return portlets


def add_site(channel_id: int, site: str) -> bool:
    channel_id_str = str(channel_id)
    channels = get_channels()

    if site in channel_sites(channel_id):
        return False
    
    channels[channel_id_str]['sites'].update({site: {'portlets': []}})
    set_channels(channels)

    logging.info(f'Site {site} added to {channel_id}')

    return True


def remove_site(channel_id: int, site: str) -> bool:
    channel_id_str = str(channel_id)
    channels = get_channels()

    if site not in channel_sites(channel_id):
        return False
    
    channels[channel_id_str]['sites'].pop(site)
    set_channels(channels)

    logging.info(f'Site {site} removed from {channel_id}')

    return True


def add_portlet(channel_id: int, site: str, portlet: str) -> (bool | None):
    if site not in channel_sites(channel_id):
        return None

    channel_id_str = str(channel_id)
    channels = get_channels()

    site_portlets = channels[channel_id_str]['sites'][site]['portlets']

    if portlet in site_portlets:
        return False
    
    channels[channel_id_str]['sites'][site]['portlets'].append(portlet)
    set_channels(channels)

    logging.info(f'Portlet {portlet} added to site {site} for {channel_id}')

    return True


def remove_portlet(channel_id: int, site: str, portlet: str) -> (bool | None):
    if site not in channel_sites(channel_id):
        return None
    
    channel_id_str = str(channel_id)
    channels = get_channels()

    site_portlets = channels[channel_id_str]['sites'][site]['portlets']

    if portlet not in site_portlets:
        return False
    
    channels[channel_id_str]['sites'][site]['portlets'].remove(portlet)
    set_channels(channels)

    logging.info(f'Portlet {portlet} removed from {site} for {channel_id}')

    return True
