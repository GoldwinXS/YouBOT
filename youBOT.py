import praw, shutil
import pandas as pd
from API_keys import *
import numpy as np
from YouBot_utils import *
import os
from moviepy.audio.fx.volumex import volumex
import moviepy.editor as mpy
import textwrap
import moviepy.video.fx.all as vfx
from simple_youtube_api.Channel import Channel, LocalVideo
import spacy

########################
""" FILE SETTINGS """

fps = 24
width = 854
height = 480
rescale_factor = 1
number_of_comments = 26
max_replies = 6
subreddit_name = 'AskReddit'

########################

reddit = praw.Reddit(client_id=reddit_client_ID,
                     client_secret=reddit_client_secret,
                     user_agent=reddit_app_name,
                     username=reddit_account_name,
                     password=reddit_account_pass)

data_file = 'YouBOT_{}_data.pickle'.format(subreddit_name)
reddit_post_data_path = 'reddit_post_data/'
subreddit = reddit.subreddit(subreddit_name)
YouBOT_session_data = {'post_ID': None,
                       'post_data': None}
YouBOT_data = None
audio_temp = 'temp/voice_temp.mp3'
icon_assets_path = r'C:\Users\Goldwin Stewart\PycharmProjects\YouBOT\assets\reddit_icons/'
blue_text_color = '#009dff'  # '#33667F'  # (51,102,134)
dark_grey_text_color = '#7C7E7F'  # (124,126,127)
transition_clip_path = 'assets/transitions/TV Static Transition with sound.mp4'  # TV Static Transition Effect.mp4'
music_dir = r'C:\Users\Goldwin Stewart\PycharmProjects\YouBOT\assets\songs\happy\instrumental'
release_path = 'releases/'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Goldwin Stewart\PycharmProjects\YouBOT\trading-65284e3585ce.json"
google_voices = ['en-AU-Standard-C', 'en-AU-Standard-D', 'en-AU-Standard-B', 'en-AU-Standard-A', 'en-GB-Standard-A', 'en-GB-Standard-B', 'en-GB-Standard-C', 'en-GB-Standard-D', 'en-US-Standard-B', 'en-US-Standard-C', 'en-US-Standard-D',
                 'en-US-Standard-E']
voice_rng = np.random.randint(0, len(google_voices))

nlp = spacy.load('en_core_web_sm')



def ensure_new(names_list, generator):
    topic = None
    while True:
        try:
            topic = generator.next()
            names_list.index(prepare_title_for_win10_file(topic.title))
        except ValueError:
            break

    return topic


def get_next_topic():
    try:
        dat = pd.read_pickle('YouBOT_data.pickle')
        print(dat)
        list_gen = dat
        dat = {'dat': []}
    except FileNotFoundError:
        dat = {'dat': []}
        list_gen = subreddit.top()

    # print(list_gen)
    names = os.listdir('releases/')
    topic = ensure_new(names, list_gen)
    # print(topic.title)
    YouBOT_session_data['post_ID'] = topic.id
    YouBOT_session_data['post_data'] = topic

    dat['dat'].append(list_gen)
    pd.to_pickle(list_gen, 'YouBOT_data.pickle')

    return topic.id


print('Getting fresh topic...')
get_next_topic()
print('Selected topic: {}'.format(YouBOT_session_data['post_data'].title))

# test_id = 'cw6hto'
submission = reddit.submission(id=YouBOT_session_data['post_ID'])
# submission = reddit.submission(id='aqf3bi')
submission.comments.replace_more(limit=0)


