import discord
import asyncio
import asyncpg
import random
from discord.ext import commands
# nothing rn


class PewDieCoin:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['$', 'balance'])
    async def bank(self, ctx):
        count = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1", ctx.author.id)
        if count is None:
            count = 0
        await ctx.send(f"You currently have `{count}` coins")

    @commands.cooldown(1, 14400, commands.BucketType.user)
    @commands.command()
    async def timely(self, ctx):
        count = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1", ctx.author.id)
        if count is None:
            count = 0
        await self.bot.db.execute("INSERT INTO bank (user_id, user_money) VALUES ($1, $2 + 75) ON CONFLICT (user_id) DO UPDATE SET user_money= $2 + 75", ctx.author.id, count)
        after_money = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1", ctx.author.id)
        await ctx.send(f"Added `75` coins to your coin pouch, your current amount is now `{after_money}` coins")

    @commands.command(alias='cf')
    async def coinflip(self, ctx, side: str, amount_of_coins):
        result = random.choice(['h', 't'])
        amt = amount_of_coins
        count = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1", ctx.author.id)
        if amt == 'all':
            amt = count
        else:
            amt = int(amt)
        if (side == 'head' or side == 'heads') and result == 'h':
            side = 'h'
        elif (side == 'tail' or side == 'tails') and result == 't':
            side = 't'
        else:
            side = side
        if count is None:
            count = 0
        if amt > count:
            return await ctx.send("Seems like you don't have enough coin")
        else:
            if result == side:
                await ctx.send(embed=discord.Embed(description=f"Congrats fellow Pewd, you won {amt} coins", color=discord.Color.green()))
                await self.bot.db.execute("UPDATE bank SET user_money= user_money + $1 WHERE user_id=$2", amt, ctx.author.id)
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=f"Lost to T-Series by {amt} coins"))
                await self.bot.db.execute("UPDATE bank SET user_money= user_money - $1 WHERE user_id=$2", amt, ctx.author.id)

    
    @commands.command()
    async def leaderboard(self, ctx):
        stats = await self.bot.db.fetch("SELECT * FROM bank ORDER BY user_money DESC LIMIT 5")
        emb = discord.Embed(color=discord.Color(value=0xae2323), title="Leaderboard for the Most Coins")
        c = 0
        for _ in stats:
            emb.add_field(name=str(self.bot.get_user(stats[c]['user_id']).name), value=f"coins - {stats[c]['user_money']}", inline=False)
            c+=1
        await ctx.send(embed=emb)


    @commands.command()
    async def give(self, ctx, user : discord.Member, amount: int):
        author_coin = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1;", ctx.author.id)
        if author_coin is None:
            author_coin = 0
        if amount > (author_coin):
            return await ctx.send("Insufficient coins to give")
        if user.bot:
            return await ctx.send("Bot Accounts cannot have coins")
        elif user.id == ctx.author.id:
            return await ctx.send(r"Why, why are you trying to give money to your self ¯\_(ツ)_/¯")
        else:
            await self.bot.db.execute("UPDATE bank SET user_money=user_money-$1 WHERE user_id=$2;", amount, ctx.author.id)
            await self.bot.db.execute("INSERT INTO bank (user_id, user_money) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET user_money = user_money+$2;", int(user.id), amount)
            author_coin = await self.bot.db.fetchval("SELECT user_money FROM bank WHERE user_id=$1;", ctx.author.id)
            await ctx.send(embed=discord.Embed(description=f"Gave {amount} coins to {user.mention}, your current amount is now `{author_coin}` coins"))

def setup(bot):
    bot.add_cog(PewDieCoin(bot))