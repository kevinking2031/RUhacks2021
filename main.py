import asyncio
import os

import discord
from discord.ext import commands

from settings_files._global import DISCORD_BOT_TOKEN

bot = commands.Bot(command_prefix="!")
question_of_day = "r u happy"
answer_of_day = "yes"


# for filename in os.listdir("./cogs"):
#     if filename.endswith(".py") and filename != "__init__.py":
#         bot.load_extension(f'cogs.{filename[:-3]}')


@bot.command(description="Translate sentence into language of choice, to be outputted in text.",
             brief="Translate text to specified language.")
async def tr_text(ctx, language, sentence):
    translation = "insert translation here"  # add translation code from google api
    embed = discord.Embed(title="Text Translation", description=translation,
                          color=0x800080)


@bot.command(description="Translate sentence into language of choice, to be outputted in text."
                         " Will also be played in user voice channel.",
             brief="Translate text to specified language, with audio.")
async def tr_audio(ctx, language, sentence):
    translation = "insert translation here"  # add translation code from google api
    embed = discord.Embed(title="Text Translation", description=translation,
                          color=0x800080)

    footer = "React to with ✅ within 5 seconds to replay translation"
    embed.set_footer(text=footer)

    my_msg = await ctx.send(embed=embed)
    await asyncio.sleep(1)

    await my_msg.add_reaction("✅")

    def check(reaction, user):
        return user != my_msg.author and str(reaction.emoji) == '✅'

    try:
        await bot.wait_for('reaction_add', timeout=5.0, check=check)
    except asyncio.TimeoutError:
        embed.set_footer(text="Can no longer replay translation")
        await my_msg.edit(embed=embed)
    else:
        await ctx.send('👍')  # put replay code here


@bot.command(description="Outputs the question of the day, giving the user 30 seconds to respond",
             brief="Question of the day!")
async def tr_daily(ctx):
    description = "Fill in the missing word based on the translation!\n\n" + question_of_day

    embed = discord.Embed(title="Question of the Day!",
                          description=description, color=0x800080)
    embed.set_footer(text="You have 30 seconds to answer correctly!")
    await ctx.send(embed=embed)

    def check(m):
        return m.content.lower() == answer_of_day and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("Unfortunately, you didn't answer correctly.")
    else:
        await ctx.send("Congratulations, {.author}, you answered correctly!".format(msg))


@bot.command(description="Set the question of the day. Can only be done by users with the \"Teacher\" role. "
                         "The format of the question is to have a sentence with a word removed and have the word"
                         " filled in by students",
             brief="Set the question of the day. Can only be done by users with the \"Teacher\" role.")
async def set_daily(ctx):
    global question_of_day, answer_of_day

    await ctx.send('Enter the english sentence.')
    sentence = await bot.wait_for('message')
    sentence = sentence.content.lower()

    await ctx.send('Enter the translated sentence.')
    translation = await bot.wait_for('message')
    translation = translation.content.lower()

    await ctx.send('Enter the answer/word to be removed.')
    word = await bot.wait_for('message')
    word = word.content.lower()

    question_of_day = "English: " + sentence + "\nTranslation: " + translation.replace(word, "\\_ " * len(word))
    answer_of_day = word

    await ctx.send('This is the question of the day: ' + question_of_day
                   + '\nIf this is incorrect, please redo the setting process.')


bot.run(DISCORD_BOT_TOKEN)