def make_temp_voice(text, voice_index):
    text = text.replace('<NEWLINE>', '').replace('<', '').replace('>', '').replace('*', '')  # dont say random punctuation
    text = ' '.join(item for item in text.split() if not (item.startswith('https')))  # dont say websites starting with https
    voice_name = google_voices[voice_index]
    voice_lang_code = voice_name[0:5]
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(text=text)

    voice = texttospeech.types.VoiceSelectionParams(language_code=voice_lang_code, name=voice_name)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        speaking_rate=0.935)

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open(audio_temp, 'wb') as out:
        out.write(response.audio_content)
        # print('Audio content written to file "voice_temp.mp3"')

    # if len(text) > 2:
    #     myob = gTTS(text=text, lang='en-AU-Standard-B', slow=False, )
    #
    #     try:
    #         os.remove(audio_temp)
    #     except OSError:
    #         pass
    #     myob.save(audio_temp)


def remove_urls(text):
    doc = nlp(text)
    for tok in doc:
        if tok.like_url == True:
            text = text.replace(tok.text, '[URL REDACTED]')

    return text


def read_sentence(text, pos=(10, 10), time=0):
    voice_rng = np.random.randint(0, len(google_voices))
    xpos, ypos = pos
    start_time = time

    text = text.rstrip(" ")

    if len(text) >= 2:
        if text[-1] != '.' and text[-1] != '!' and text[-1] != '?':
            text += "."

    print(text)

    text = remove_urls(text)
    text = text.replace('\n', '<NEWLINE>')
    sentences_to_read_aloud = split_into_sentences(text)
    text_to_display = []

    video_clips = []
    audio_clips = []

    for i in range(0, len(sentences_to_read_aloud)):
        make_temp_voice(sentences_to_read_aloud[i], voice_rng)  # make temp audio file
        text_to_display.append(sentences_to_read_aloud[i])
        text_to_wrap = ' '.join(text_to_display)

        wrapped_text_to_display = '\n'.join(textwrap.wrap(text_to_wrap, width=int(width / 8) - int(ypos / 10)))
        wrapped_text_to_display = wrapped_text_to_display.replace("<NEWLINE>", '\n')

        audio = mpy.AudioFileClip(audio_temp, buffersize=1000000).set_start(time)  # load temp audio file
        video = mpy.TextClip(wrapped_text_to_display, color='white', align='west', fontsize=13, font='Verdana').set_position(pos).set_start(time)  # make text clip and set duration to be as long as audio file

        time += audio.duration

        video_clips.append(video)
        audio_clips.append(audio)

    duration = time - start_time

    return video_clips, audio_clips, duration


def get_text_length(text, pos):
    xpos, ypos = pos
    formatting_new_lines = text.count('<NEWLINE>')
    w = int(width / 8) - int(ypos / 10)
    if w < 0:
        w = 25
    ltext = textwrap.wrap(text, width=w)
    length = int((len(ltext) * 40) + formatting_new_lines * 40)
    return int(length)


