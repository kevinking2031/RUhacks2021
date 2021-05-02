import asyncio
import os
import random
from asyncio import sleep

import discord
from discord.ext import commands
import audioread
from google.api_core.exceptions import BadRequest

from settings_files._global import DISCORD_BOT_TOKEN

FFMPEG_PATH = "ffmpeg-20200831-4a11a6f-win64-static/bin/ffmpeg.exe"

bot = commands.Bot(command_prefix="!")

def chooseRandomQuestion():
    from dailyQuestions import QUESTIONS, ANSWERS

    choice = random.randint(0,6)
    question_of_day = QUESTIONS[choice]
    answer_of_day = ANSWERS[choice]
    return [question_of_day, answer_of_day]

randomQuestionAndAns = chooseRandomQuestion()
question_of_day = randomQuestionAndAns[0]
answer_of_day = randomQuestionAndAns[1]
scores = {}

# For text to speech
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'demottsAccount.json'

bot = commands.Bot(command_prefix='!', help_command=None)

@bot.command()
async def help(ctx):
    commands = "```help\t\t   Shows this message.\n" \
               "tr_text\t\tTranslate text to specified language.\n" \
               "tr_audio\t   tr_text but with audio.\n" \
               "tr_daily\t   Question of the day!\n" \
               "tr_setdaily\tSet the question of the day for \"Teacher\"\n" \
               "tr_leaderboard See rankings for dailies.\n```" \
               "For more help, see https://slimysea55.qoom.space/PolyBot/commands.html"
    embed = discord.Embed(title="PolyBot help", description=commands,
                        color=0x800080)

    await ctx.send(embed=embed)

async def translateText(targetLanguage, userText):
    import six
    from google.cloud import translate_v2 as translate

    client = translate.Client()
    if isinstance(userText, six.binary_type):
        text = userText.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = client.translate(userText, target_language=targetLanguage, format_='text')

    print(u"Text: {}".format(result["input"]))
    print(u"Translation: {}".format(result["translatedText"]))
    print(u"Detected source language: {}".format(result["detectedSourceLanguage"]))
    return result

def textToSpeech(ctx, userLanguage, userText):
    from google.cloud import texttospeech
    from google.cloud import texttospeech_v1

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=userText)
    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech_v1.VoiceSelectionParams(
        language_code=userLanguage,
        ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech_v1.AudioConfig(
        audio_encoding=texttospeech_v1.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

async def joinToPlayAudio(ctx):
    # User info
    currUser = ctx.message.author
    if (currUser.voice is None):
        await ctx.send("You're currently not in a voice channel")
        return

    currUserVC = currUser.voice.channel
    audioPath = "output.mp3"

    vc = await currUserVC.connect()
    await sleep(.5)
    vc.play(discord.FFmpegPCMAudio(executable=FFMPEG_PATH, source=audioPath))
    with audioread.audio_open(audioPath) as f:
        # Start Playing
        await sleep(f.duration)
    await vc.disconnect()

@bot.command(description="Translate sentence into language of choice, to be outputted in text.",
             brief="Translate text to specified language.")
async def tr_text(ctx, language, sentence):
    result = await translateText(language, sentence)
    translation = result["translatedText"]  # add translation code from google api
    embed = discord.Embed(title="Text Translation", description=translation,
                          color=0x800080)
    await ctx.send(embed=embed)

@tr_text.error
async def tr_text_error(ctx, error):
    print(error)
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Language not supported, please refer to https://slimysea55.qoom.space/PolyBot/about.html")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument(s), please refer to !help or https://slimysea55.qoom.space/PolyBot/about.html")


@bot.command(description="Translate sentence into language of choice, to be outputted in text."
                         " Will also be played in user voice channel.",
             brief="Translate text to specified language, with audio.")
async def tr_audio(ctx, language, sentence):
    result = await translateText(language, sentence)
    textToSpeech(ctx, language, result["translatedText"])

    translation = result["translatedText"]  # add translation code from google api
    embed = discord.Embed(title="Text Translation", description=translation,
                        color=0x800080)

    await joinToPlayAudio(ctx)

    currUser = ctx.message.author
    if currUser.voice is not None:
        footer = "React to with ✅ within 5 seconds to replay translation"
        embed.set_footer(text=footer)

    my_msg = await ctx.send(embed=embed)
    await asyncio.sleep(1)

    if currUser.voice is not None:
        await my_msg.add_reaction("✅")

        def check(reaction, user):
                return user != my_msg.author and str(reaction.emoji) == '✅'

        try:
                await bot.wait_for('reaction_add', timeout=5.0, check=check)
        except asyncio.TimeoutError:
            embed.set_footer(text="Can no longer replay translation")
            await my_msg.edit(embed=embed)
        else:
            await joinToPlayAudio(ctx)

@tr_audio.error
async def tr_audio_error(ctx, error):
    print(error)
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Voice not supported, please refer to https://slimysea55.qoom.space/PolyBot/about.html")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument(s), please refer to !help or https://slimysea55.qoom.space/PolyBot/about.html")

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
        global scores
        if msg.author in scores:
            scores[msg.author] += 1
        else:
            scores[msg.author] = 1
        await ctx.send("Congratulations, {.author}, you answered correctly! Your score is now {}."
                       .format(msg, scores[msg.author]))


@bot.command(description="Set the question of the day. Can only be done by users with the \"Teacher\" role. "
                         "The format of the question is to have a sentence with a word removed and have the word"
                         " filled in by students",
             brief="Set the question of the day. Can only be done by users with the \"Teacher\" role.")
@commands.has_role('Teacher')
async def tr_setdaily(ctx):
    global question_of_day
    global answer_of_day

    await ctx.send('Enter the english sentence.')
    message = await bot.wait_for('message')
    while message.author != ctx.author:
        print(message.author)
        message = await bot.wait_for('message')
    sentence = message.content.lower()

    await ctx.send('Enter the translated sentence.')
    message = await bot.wait_for('message')
    while message.author != ctx.author:
        print(message.author)
        message = await bot.wait_for('message')
    translation = message.content.lower()

    await ctx.send('Enter the answer/word to be removed.')
    message = await bot.wait_for('message')
    while message.author != ctx.author:
        print(message.author)
        message = await bot.wait_for('message')
    word = message.content.lower()

    question_of_day = "English: " + sentence + "\nTranslation: " + translation.replace(word, "\\_ " * len(word))
    answer_of_day = word

    await ctx.send('This is the question of the day: ' + question_of_day
                   + '\nIf this is incorrect, please redo the setting process.')

@tr_setdaily.error
async def tr_setdaily_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        await ctx.send("*You do not have permission to do this.*")


@bot.command(description="Check the current leaderboard for daily questions!", brief="See rankings for dailies.")
async def tr_leaderboard(ctx):
    global scores
    dict(sorted(scores.items(), key=lambda item: item[1]))
    description = ""

    if len(scores) == 0:
        await ctx.send("There are no scores to display.")
    else:
        for key in scores:
            description += str(key) + " --- " + str(scores[key]) + "\n"

        embed = discord.Embed(title="Leaderboard", description=description,
                          color=0x800080)
        await ctx.send(embed=embed)

bot.run(DISCORD_BOT_TOKEN)