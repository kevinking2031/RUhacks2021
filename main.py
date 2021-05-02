import asyncio
import os

import discord
from discord.ext import commands

from settings_files._global import DISCORD_BOT_TOKEN

bot = commands.Bot(command_prefix="!")
question_of_day = "r u happy"
answer_of_day = "yes"

# For text to speech
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'demottsAccount.json'

async def translateText(ctx, targetLanguage, userText):
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


# for filename in os.listdir("./cogs"):
#     if filename.endswith(".py") and filename != "__init__.py":
#         bot.load_extension(f'cogs.{filename[:-3]}')


@bot.command(description="Translate sentence into language of choice, to be outputted in text.",
             brief="Translate text to specified language.")
async def tr_text(ctx, language, sentence):
    result = await translateText(ctx, language, sentence)
    translation = result["translatedText"]  # add translation code from google api
    embed = discord.Embed(title="Text Translation", description=translation,
                          color=0x800080)



@bot.command(description="Translate sentence into language of choice, to be outputted in text."
                         " Will also be played in user voice channel.",
             brief="Translate text to specified language, with audio.")
async def tr_audio(ctx, language, sentence):
    result = await translateText(ctx, language, sentence)
    textToSpeech(ctx, language, result["translatedText"])

    translation = result["translatedText"]  # add translation code from google api
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