def read_comment_and_replies(comment, replies, start_time):
    section_time = start_time
    xpos = 100
    ypos = height / (2 + len(replies))

    audio_clips = []
    video_clips = []
    ups_arrow_img = [mpy.ImageClip(icon_assets_path + 'up_logo.png').set_start(section_time).set_pos((xpos - 30, ypos)).resize(0.8)]
    downs_arrow_img = [mpy.ImageClip(icon_assets_path + 'down_logo.png').set_start(section_time).set_pos((xpos - 32, ypos + 25)).resize(0.8)]
    corner_logo_img = [mpy.ImageClip(icon_assets_path + 'reddit_logo_corner.png').set_start(section_time).set_pos(('right', 'bottom'))]

    # isinstance(comment.author.name, type(None)):
    try:
        author_name_text = [mpy.TextClip(comment.author.name, color=blue_text_color, align='west').set_position((xpos, ypos - 20)).set_start(section_time)]
    except AttributeError:
        author_name_text = [mpy.TextClip('[Deleted]', color=blue_text_color, align='west').set_position((xpos, ypos - 20)).set_start(section_time)]

    time = pd.to_datetime(comment.created, unit='s').isoformat()
    ups_text = [
        mpy.TextClip(str(round_ups(comment.ups)) + ' points - ' + time[0:10] + ' at ' + time[11:], color=dark_grey_text_color, align='east', fontsize=9).set_position((xpos + author_name_text[0].w + 10, ypos - 18)).set_start(
            section_time)]

    comment_text = comment.body.replace('&#x200B;', '')

    vt, at, dt = read_sentence(comment_text, pos=(xpos, ypos), time=section_time)
    # print(dt, section_time, xpos, ypos, vt[-1].h)
    if len(vt) > 0:
        bottom_bar_img = [mpy.ImageClip(icon_assets_path + 'bottom_bar.png').set_start(dt + section_time).set_pos((xpos, ypos + vt[-1].h + 5)).resize(0.45)]
    else:
        bottom_bar_img = []

    audio_clips += at
    video_clips += vt
    section_time += dt

    for i in range(len(replies)):
        xpos += 30
        # ypos += get_text_length(reply_text, (xpos, ypos)) + 50

        try: # got a strange bug here so I added this
            ypos += video_clips[-1].h + 65
        except IndexError:
            ypos += 65


        if ypos + get_text_length(replies[i].body, (xpos, ypos)) > height * 0.9:  # do not continue if we are too low on the screen
            break

        reply_text = replies[i].body.replace('&#x200B;', '')
        vt, at, dt = read_sentence(reply_text, pos=(xpos, ypos), time=section_time)
        ups_arrow_img.append(mpy.ImageClip(icon_assets_path + 'up_logo.png').set_start(section_time).set_pos((xpos - 30, ypos)).resize(0.8))
        if len(vt) > 0:
            bottom_bar_img.append(mpy.ImageClip(icon_assets_path + 'bottom_bar.png').set_start(dt + section_time).set_pos((xpos, ypos + vt[-1].h + 5)).resize(0.45))
        downs_arrow_img.append(mpy.ImageClip(icon_assets_path + 'down_logo.png').set_start(section_time).set_pos((xpos - 32, ypos + 25)).resize(0.8))
        try:
            author_name_text.append(mpy.TextClip(replies[i].author.name, color=blue_text_color, align='west').set_position((xpos, ypos - 20)).set_start(section_time))
        except AttributeError:
            author_name_text.append(mpy.TextClip('[Deleted]', color=blue_text_color, align='west').set_position((xpos, ypos - 20)).set_start(section_time))

        time = pd.to_datetime(replies[i].created, unit='s').isoformat()

        ups_text.append(
            mpy.TextClip(str(round_ups(replies[i].ups)) + ' points - ' + time[0:10] + ' at ' + time[11:], color=dark_grey_text_color, fontsize=9, align='east').set_position((xpos + author_name_text[i + 1].w + 10, ypos - 18)).set_start(
                section_time))
        audio_clips += at
        video_clips += vt
        section_time += dt
        # print(section_time)

        # xpos += 30
        # # ypos += get_text_length(reply_text, (xpos, ypos)) + 50
        # ypos += video_clips[-1].h + 50

        # if ypos > height * 0.9:  # do not continue if we are too low on the screen
        #     break
        # else: section_time += dt

    for i in range(0, len(video_clips)):
        video_clips[i] = video_clips[i].set_end(section_time)

    for i in range(0, len(ups_arrow_img)):
        ups_arrow_img[i] = ups_arrow_img[i].set_end(section_time)
        downs_arrow_img[i] = downs_arrow_img[i].set_end(section_time)
        author_name_text[i] = author_name_text[i].set_end(section_time)
        ups_text[i] = ups_text[i].set_end(section_time)

    for i in range(0, len(corner_logo_img)):
        corner_logo_img[i] = corner_logo_img[i].set_end(section_time)

    for i in range(0, len(bottom_bar_img)):
        bottom_bar_img[i] = bottom_bar_img[i].set_end(section_time)

    return video_clips, audio_clips, ups_arrow_img, bottom_bar_img, downs_arrow_img, author_name_text, corner_logo_img, ups_text, section_time,


