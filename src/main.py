"""
Copyright (c) 2023 Mjolnir2425

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import imaplib
import email
import os
import discord
import json
import sys
import random
import logging

from dataclasses import dataclass
from discord.ext import commands, tasks
from email.header import decode_header
from datetime import datetime

IMAP_SERVER = 'imap.example.com'
IMAP_PORT = 993

CHECK_INTERVAL_MINUTES = 1
CHANNELS_FP = 'data/channels.json'
EMAIL_FP = 'data/last_email_id.json'
QUOTES_FP = 'quotes.txt'

SEARCH_CRITERIA = '(FROM "example@example.com")'

EMAIL_ADDRESS = 'monitored.mail@example.com'
EMAIL_PASSWORD = 'your_app_password'
TOKEN = 'your_discord_token'

RED = discord.Color.from_rgb(242, 63, 67)
YELLOW = discord.Color.from_rgb(240, 178, 50)
GREEN = discord.Color.from_rgb(33, 155, 85)
BLUE = discord.Color.from_rgb(88, 101, 242)
ACCENT = discord.Color.from_rgb(194, 149, 76)

ENABLED_ATTACHMENTS = False

CHAR_LIMIT = 2000

logging.basicConfig(format='%(asctime)s %(message)s')
root = logging.getLogger()
root.setLevel(logging.DEBUG)


async def sendf(text: str,
                interaction: discord.Interaction,
                followup: bool = False,
                fail: bool = False,
                event: bool = False,
                warning: bool = False,
                info: bool = False,
                ephemeral: bool = True) -> None:
    embed = discord.Embed(
        title='Error' if fail else 'Event' if event else 'Warning' if warning else 'Info' if info else 'Success',
        description=text,
        color=RED if fail else ACCENT if event else YELLOW if warning else BLUE if info else GREEN
    )
    if followup:
        await interaction.followup.send(content='', embed=embed, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content='', embed=embed, ephemeral=ephemeral)


def get_channels() -> list[int]:
    with open(CHANNELS_FP, 'r') as file:
        channels = json.load(file)
    return channels


def delete_channel(channel_id: int) -> bool:
    channels = get_channels()
    if channel_id in channels:
        channels.remove(channel_id)
    else:
        return False

    with open(CHANNELS_FP, 'w') as file:
        json.dump(channels, file)
    return True


def add_channel(channel_id: int) -> bool:
    channels = get_channels()
    if channel_id in channels:
        return False
    
    channels.append(channel_id)

    with open(CHANNELS_FP, 'w') as file:
        json.dump(channels, file)
    return True


def get_random_quote() -> str:
    with open(QUOTES_FP, 'r', encoding='utf-8', errors='replace') as file:
        quotes = file.read().split('\n')
    return random.choice(quotes)


@dataclass
class Email:
    def __init__(self,
                 timestamp: datetime = None,
                 sender: str = None,
                 subject: str = None,
                 content: str = None,
                 attachment_paths: list[str] = None):
        self.timestamp = timestamp
        self.sender = sender
        self.subject = subject
        self.content = content
        self.attachment_paths = attachment_paths
        
    def __repr__(self):
        return f'Timestamp: {self.timestamp}, Sender: {self.sender}, Subject: {self.subject}'


class MainBot(commands.Bot):
    def __init__(self, command_prefix='!', intents=discord.Intents.default()):
        activity = discord.Activity(type=discord.ActivityType.watching, name='the Intranet')
        super().__init__(command_prefix=command_prefix, activity=activity, intents=intents)
        self.started = False
        self.mail = None
        with open(EMAIL_FP, 'r') as file:
            self.highest_email_id = json.load(file)
        
        @self.tree.command(name='ping', description='Pings the bot and gives you the ping, duh.')
        async def ping_callback(interaction: discord.Interaction):
            logging.info(f'Pinged by {interaction.user}')
            await sendf(f'Pong! Moj ping je { round(self.latency * 1000) } ms.', interaction, info=True)
        
        @self.tree.command(name='check', description='Check if announcements are being sent to this channel.')
        async def check_callback(interaction: discord.Interaction):
            try:
                channels = get_channels()
            except Exception as e:
                logging.error(e)
                await sendf('An error occurred.', interaction, fail=True)
                return
            
            if interaction.channel.id in channels:
                await sendf('Announcements **are sent** to this channel.', interaction, info=True)
            else:
                await sendf('Announcements **are not sent** to this channel.', interaction, info=True)
    
        @self.tree.command(name='start', description='Begin sending announcements to this channel.')
        async def start_callback(interaction: discord.Interaction):
            if not interaction.permissions.administrator:
                await sendf('You must be an admin to use this command.', interaction, fail=True)
                return
    
            try:
                success = add_channel(interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('An error occurred.', interaction, fail=True)
                return
            
            if success:
                await sendf('Announcements turned on.', interaction)
            else:
                await sendf('Announcements are already turned on.', interaction, warning=True)
    
        @self.tree.command(name='stop', description='Prestaje slati obavijesti u ovaj kanal.')
        async def stop_callback(interaction: discord.Interaction):
            if not interaction.permissions.administrator:
                await sendf('You must be an admin to use this command.', interaction, fail=True)
                return
            
            try:
                success = delete_channel(interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('An error occurred.', interaction, fail=True)
                return
            
            if success:
                await sendf('Announcements turned on.', interaction)
            else:
                await sendf('Announcements are already turned off.', interaction, warning=True)
                    
    def extract_email(self) -> list[Email]:
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        self.mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        self.mail.select("inbox")

        _, data = self.mail.search(None, SEARCH_CRITERIA)
        email_ids = data[0].split()

        mail_objs = []

        for email_id in email_ids:
            int_id = int(email_id)
            if int_id <= self.highest_email_id:
                continue
            self.highest_email_id = int_id
            with open(EMAIL_FP, 'w') as file:
                json.dump(self.highest_email_id, file)

            _, data = self.mail.fetch(email_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            mail_obj = Email()

            sender = msg['from'].strip('>').split('<')[-1]
            subject = msg['subject']
            timestamp = email.utils.parsedate_to_datetime(msg["date"])

            mail_obj.timestamp = timestamp
            mail_obj.sender = sender
            mail_obj.subject = subject
            content = ''
            attachment_paths = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type != 'text/plain':
                        continue
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            content = payload.decode()
                        else:
                            content = str(payload)

                    else:
                        filename = part.get_filename()
                        if filename:
                            filename = decode_header(filename)[0][0]
                            attachment_data = part.get_payload(decode=True)

                            if attachment_data:
                                save_path = os.path.join(os.getcwd(), 'Attachments', filename)
                                attachment_paths.append(save_path)
                                with open(save_path, "wb") as attachment_file:
                                    attachment_file.write(attachment_data)
            else:
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    content = payload.decode()
                else:
                    content = str(payload)

            if attachment_paths:
                mail_obj.attachment_paths = attachment_paths
            if content:
                mail_obj.content = content

            mail_objs.append(mail_obj)

        return mail_objs

    async def send_to_discord(self, mail: email, channel_ids: list[int]):
        logging.info(mail)
        full = f'{get_random_quote()}\n\n'
        full += f'Timestamp: {mail.timestamp}\n'
        full += f'Sender: **{mail.sender}**\n'
        full += f'Subject: **{mail.subject}**\n'
        full += f'\n{mail.content}'

        msg_components = []
        for i in range(len(full) // CHAR_LIMIT + 1):
            msg_components.append(full[i * CHAR_LIMIT: (i + 1) * CHAR_LIMIT])

        files = []
        if mail.attachment_paths and ENABLED_ATTACHMENTS:
            for path in mail.attachment_paths:
                filename = path.split('\\')[-1]
                fp = f'/Attachments/{filename}'
                files.append(discord.File(fp))
                os.remove(fp)

        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            try:
                for i in range(len(msg_components) - 1):
                    await channel.send(content=msg_components[i], suppress_embeds=True)
                await channel.send(content=msg_components[-1], files=files, suppress_embeds=True)
            except Exception as e:
                logging.error(e)
                continue

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_loop(self):
        try:
            emails = self.extract_email()
        except Exception as e:
            logging.error(e)
            return
        finally:
            if self.mail is not None:
                self.mail.logout()
        
        try:
            channel_ids = get_channels()
        except Exception as e:
            logging.error(e)
            return
        
        logging.info('Email recieved:')

        for mail in emails:
            await self.send_to_discord(mail, channel_ids)
                
    async def on_ready(self):
        if self.started:
            return
        
        self.started = True
        logging.info(f'Logged in as {self.user.name}')
        
        try:
            await self.tree.sync()
        except discord.app_commands.errors.CommandSyncFailure as e:
            logging.error(f'Failed to sync commands: {e}')
            logging.warn('Exiting')
            sys.exit()
        else:
            logging.info('Commands synced.')
        
        self.check_loop.start()
        logging.info('Started check loop.')
        

if __name__ == '__main__':
    bot = MainBot()
    bot.run(TOKEN)
