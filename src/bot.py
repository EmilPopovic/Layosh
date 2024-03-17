import discord
import logging
import sys
import json
import imaplib
import os
import email

from discord import app_commands
from discord.ext import commands, tasks
from email.header import decode_header

from load_config import EMAIL_FP, SITE_NAMES, IMAP_PORT, IMAP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD, SEARCH_CRITERIA, CHECK_INTERVAL_MINUTES, ENABLED_CREATE_THREAD, ENABLED_ATTACHMENTS, CHAR_LIMIT
from message_sender import sendf, send_not_implemented
from channel_management import get_channels, get_channel_ids, add_channel, delete_channel, channel_enabled
from subscription_management import add_site, remove_site, add_portlet, remove_portlet, all_site_portlets, channel_sites, channel_site_portlets
from whitelist_management import get_whitelist, add_to_whitelist, remove_from_whitelist
from class_email import Email
from util import get_random_quote

class Bot(commands.Bot):
    def __init__(
            self,
            command_prefix: str = '!',
            activity: discord.Activity = discord.Activity(type=discord.ActivityType.watching, name='the Intranet'),
            intents: discord.Intents = discord.Intents.default()
        ) -> None:
        super().__init__(command_prefix=command_prefix, activity=activity, intents=intents)
        
        self.started = False
        self.mail = None

        self.command_names: list[str] = []
        
        try:
            with open(EMAIL_FP, 'r') as file:
                self.highest_email_id = json.load(file)
        except FileNotFoundError:
            logging.error(f"{EMAIL_FP} not found.")
            sys.exit()

        logging.debug('Bot constructed.')
        
        @self.tree.command(name='ping', description='Pinga Lajoša i daje ti ping, duh.')
        async def ping_callback(interaction: discord.Interaction) -> None:
            logging.info(f'Pinged by {interaction.user}')

            await sendf(f'Pong! Moj ping je { round(self.latency * 1000) } ms.', interaction, info=True)

        @self.tree.command(name='help', description='Prikazuje uputstva.')
        @app_commands.describe(naredba='Naredba s kojom trebaš pomoć.')
        async def help_callback(interaction:discord.Interaction, naredba: str = '') -> None:
            logging.info(f'{interaction.user} used /help')

            # todo finish
            
            command = naredba

            if command != '' and command not in self.command_names:
                await sendf(f'`/{command}` is not a valid command.', interaction, fail=True)
            if command:
                await send_not_implemented(interaction)
            else:
                await send_not_implemented(interaction)
        
        @self.tree.command(name='provjeri', description='Provjerava šalju li se obavijesti u ovaj kanal.')
        async def check_callback(interaction: discord.Interaction) -> None:
            logging.info(f'{interaction.user} used /provjeri')

            try:
                channel_dict = get_channels()[str(interaction.channel.id)]
            except KeyError:
                await sendf('Obavijesti se ne šalju u ovaj kanal.', interaction, info=True)
                return

            try:
                channels = get_channel_ids()

                content = ''
                for site in channel_dict['sites'].keys():
                    portlets = channel_dict['sites'][site]['portlets']
                    portlets_display = '\n- ' + '\n- '.join(portlets)
                    if portlets_display == '\n- ':
                        portlets_display = 'Nema portleta.'
                    content += f'**{site}**: {portlets_display}\n'
            
            except Exception as e:
                logging.error(e)
                await sendf('An error occurred.', interaction, fail=True)
                return
        
            if interaction.channel.id in channels:
                if content:
                    await sendf(f'Sljedeće se obavijesti šalju u ovaj kanal:\n\n{content}', interaction, info=True)
                else:
                    await sendf('Ovaj je kanal registriran, ali nema pretplata. Dodaj pretplate koristeći `/dodaj-stranicu` i `dodaj-portlet`.', interaction, info=True)
            else:
                await sendf('Obavijesti se ne šalju u ovaj kanal.', interaction, info=True)
    
        @self.tree.command(name='start', description='Počni slati obavijesti u ovaj kanal.')
        async def start_callback(interaction: discord.Interaction) -> None:
            logging.info(f'{interaction.user} used /start')
            
            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
    
            try:
                success = add_channel(interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success:
                await sendf('Slanje obavijesti uključeno.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf('Slanje obavijesti već je bilo uključeno.', interaction, warning=True)
    
        @self.tree.command(name='stop', description='Prestani slati obavijesti u ovaj kanal.')
        async def stop_callback(interaction: discord.Interaction) -> None:
            logging.info(f'{interaction.user} used /stop')
            
            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            try:
                success = delete_channel(interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success:
                await sendf('Slanje obavijesti isključeno.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf('Slanje obavijesti već je bilo isključeno.', interaction, warning=True)

        @self.tree.command(name='dodaj-stranicu', description='Pretplati kanal na stranicu.')
        @app_commands.describe(stranica='Stranica na koju se želiš pretplatiti.')
        async def add_site_callback(interaction: discord.Interaction, stranica: str) -> None:
            logging.info(f'{interaction.user} used /dodaj-stranicu')
            
            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio pretplate.', interaction, warning=True)
                logging.debug('Channel not enabled, skipping command.')
                return
            
            site = stranica
            
            if site not in SITE_NAMES:
                await sendf(f'Stranica `{site}` ne postoji, odaberi stranicu s popisa.', interaction, fail=True)
                return
            
            try:
                success = add_site(interaction.channel.id, site)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success:
                await sendf(f'Kanal pretplaćen na stranicu `{site}`.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf(f'Kanal je već pretplaćen na stranicu `{site}`.', interaction, warning=True)

        @self.tree.command(name='ukloni-stranicu', description='Prekini pretplatu na stranicu.')
        @app_commands.describe(stranica='Stranica čiju pretplatu želiš prekinuti.')
        async def remove_site_callback(interaction: discord.Interaction, stranica: str) -> None:
            logging.info(f'{interaction.user} used /ukloni-stranicu')
            
            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio pretplate.', interaction, warning=True)
                return
            
            site = stranica

            try:
                success = remove_site(interaction.channel.id, site)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success:
                await sendf(f'Pretplata na stranicu `{site}` prekinuta.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf(f'Nije bilo pretplate na stranicu `{site}`.', interaction, warning=True)

        @self.tree.command(name='dodaj-portlet', description='Pretplati se na portlet stranice.')
        @app_commands.describe(stranica='Stranica čiji portlet želiš dodati.', portlet='Portlet na koji se želiš pretplatiti.')
        async def add_portlet_callback(interaction: discord.Interaction, stranica: str, portlet: str) -> None:
            logging.info(f'{interaction.user} used /dodaj-portlet')
            
            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio pretplate.', interaction, warning=True)
                return
            
            site = stranica

            if site not in SITE_NAMES:
                await sendf(f'Stranica `{site}` ne postoji, odaberi stranicu s popisa.', interaction, fail=True)
                return

            if portlet not in all_site_portlets(site):
                await sendf(f'Portlet `{portlet}` ne postoji, odaberi portlet s popisa.', interaction, fail=True)
                return

            try:
                success = add_portlet(interaction.channel.id, site, portlet)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success is None:
                await sendf(f'Stranica `{site}` ne postoji, odaberi stranicu s popisa.', interaction, fail=True)
            elif success:
                await sendf(f'Dodana pretplata na portlet `{portlet}` stranice `{site}`.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf(f'Kanal je već pretplaćen na portlet `{portlet}` stranice `{site}`.', interaction, warning=True)

        @self.tree.command(name='ukloni-portlet', description='Prekini pretplatu na portlet stranice.')
        @app_commands.describe(stranica='Stranica čiji portlet želiš maknuti.', portlet='Portlet čiju pretplatu želiš prekinuti.')
        async def remove_portlet_callback(interaction: discord.Interaction, stranica: str, portlet: str) -> None:
            logging.info(f'{interaction.user} used /ukloni-portlet')

            if not interaction.permissions.administrator and interaction.user.id not in get_whitelist(interaction.channel.id):
                await sendf('Moraš biti admin ili menadžer kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio pretplate.', interaction, warning=True)
                return
            
            site = stranica
            
            try:
                success = remove_portlet(interaction.channel.id, site, portlet)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success is None:
                await sendf(f'Stranica `{site}` ne postoji, odaberi stranicu s popisa.', interaction, fail=True)
            elif success:
                await sendf(f'Prekinuta pretpata na portlet `{portlet}`.', interaction, ephemeral=False, author=interaction.user)
            else:
                await sendf(f'Nije bilo pretplate na portlet `{portlet}`.', interaction, warning=True)

        @self.tree.command(name='dodaj-menadžera', description='Menadžer može u kanalu koristiti sve naredbe osim onih za dodavanje i uklanjanje menadžera.')
        @app_commands.describe(korisnik='Korisnik koji će postati menadžer.')
        async def add_manager_callback(interaction: discord.Interaction, korisnik: discord.User) -> None:
            logging.info(f'{interaction.user} used /dodaj-menadžera')

            if not interaction.permissions.administrator:
                await sendf('Moraš biti admin kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocked')
                return
            
            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio menadžere.', warning=True)
                return

            manager = korisnik

            try:
                success = add_to_whitelist(manager.id, interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)
                return
            
            if success is None:
                await sendf(f'Nešto si krivo upisao, pokušaj ponovno.', interaction, fail=True)
            elif success:
                await sendf(f'`{manager.name}` je sada menadžer ovog kanala.', interaction, ephemeral=False)
            else:
                await sendf(f'`{manager.name}` je već menadžer ovog kanala.', interaction, warning=True)

        @self.tree.command(name='ukloni-menadžera', description='Ukloni korisnika s popisa menadžera za kanal.')
        @app_commands.describe(korisnik='Korisnik koji će izgubiti titulu menadžera.')
        async def remove_manager_callback(interaction: discord.Interaction, korisnik: discord.User) -> None:
            logging.info(f'{interaction.user} used /ukloni-menadžera')

            if not interaction.permissions.administrator:
                await sendf('Moraš biti admin kako bi koristio ovu naredbu.', interaction, warning=True)
                logging.info(f'{interaction.user} was not admin, command blocekd')
                return

            if not channel_enabled(interaction.channel.id):
                await sendf('Moraš registrirati kanal koristeći `/start` kako bi uredio menadžere.', warning=True)
                return
            
            manager = korisnik

            try:
                success = remove_from_whitelist(manager.id, interaction.channel.id)
            except Exception as e:
                logging.error(e)
                await sendf('Dogodila se pogreška.', interaction, fail=True)

            if success is None:
                await sendf(f'Nešto si krivo upisao, pokušaj ponovno.', interaction, fail=True)
            elif success:
                await sendf(f'`{manager.name}` više nije menadžer ovog kanala.', interaction, ephemeral=False)
            else:
                await sendf(f'`{manager.name}` već nije menadžer ovog kanala.', interaction, warning=True)

        # autocomplete functions

        def make_choices(current: str, options: list[str]) -> list[app_commands.Choice]:
            lst = []
            for option in options:
                if option.lower().startswith(current.lower()):
                    choice_obj = app_commands.Choice(name=option, value=option)
                    lst.append(choice_obj)
            return lst
        
        @help_callback.autocomplete(name='naredba')
        async def help_callback_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
            return make_choices(current=current, options=self.command_names)
        
        @add_site_callback.autocomplete(name='stranica')
        async def disabled_sites_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
            return make_choices(
                current=current,
                options=[site for site in SITE_NAMES if site not in channel_sites(interaction.channel.id)]
            )
        
        @remove_site_callback.autocomplete(name='stranica')
        @add_portlet_callback.autocomplete(name='stranica')
        @remove_portlet_callback.autocomplete(name='stranica')
        async def enabled_sites_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
            return make_choices(
                current=current,
                options=channel_sites(interaction.channel.id)
            )
        
        @add_portlet_callback.autocomplete(name='portlet')
        async def disabled_portlets_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
            site = interaction.data['options'][0]['value']
            return make_choices(
                current=current,
                options=[
                    portlet for portlet in all_site_portlets(site)
                    if portlet not in channel_site_portlets(interaction.channel.id, site)
                ]
            )

        @remove_portlet_callback.autocomplete(name='portlet')
        async def enabled_portlets_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
            site = interaction.data['options'][0]['value']
            return make_choices(
                current=current,
                options=channel_site_portlets(interaction.channel.id, site)
            )

    def extract_email(self) -> list[Email]:
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        self.mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        self.mail.select('inbox')

        _, data = self.mail.search(None, SEARCH_CRITERIA)
        email_ids = data[0].split()

        mail_objs = []

        for email_id in email_ids:
            # save the latest email id to a file
            # this way we can make sure that any email is only announced once
            int_id = int(email_id)
            if int_id <= self.highest_email_id:
                continue
            self.highest_email_id = int_id
            with open(EMAIL_FP, 'w') as file:
                json.dump(int_id, file)
                logging.info(f'Received email with id {int_id}')

            _, data = self.mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            content = ''
            attachment_paths = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type != 'text/plain':
                        continue
                    content_disposition = str(part.get('Content-Disposition'))

                    if 'attachment' not in content_disposition:
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
                                save_path = os.path.join(os.getcwd(), 'attachments', filename)
                                attachment_paths.append(save_path)
                                with open(save_path, "wb") as attachment_file:
                                    attachment_file.write(attachment_data)
            
            else:
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    content = payload.decode()
                else:
                    content = str(payload)

            timestamp = email.utils.parsedate_to_datetime(msg['date'])
            sender = msg['from'].strip('>').split('<')[-1]
            subject = content.split('\n')[0].strip()
            content = content.strip(subject)

            mail_objs.append(
                Email(
                    timestamp=timestamp,
                    sender=sender,
                    subject=subject,
                    content=content,
                    attachment_paths=attachment_paths
                )
            )

        return mail_objs

    async def send_to_discord(self, mail: Email, channel_ids: list[int]):
        logging.info(mail)

        full = mail.content

        msg_components = []
        for i in range(len(full) // CHAR_LIMIT + 1):
            msg_components.append(full[i * CHAR_LIMIT: (i + 1) * CHAR_LIMIT])

        files = []
        if mail.attachment_paths and ENABLED_ATTACHMENTS:
            for path in mail.attachment_paths:
                filename = path.split('\\')[-1]
                fp = f'/attachments/{filename}'
                files.append(discord.File(fp=fp, filename=filename))
                os.remove(fp)

        embed = mail.get_embed()

        view = discord.ui.View()
        for button in mail.get_buttons():
            view.add_item(button)

        for channel_id in channel_ids:
            if mail.is_for_channel(channel_id):
                #logging.debug(f'Mail is for {channel_id}; Site: {mail.site}, Portlet: {mail.portlet}')
                
                try:
                    channel = self.get_channel(channel_id)

                    message = await channel.send(content=get_random_quote(), embed=embed, view=view)

                    if ENABLED_CREATE_THREAD:
                        try:
                            thread = await message.create_thread(name=f'Diskusija o `{mail.subject}`', auto_archive_duration=10080)
                        except discord.Forbidden:
                            logging.warning(f'Forbidden;Thread creation forbidden for {channel.id}.')
                        except discord.HTTPException:
                            logging.warning('HTTPExceptoin; Starting thread failed.')
                        except ValueError:
                            logging.warning('ValueError; The files or embeds list not of appropriate size.')
                        except TypeError:
                            logging.warning('TypeError; Specified both file and files, or embed and embeds.')
                    
                    for i in range(len(msg_components) - 1):
                        await channel.send(content=msg_components[i], suppress_embeds=True)
                    
                    await channel.send(content=msg_components[-1], files=files, suppress_embeds=True)
                
                except Exception as e:
                    logging.error(e)

            else:
                logging.debug(f'Mail is not for {channel_id}; Site: {mail.site}, Portlet: {mail.portlet}')

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_loop(self) -> None:
        logging.debug('Checking for new emails.')
        
        try:
            emails = self.extract_email()
        except Exception as e:
            logging.error(e)
            return
        finally:
            if self.mail is not None:
                self.mail.logout()
        
        try:
            channel_ids = get_channel_ids()
        except Exception as e:
            logging.error(e)
            return
        
        if emails:
            logging.info('Email recieved:')

        for mail in emails:
            await self.send_to_discord(mail, channel_ids)
                
    async def on_ready(self) -> None:
        if self.started:
            return
        
        self.started = True
        logging.info(f'Logged in as {self.user.name}')
        
        try:
            await self.tree.sync()
        except discord.app_commands.errors.CommandSyncFailure as e:
            logging.error(f'Failed to sync commands: {e}')
            logging.warning('Exiting')
            sys.exit()
        else:
            logging.info('Commands synced.')

        self.command_names = [command.name for command in self.commands]
        
        self.check_loop.start()
        logging.info('Started check loop.')
