import discord
import logging
import openai

from datetime import datetime

from channel_management import get_channels
from load_config import (
    ENABLED_SHOW_TLDR,
    ACCENT,
    THUMBNAIL_URL,
    MODEL,
    SYSTEM_MESSAGE,
    MAX_TOKENS,
    TEMPERATURE,
    OPENAI_API_KEY,
    ENABLED_SHOW_TIME,
    ENABLED_SHOW_THUMBNAIL,
    ENABLED_SHOW_AUTHOR,
    ENABLED_SHOW_SENDER,
    ENABLED_SHOW_SITE,
    ENABLED_SHOW_PORTLET,
    ENABLED_SHOW_EVENT
)

class Email:
    def __init__(
            self,
            timestamp: datetime = datetime.now(),
            sender: str = '',
            subject: str = '',
            content: str = '',
            tldr: str = None,
            attachment_paths: list[str] = [],
            files: list[discord.File] = [],
        ) -> None:
        self.timestamp = timestamp
        self.sender = sender
        self.subject = subject
        self.full_content = content
        self.attachment_paths = attachment_paths
        self.files = files

        self.content = '‎' + ''.join(content.split('Direktna poveznica:')[:-1])[2:]

        self.direct_link = content.split('Direktna poveznica:')[-1].strip().split('\n')[0].strip().split()[0]
        self.published_on = content.split('Objavljeno na:')[-1].strip().split('\n')[0].strip().split()[0]
        self.site = content.split('Naziv stranice:')[-1].strip().split('\n')[0].strip()
        self.portlet = content.split('Portlet:')[-1].strip().split('\n')[0].strip()
        self.user = content.split('Korisnik:')[-1].strip().split('\n')[0].strip()
        self.event = content.split('Događaj:')[-1].strip().split('\n')[0].strip()

        self.tldr = tldr

        if tldr is None and ENABLED_SHOW_TLDR:
            self.set_tldr()

    def __repr__(self) -> str:
        return f'Timestamp: {self.timestamp}, Sender: {self.sender}, Subject: {self.subject}, Site: {self.site}, Portlet: {self.portlet}'
    
    def get_embed(
            self,
            show_thumbnail: bool = ENABLED_SHOW_THUMBNAIL,
            show_author: bool = ENABLED_SHOW_AUTHOR,
            show_timestamp: bool = ENABLED_SHOW_TIME,
            show_sender: bool = ENABLED_SHOW_SENDER,
            show_site: bool = ENABLED_SHOW_SITE,
            show_portlet: bool = ENABLED_SHOW_PORTLET,
            show_event: bool = ENABLED_SHOW_EVENT,
            show_tldr: bool = ENABLED_SHOW_TLDR,
            description: str = ''
        ) -> discord.Embed:
        embed = discord.Embed(title=self.subject, description=description, color=ACCENT)
        
        if show_thumbnail:
            embed.set_thumbnail(url=THUMBNAIL_URL)
        if show_author:
            embed.set_author(name=self.user, url=None, icon_url=None)
        if show_timestamp:
            embed.add_field(name='Vrijeme', value=self.timestamp, inline=False)
        if show_sender:
            embed.add_field(name='Pošiljatelj', value=self.sender, inline=False)
        if show_site:
            embed.add_field(name='Naziv stranice', value=self.site, inline=True)
        if show_portlet:
            embed.add_field(name='Portlet', value=self.portlet, inline=True)
        if show_event:
            embed.add_field(name='Događaj', value=self.event, inline=True)
        if show_tldr:
            embed.add_field(name='Sažetak', value=self.tldr, inline=False)
            embed.set_footer(
                text='Sažetak je generirao ChatGPT i možda nije u potpunosti točan.',
                icon_url='https://brandlogovector.com/wp-content/uploads/2023/01/ChatGPT-Icon-Logo-PNG.png'
            )

        return embed
    
    def get_buttons(self) -> list[discord.ui.Button]:
        buttons: list
        try:
            buttons = [
                discord.ui.Button(style=discord.ButtonStyle.link, url=self.direct_link, label='Direktna poveznica'),
                discord.ui.Button(style=discord.ButtonStyle.link, url=self.published_on, label='Objavljeno na'),
            ]
        except Exception as e:
            buttons = []
        return buttons
    
    def is_for_channel(self, channel_id: int) -> bool:
        logging.debug(f'Checking if mail is for {channel_id}; site: {self.site}; portlet: {self.portlet}')

        channel_id_str = str(channel_id)
        channels = get_channels()

        if channel_id_str not in channels.keys():
            logging.debug(f'Mail is not for {channel_id}')
            return False
        
        sites = channels[channel_id_str]['sites']
        for site in sites.keys():
            if site == self.site:
                for portlet in channels[channel_id_str]['sites'][site]['portlets']:
                    if portlet == self.portlet:
                        logging.debug(f'Mail is for {channel_id}')
                        return True
        
        logging.debug(f'Mail is not for {channel_id}')
        return False
    
    def set_tldr(self):
        if self.tldr:
            return
        
        openai.api_key = OPENAI_API_KEY
        
        messages = [
            {'role': 'system', 'content': SYSTEM_MESSAGE},
            {'role': 'user', 'content': self.content}
        ]
        
        try:
            logging.debug('Getting summary from OpenAI.')
            chat = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
        except openai.error.InvalidRequestError as e:
            logging.error(f'openai.error.InvalidRequestError; {e}')
        except openai.error.AuthenticationError as e:
            logging.error(f'openai.error.AuthenticationError; {e}')
        except openai.error.APIConnectionError as e:
            logging.error(f'openai.error.APIConnectionError; {e}')
        except openai.error.RateLimitError as e:
            logging.error(f'openai.error.RateLimitError; {e}')
        except openai.error.OpenAIError as e:
            logging.error(f'openai.error.OpenAIError; {e}')
        else:
            self.tldr = chat.choices[0].message.content
            logging.info('Successfully got summary from OpenAI')
