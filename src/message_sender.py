import discord
import logging

from load_config import RED, ACCENT, YELLOW, BLUE, GREEN


async def sendf(
        text: str,
        interaction: discord.Interaction,
        followup: bool = False,
        fail: bool = False,
        event: bool = False,
        warning: bool = False,
        info: bool = False,
        ephemeral: bool = True,
        author: discord.User = None
    ) -> None:
    embed = discord.Embed(
        title='Pogreška!' if fail else 'Događaj' if event else 'Pozor!' if warning else 'Info' if info else 'Uspjeh!',
        description=text,
        color=RED if fail else ACCENT if event else YELLOW if warning else BLUE if info else GREEN
    )
    if author is not None:
        embed.set_author(name=author.name, icon_url=author.avatar.url)
    try:
        if followup:
            await interaction.followup.send(content='', embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content='', embed=embed, ephemeral=ephemeral)
    except discord.HTTPException:
        logging.error('discord.HTTPException; Failed sending message.')
    except discord.InteractionResponded:
        logging.error('discord.InteractionResponded; This interaction has been responded to before.')
    except Exception as e:
        logging.error(f'An error occurred in sendf(), {e}')


async def send_not_implemented(interaction: discord.Interaction):
    embed = discord.Embed(title='Huh', description='Ova funkcija još nije implementirana.', color=ACCENT)
    try:
        await interaction.response.send_message(content='', embed=embed, ephemeral=True)
    except discord.HTTPException:
        logging.error('discord.HTTPException; Failed sending message.')
    except discord.InteractionResponded:
        logging.error('discord.InteractionResponded; This interaction has been responded to before.')
    except Exception as e:
        logging.error(f'An error occurred in sendf(), {e}')