def is_comment_too_long(text):
    max_word_count = 1000
    max_char_count = 2000
    too_long = False

    if len(text.split()) > max_word_count:
        too_long = True
    if len(text) > max_char_count:
        too_long = True

    return too_long


def get_top_comments_and_replies(comment_list):
    data = {'comments': comment_list, 'replies': [], 'ups': []}

    #  create a dataframe for all comment object replies and ups
    for i in range(0, len(data['comments'])):
        data['replies'].append(data['comments'][i].replies.list()[0:max_replies])
        data['ups'].append(data['comments'][i].ups)
    dat = pd.DataFrame(data)

    #  remove any posts with deleted comments
    for i in range(0, len(dat)):

        try:
            if is_comment_too_long(dat['comments'][i].body) or dat['comments'][i].depth >0:
                dat = dat.drop(i).reset_index(drop=True)
            try:
                # isinstance(dat['comments'][i].author.name, type(None))
                assert dat['comments'][i].author.name
            except AttributeError:
                # print('DELETED COMMENT DETECTED. REMOVING.')
                dat = dat.drop(i).reset_index(drop=True)

            index = 0
            while True:
                max_index = len(dat['replies'][i])
                if index >= max_index:
                    break
                elif isinstance(dat['replies'][i][index].name, type(None)) or dat['replies'][i][index].body == '[deleted]' or is_comment_too_long(dat['replies'][i][index].body):  # or isinstance(dat_temp['replies'][i][index], type(None)):
                    # print('DELETED REPLY DETECTED. REMOVING.')
                    del dat['replies'][i][index]
                    index = 0
                else:
                    index += 1

        except KeyError:
            break
    dat = dat.iloc[0:len(dat)].sort_values('ups', ascending=False).reset_index()

    return dat


def prepare_all_comment_clips(comments, list_or_replies, start_time):
    section_time = start_time
    audio_clips = []
    video_clips = []
    ups_arrow_img = []
    bottom_bar_img = []
    downs_arrow_img = []
    author_name = []
    corner_logo_img = []
    transition_clips = []
    ups_text = []

    for i in range(0, len(comments)):
        video_clips_temp, audio_clips_temp, ups_arrow_img_temp, bottom_bar_img_temp, downs_arrow_img_temp, author_name_temp, corner_logo_img_temp, ups_text_temp, section_time = read_comment_and_replies(comments[i], list_or_replies[i],
                                                                                                                                                                                                          section_time)
        audio_clips += audio_clips_temp
        video_clips += video_clips_temp
        ups_arrow_img += ups_arrow_img_temp
        downs_arrow_img += downs_arrow_img_temp
        author_name += author_name_temp
        ups_text += ups_text_temp
        corner_logo_img += corner_logo_img_temp
        section_time = section_time
        bottom_bar_img += bottom_bar_img_temp
        transition_clip = mpy.VideoFileClip(transition_clip_path).set_start(section_time)
        transition_clip_audio = volumex(transition_clip.audio, 0.5)
        transition_clips.append(transition_clip.set_audio(transition_clip_audio))
        section_time = section_time + transition_clip.duration
        audio_clips.append(transition_clip.audio)
        # print(section_time)

    return video_clips, audio_clips, ups_arrow_img, downs_arrow_img, bottom_bar_img, author_name, corner_logo_img, transition_clips, ups_text, section_time


