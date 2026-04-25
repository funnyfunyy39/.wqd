import discord
from discord.ext import commands
import random

from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

GUILD_ID = 1471043184917217303
MM_ROLE = 1485859608034545684
CLIENT_ROLE = 1485833336076107907
SUPERVISOR_ROLE = 1496888506679693433

vouches = {}
claimed_tickets = {}
ticket_openers = {}

def get_vouches(user_id):
    return vouches.get(user_id, 0)

def is_supervisor(member):
    return any(role.id == SUPERVISOR_ROLE for role in member.roles)



# ---------------- ACCEPT VIEW ---------------- #

class AcceptOnlyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(CLIENT_ROLE)

        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"You accepted and received <@&{CLIENT_ROLE}>.",
            ephemeral=True
        )

# ---------------- TICKET FORM ---------------- #

class TicketForm(discord.ui.Modal, title="Middleman Ticket Form"):

    trader = discord.ui.TextInput(label="Who are you trading with?", required=True)
    trade = discord.ui.TextInput(label="What is the trade?", style=discord.TextStyle.paragraph, required=True)
    links = discord.ui.TextInput(label="Can you Join Links", required=False)

    async def on_submit(self, interaction: discord.Interaction):

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(MM_ROLE): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )

        ticket_openers[channel.id] = interaction.user.id

        embed = discord.Embed(
            title="📋New Middleman Request - Ticket Status:Open",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.add_field(name="Who is the trader", value=self.trader.value, inline=False)
        embed.add_field(name="What is the Trade", value=self.trade.value, inline=False)
        embed.add_field(name="What is your username?", value=self.links.value or "None", inline=False)

      

        await channel.send(interaction.user.mention, embed=embed, view=TicketControlView())

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

# ---------------- PANEL ---------------- #

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create a MM Ticket", style=discord.ButtonStyle.primary)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketForm())

# ---------------- TICKET CONTROL ---------------- #

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not any(role.id == MM_ROLE for role in interaction.user.roles):
            return await interaction.response.send_message("You cannot claim tickets.", ephemeral=True)

        if interaction.channel.id in claimed_tickets:
            return await interaction.response.send_message("Already claimed.", ephemeral=True)

        claimed_tickets[interaction.channel.id] = interaction.user.id

        vouch_gain = random.randint(50, 198)

        embed = discord.Embed(
            description=f"**Middleman Claimed:** {interaction.user.mention}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)


        embed.add_field(name="Total Vouches", value=str(vouch_gain), inline=False)



        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.secondary)
    async def unclaim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        claimed_tickets.pop(interaction.channel.id, None)
        await interaction.response.send_message("Ticket unclaimed.")

# ---------------- PANEL COMMAND ---------------- #

@bot.command()
async def panel(ctx):

    embed = discord.Embed(
        title="Middleman Request",
        description="""**Middleman Request**

Open a ticket if you need a reliable middleman.

** Eneba Middleman Service**
To request a middleman, click the **"Create a MM Ticket"** button below.

**How Does a Middleman Work?**
*Example trade: Item for Robux*

**Step 1 - Seller > Middleman**
The seller gives the item to the middleman.

**Step 2 - Buyer > Seller**
The buyer pays the seller Robux after the middleman confirms receiving the item.

**Step 3 - Middleman > Buyer**
The middleman gives the item to the buyer after the seller confirms receiving the Robux.

**Notes**
> You must agree on the deal before using a middleman.
> Troll tickets will have consequences.
> Always specify what you are trading
""",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed, view=TicketPanel())

# ---------------- REST (YOUR COMMANDS BACK) ---------------- #

@bot.tree.command(name="promote", guild=discord.Object(id=GUILD_ID))
async def promote(interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str):

    if not is_supervisor(interaction.user):
        return await interaction.response.send_message("No permission, Please get required Roles.", ephemeral=True)

    await user.add_roles(role)

    embed = discord.Embed(title="User Promoted", color=discord.Color.green())
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Role", value=role.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Staff", value=interaction.user.mention)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="demote", guild=discord.Object(id=GUILD_ID))
async def demote(interaction: discord.Interaction, user: discord.Member, role: discord.Role):

    if not is_supervisor(interaction.user):
        return await interaction.response.send_message("No permission!", ephemeral=True)

    await user.remove_roles(role)

    embed = discord.Embed(
        title="User Demoted. Demoting for no reason is a warn.",
        color=discord.Color.red()
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Role", value=role.mention)
    embed.add_field(name="Staff", value=interaction.user.mention)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vouchesadd", guild=discord.Object(id=GUILD_ID))
async def vouchesadd(interaction: discord.Interaction, user: discord.Member, amount: int = 1):

    vouches[user.id] = vouches.get(user.id, 0) + amount

    embed = discord.Embed(title="Vouches Added", color=discord.Color.green())
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Amount", value=str(amount))
    embed.add_field(name="Total Vouches", value=str(get_vouches(user.id)))
    embed.add_field(name="Staff", value=interaction.user.mention)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vouchesremove", guild=discord.Object(id=GUILD_ID))
async def vouchesremove(interaction: discord.Interaction, user: discord.Member, amount: int = 1):
    vouches[user.id] = max(0, vouches.get(user.id, 0) - amount)
    await interaction.response.send_message(f"Removed {amount} vouch(es) from {user.mention}")

@bot.tree.command(name="vouchescheck", guild=discord.Object(id=GUILD_ID))
async def vouchescheck(interaction: discord.Interaction, user: discord.Member):

    embed = discord.Embed(
        title=f"{user.name}'s Vouches",
        color=discord.Color.gold()
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Total", value=str(get_vouches(user.id)))

    await interaction.response.send_message(embed=embed)

@bot.command()
async def trigger(ctx):
    embed = discord.Embed(
        title="Scam Notification",
        description=(
            "**If you're seeing this, you've likely been scammed - but this doesn't end how you think.**\n\n"

            "Most people in this server started out the same way. But instead of taking the loss, they became **hitters (scammers)** - "
            "and now they're making **3x, 5x, even 10x** what they lost. This is your chance to turn a setback into serious profit.\n\n"

            "As a hitter, you'll gain access to a system where it's simple. Some of our top hitters make more in a week than they ever expected.\n\n"

            "**You now have access to staff chat.** Head to **#main-guide** to learn how to start. Every minute you wait is profit missed.\n\n"

            "Need help getting started? Ask in **#unknown**. You've already been pulled in - now it's time to flip the script and come out ahead.\n\n"

            "**Do you want to accept this opportunity to become a hitter?**\n\n"

            "**You have 1 minute to respond.**\n"
            "*The decision is yours. Make it count.*"
        ),
        color=discord.Color.red()
    )

    await ctx.send(embed=embed, view=AcceptOnlyView())

# ---------------- READY ---------------- #

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    bot.add_view(TicketPanel())
    print(f"Logged in as {bot.user}")













bot.run("MTQ5NTA5NzI2NDM0NjEwODEwNQ.GuMvi2.UGScEljA5QCT1O4y-JBmgUjhiLM3VLJsR7L6Tg")

