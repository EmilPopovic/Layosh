# Layosh

Layosh is a Python Discord bot designed to streamline communication between universities and their students. This bot listens to automated emails from the university's official email system and seamlessly displays them within a subscribed Discord server. Stay up-to-date with important announcements, events, and notices directly on Discord, making sure you never miss out on crucial information. (Layosh can technically be used for any email but university announcements are his intended purpose.)

### Features:

- Monitors and processes automated emails from the university.
- Displays email content, including announcements and notifications (and in the future attachments, too), in a Discord channel.
- Provides a unified platform for students to access official communications.
- User-friendly setup for easy deployment and customization, Docker files included :).
- Completely free, do anything you want with it.

### Usage:

- Clone this repository to your local machine.
- Create an `Attachments` folder in the working directory (next to `main.py` and company).
- Add some funny quotes to `quotes.txt`. This was not my idea, blame my friend.
- Configure the bot token and other settings at the top of `main.py`.
- Install the required dependencies using `pip install discord` (Everything else is from the standard library!).
- Run the bot by running `main.py`.
- Alternatively, use `docker-compose build` and run the container to let Docker take care of everything for you.
- Add Layosh to your Discord server and run `/start` in any channels you want announcements to be sent.
- Sit back and let the bot automatically relay university emails to your Discord server.

### Commands list:

- `/start` - Start sending announcements to current channel.
- `/stop` - Stop sending announcements to current channel.
- `/check` - Check if announcements are being sent to the current channel.
- `/ping` - Ping the bot and display latency.

### Other considerations:

- Yes, this is somewhat of a long section. Please read it.
- Email titles are broken. I know, and honestly, I don't care. If you fix it, contact me (or don't, you do you).
- Please don't use your real email for this. First, I didn't bother to secure the password (It's just sitting in `main.py`.) and some email providers may block your email address (In my testing, Outlook based emails will be banned).
- The deployed bot is using a throwaway gmail.com address to which emails are forwarded from a real uni.domain address.
- The filter is dead simple by default, it just checks if an email has been sent from no-reply, could be improved, if you ask me (but again, I know, and I don't care), don't blame me if you use this and end up leaking something.
- There may also be some bugs, of course. I only spent a couple of hours on this... thing.
- Check out [Shteff](https://github.com/Mjolnir2425/Shteff), a fully free and definitely not half broken Discord music bot with some interesting features.

### Contributing

Contributions are encouraged and welcome! If you have suggestions, bug fixes, or feature enhancements, feel free to open issues and pull requests. Or just keep them to yourself, you greedy bastard! ',:/