def prepare_intro_clips(reddit_post):
    # iv = []
    voice_rng = np.random.randint(0, len(google_voices))
    rpost = reddit_post
    intro_text = rpost.subreddit.title
    intro_text = intro_text.rstrip('...')
    intro_text = 'r/' + intro_text + ', asks: ' + rpost.title
    intro_text = textwrap.wrap(intro_text, width=80)
    intro_text = '\n'.join(intro_text)
    # intro_text_clip = mpy.TextClip(intro_text, color='white', fontsize=18).set_position(('center', height / 1.2)).set_start(0)
    make_temp_voice(intro_text, voice_rng)
    intro_audio_clip = mpy.AudioFileClip(audio_temp, buffersize=1000000).set_start(0)  # load temp audio file
    intro_time = intro_audio_clip.duration

    outro_image_offset = height / 10
    intro_image = mpy.ImageClip(icon_assets_path + 'reddit_logo_verylarge_middle.png').set_position(('center', outro_image_offset)).resize(.4)

    intro_text_clip = mpy.TextClip(intro_text, color='white', fontsize=18).set_position(('center', outro_image_offset + intro_image.h + 20)).set_start(0).set_duration(intro_audio_clip.duration)
    try:
        author_text_clip = mpy.TextClip('posted by: ' + rpost.author.name, color=dark_grey_text_color, fontsize=14).set_position(('center', outro_image_offset + intro_image.h + intro_text_clip.h + 30)).set_start(0).set_duration(
            intro_audio_clip.duration)
    except AttributeError:
        author_text_clip = mpy.TextClip('posted by: ' + '[Deleted] (RIP)', color=dark_grey_text_color, fontsize=14).set_position(('center', outro_image_offset + intro_image.h + intro_text_clip.h + 30)).set_start(0).set_duration(
            intro_audio_clip.duration)
    intro_image = intro_image.set_duration(intro_time)
    # print(intro_time)

    # for i in range(len(iv)):
    #     iv[i].set_end(it)

    return intro_text_clip, intro_audio_clip, intro_time, intro_image, author_text_clip


def prepare_background_music(video_length):
    background_songs = os.listdir(music_dir)
    song_rng = np.random.randint(0, len(background_songs))
    background_song = mpy.AudioFileClip(music_dir + '/' + background_songs[song_rng])
    background_audio = background_song

    extend_audio_factor = int(video_length / background_audio.duration) + 1  # number of times to repeat audio in order to have the correct length

    if video_length > background_audio.duration:
        print('extending audiotrack to match video.')
        for i in range(0, extend_audio_factor):
            song_rng = np.random.randint(0, len(background_songs))
            background_song = mpy.AudioFileClip(music_dir + '/' + background_songs[song_rng])
            background_audio = mpy.concatenate_audioclips([background_audio, background_song])

    background_audio = background_audio.set_duration(video_length)
    background_audio = volumex(background_audio, 0.1)

    return background_audio


def prepare_outro_clips(time):
    voice_rng = np.random.randint(0, len(google_voices))
    adjectives = ['amazing', 'marvelous', 'incredible', 'wonderful']
    outro_text = 'Thank you for watching! Please like and subscribe to support the channel, and above all, have an excellent day you ' + adjectives[np.random.randint(0, len(adjectives))] + ' people!'
    intro_text = textwrap.wrap(outro_text, width=80)
    intro_text = '\n'.join(intro_text)
    make_temp_voice(intro_text, voice_rng)
    outro_audio_clip = mpy.AudioFileClip(audio_temp, buffersize=1000000).set_start(time)  # load temp audio file
    outro_time = outro_audio_clip.duration

    outro_image_offset = height / 10
    outro_image = mpy.ImageClip(icon_assets_path + 'reddit_logo_verylarge_middle.png').set_position(('center', outro_image_offset)).set_duration(outro_time).set_start(time).resize(.40)
    outro_text_clip = mpy.TextClip(intro_text, color='white', fontsize=20).set_position(('center', outro_image.h + outro_image_offset + 20))
    outro_text_clip = outro_text_clip.set_start(time).set_duration(outro_time)

    return outro_text_clip, outro_audio_clip, outro_time, outro_image


def make_thumbnail(text, path, max_steps=30):
    print('Preparing tumbnail image.')
    asset_path = r'assets\thumbnail_images/'
    offset = 55
    text_clips = []
    blue_text_color = '#009dff'

    wrap_width = 40
    font_size = 70
    correct = False

    files = os.listdir(r'assets\thumbnail_images/')
    background_files = os.listdir(r'assets\thumbnail_backgrounds/')
    background = mpy.ColorClip((1280, 720), color=(26, 26, 27)).set_duration(3)
    background_image = vfx.mask_color(mpy.ImageClip(r'assets\thumbnail_backgrounds/' + background_files[np.random.randint(0, len(background_files))]), color=[26, 26, 27])

    image = vfx.mask_color(mpy.ImageClip(asset_path + files[np.random.randint(0, len(files))]).set_position(('right', 'center')).set_duration(background.duration), color=[26, 26, 27])

    title_text = mpy.TextClip('r/Askreddit asks:', fontsize=120, color=blue_text_color, font='Verdana-bold', stroke_color='black', stroke_width=100 * 0.06).set_position((50, 20))
    colors = ['#CF6363', '#71DEC6', 'yellow', 'orange']
    # max_steps = max_steps
    step = 0
    if text[-1] != '?':
        text += "?"

    while not correct:
        selected_color = colors[np.random.randint(0, len(colors))]
        text_clips = []
        max_xpos = 0
        xpos = offset
        ypos = title_text.h + offset
        wrapped_text = ' <NEWLINE> '.join(textwrap.wrap(text, width=wrap_width))
        word_split_text = wrapped_text.split(' ')
        quote = False

        for i in range(len(word_split_text)):
            # print(word_split_text[i])
            if word_split_text[i].__contains__('<NEWLINE>'):
                # print('newline detected')
                xpos = offset
                ypos += text_clips[-1].h
            else:
                # TODO: add a special color for anything in quotation marks

                if len(word_split_text[i]) > 5:
                    color = selected_color
                else:
                    color = 'white'
                text_clips.append(
                    mpy.TextClip((word_split_text[i] + ' '), font='Verdana-bold', fontsize=font_size, color=color, align='west', stroke_color='black', stroke_width=font_size * 0.06).set_duration(background.duration).set_pos(
                        (xpos, ypos)))

                xpos += text_clips[-1].w
                if xpos > max_xpos:
                    max_xpos = xpos

        step += 1
        # print('step: ', step, '   X and Y: ', max_xpos, ypos)
        max_ypos = 600
        if step >= max_steps:
            print('Max steps reached')
            break
        elif max_xpos > 1000:
            wrap_width -= 3
        elif ypos > max_ypos:
            font_size -= 3
            # print('font size = ', font_size)
        elif ypos < max_ypos - 100:
            font_size += 2
        elif xpos < 1000 - 100:
            wrap_width += 1
        else:
            correct = True

    clip_list = [background] + [title_text] + [background_image] + [image] + text_clips
    out = mpy.CompositeVideoClip(clip_list)
    out.save_frame(path + 'thumbnail.png', t=2)


def export_video(combinedvideo, vid_title):
    print('Exporting Video to file.')
    vid_title = prepare_title_for_win10_file(vid_title)
    combinedvideo.write_videofile(vid_title + '.mp4', fps=fps, threads=20)
    try:
        shutil.move(vid_title + '.mp4', release_path + vid_title + '/')
    except shutil.Error:
        pass


def upload_to_youtube(file_path, title):
    vtitle = title
    if title[-1] != '?':
        vtitle += '?'
    vtitle = 'R/Askreddit Asks: ' + vtitle
    if len(vtitle) > 100:
        vtitle = vtitle[0:97] + '...'
    tags = ['reddit', 'askreddit', 'toadfilms', 'updoot', 'stories'] + title.split()  # manual tags: reddit,askreddit,toadfilms,updoot,stories
    description = vtitle + '   \n Sub for the some of the best AskReddit content freshly handpicked for you!'
    channel = Channel()
    channel.login("client_secret_313020947931-jt1iobi0tetjqoprdub0osjb9r1fmulb.apps.googleusercontent.com.json", "credentials.storage")

    video = LocalVideo(file_path=file_path + title + ".mp4", title=vtitle)
    video.set_description(description)
    video.set_tags(tags)
    video.set_category(
        "entertainment")  # available categories: {'film': 1, 'animation': 31, 'autos': 2, 'vehicles': 2, 'music': 10, 'pets': 15, 'animals': 15, 'sports': 17, 'short movies': 18, 'travel': 19, 'events': 19, 'gaming': 20, 'videoblogging': 21, 'people': 22, 'blogs': 22, 'comedy': 34, 'entertainment': 24, 'news': 25, 'politics': 25, 'howto': 26, 'style': 26, 'education': 27, 'science': 28, 'technology': 28, 'nonprofits': 29, 'activism': 29, 'movies': 30, 'anime': 31, 'action': 32, 'adventure': 32, 'classics': 33, 'documentary': 35, 'drama': 36, 'family': 37, 'foreign': 38, 'horror': 39, 'sci-fi': 40, 'fantasy': 40, 'thriller': 41, 'shorts': 42, 'shows': 43, 'trailers': 44}
    video.set_thumbnail_path(file_path + 'thumbnail.png')
    print(video.get_thumbnail_path())
    video.set_privacy_status("public")

    channel.upload_video(video)
    channel.login("client_secret_313020947931-jt1iobi0tetjqoprdub0osjb9r1fmulb.apps.googleusercontent.com.json", "credentials.storage")
    channel.set_video_thumbnail(video=channel.fetch_uploads()[0], thumbnail_path=file_path + 'thumbnail.png')

# comment_list = remove_greater_depth_comments(submission.comments.list())
post_data = get_top_comments_and_replies(remove_greater_depth_comments(submission.comments.list()))
post_data = post_data[0:number_of_comments]

iv, ia, start_time, intro_image, auth_text = prepare_intro_clips(YouBOT_session_data['post_data'])

v, a, up_img, down_img, bottom_bar_img, auth, corner_logo, trans_clips, ups_text, t, = prepare_all_comment_clips(post_data['comments'].to_list(), post_data['replies'].to_list(), start_time)

ov, oa, ot, outro_image = prepare_outro_clips(t)
background = mpy.ColorClip((width, height), color=(26, 26, 27)).set_duration(t + outro_image.duration)

combined = mpy.CompositeVideoClip([background] + corner_logo + v + [iv] + [ov] + [auth_text] + [intro_image] + [outro_image] + up_img + down_img + bottom_bar_img + auth + ups_text + trans_clips).set_audio(
    mpy.CompositeAudioClip(a + [ia] + [oa]))

background_music = prepare_background_music(combined.duration)

final_audio = mpy.CompositeAudioClip([combined.audio, background_music])
combined = combined.set_audio(final_audio)

# title = subreddit_name + ', asks: ' + YouBOT_session_data['post_data'].title

tags = ['reddit', 'askreddit', 'toadfilms', 'updoot', 'stories']  # manual tags: reddit,askreddit,toadfilms,updoot,stories
description = 'Sub for the some of the best AskReddit content freshly handpicked for you!'
title = prepare_title_for_win10_file(YouBOT_session_data['post_data'].title)
path = r'releases\\'
file_path = path + title + r'\\'

# os.mkdir(path + title)
# make_thumbnail(title, file_path)
try:
    os.mkdir(path + title)
    make_thumbnail(title, file_path)
    # export_video(combined, file_path, title)
    # combined.write_videofile(title + '.mp4', fps=fps, threads=20)

except FileExistsError:
    # os.rmdir(path+title)
    make_thumbnail(title, file_path, max_steps=40)
    # combined.write_videofile(file_path+title + '.mp4', fps=fps, threads=20)

    # export_video(combined, file_path, title)

# combined.write_videofile(title + '.mp4')
export_video(combined, title)

upload_to_youtube(file_path, title)
