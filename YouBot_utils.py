import math, cv2
import tkinter as tk
import re
from gtts import gTTS



def rotation_movement_math(rotation, movement_step):
    # define internal rotation var and predefine other vars
    new_rot = rotation
    change_x, change_y = 0, 0

    # make rotation var positive all the time
    if 0 > new_rot > -360:
        new_rot = 360 + rotation

    def rotation_math(rot, move_step):
        if 0 > rot > -360:
            rot = -rot

        cos_math = math.cos(math.radians(rot))
        sin_math = math.sin(math.radians(rot))

        if cos_math < 0:
            cos_math = -cos_math
        if sin_math < 0:
            sin_math = -sin_math

        x_change = math.sqrt(move_step ** 2 - (cos_math * move_step) ** 2)
        y_change = math.sqrt(move_step ** 2 - (sin_math * move_step) ** 2)

        return x_change, y_change

    # return an x and y change so that their vector sums equal the desired move step
    x_change, y_change = rotation_math(new_rot, movement_step)

    # here we say that depending on what the rotation, change x and y according to these rules
    if 360 >= new_rot > 270:
        change_y = -y_change
        change_x = +x_change
    elif 270 >= new_rot > 180:
        change_y = +y_change
        change_x = +x_change
    elif 180 >= new_rot > 90:
        change_y = +y_change
        change_x = -x_change
    elif 90 >= new_rot >= 0:
        change_y = -y_change
        change_x = -x_change

    return change_x, change_y


class VoiceTest():

    def __init__(self):
        root = tk.Tk()
        root.geometry('400x200')
        root.title("Google's Speech Application")
        lab1 = tk.Label(root, text='Text To Speech Convertor', bg='powder blue', fg='black', font=('arial 16 bold')).pack()
        root.config(background='powder blue')

        lab2 = tk.Label(root, text='Enter text', font=('arial 16'), bg='powder blue', fg='black').pack()
        self.mytext = tk.StringVar()

        ent1 = tk.Entry(root, tex=self.mytext, font=('arial 13')).pack()

        but1 = tk.Button(root, text='Convert', width=20, bg='brown', fg='white', command=self.fetch).place(x=125, y=100)

        but2 = tk.Button(root, text='Play file', width=20, bg='brown', fg='white', command=self.play).place(x=125, y=140)

        root.mainloop()

    def fetch(self):
        language = 'en-au'
        myob = gTTS(text=self.mytext.get(), lang=language, slow=False, )
        myob.save('Voice1.mp3')

    def play(self):
        from pygame import mixer
        mixer.init()
        mixer.music.load("Voice1.mp3")
        mixer.music.play()


def remove_greater_depth_comments(comments_list):
    items_at_zero_depth = []

    for i,comment in enumerate(comments_list):
        if comment.depth == 0:
            items_at_zero_depth.append(comment)

    return items_at_zero_depth

def abs_dif(a, b):
    if a < 0:
        a = -a
    if b < 0:
        b = -b
    t = a - b
    if t < 0:
        t = -t
    return t


alphabets = "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"


def find_top(comment):
    print(comment)
    interesting_comments = []
    interesting_comment = None
    # select most interesting comment
    for i in range(0, len(comment.replies.list())):
        try:
            if comment.replies[i].ups > 0:  # comment.ups:
                print(comment.replies[i].ups)
                interesting_comment = comment.replies[i]
                interesting_comments.append(interesting_comment)
            for i in range(0, len(interesting_comment.replies.list())):
                if interesting_comment.replies[i].ups > interesting_comment.ups:
                    interesting_comment = interesting_comment.replies[i]
                    interesting_comments.append(interesting_comment)

            print(interesting_comment)

            for i in range(0, len(interesting_comment.replies.list())):
                if interesting_comment.replies[i].ups > interesting_comment.ups:
                    interesting_comment = interesting_comment.replies[i]
                    interesting_comments.append(interesting_comment)
        except IndexError:
            pass

    return interesting_comments


def round_ups(ups):
    ups_rounded = ups
    if ups > 1000:
        ups = round(ups, -3)
        ups_txt = str(ups)
        ups_rounded = ups_txt[0:len(ups_txt) - 3] + 'K'

    return ups_rounded


def split_into_sentences(text):
    text = " " + text + "  "
    # text = text.replace("\n"," ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    text = text.replace('...', '<ELIPSE>')
    if "Ph.D" in text: text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", text)
    text = re.sub(" " + suffixes + "[.]", " \\1<prd>", text)
    text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
    if "”" in text: text = text.replace(".”", "”.")
    if "\"" in text: text = text.replace(".\"", "\".")
    if "!" in text: text = text.replace("!\"", "\"!")
    if "?" in text: text = text.replace("?\"", "\"?")
    text = text.replace(".", ".<stop>")
    text = text.replace(",", ",<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("\n", "\n<stop>")

    text = text.replace(":", ":<stop>")

    text = text.replace("<prd>", ".")
    text = text.replace('<ELIPSE>', '...')
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


class VoiceTest():

    def __init__(self):
        root = tk.Tk()
        root.geometry('400x200')
        root.title("Google's Speech Application")
        lab1 = tk.Label(root, text='Text To Speech Convertor', bg='powder blue', fg='black', font=('arial 16 bold')).pack()
        root.config(background='powder blue')

        lab2 = tk.Label(root, text='Enter text', font=('arial 16'), bg='powder blue', fg='black').pack()
        self.mytext = tk.StringVar()

        ent1 = tk.Entry(root, tex=self.mytext, font=('arial 13')).pack()

        but1 = tk.Button(root, text='Convert', width=20, bg='brown', fg='white', command=self.fetch).place(x=125, y=100)

        but2 = tk.Button(root, text='Play file', width=20, bg='brown', fg='white', command=self.play).place(x=125, y=140)

        root.mainloop()

    def fetch(self):
        language = 'en-au'
        myob = gTTS(text=self.mytext.get(), lang=language, slow=False, )
        myob.save('Voice1.mp3')

    def play(self):
        from pygame import mixer
        mixer.init()
        mixer.music.load("Voice1.mp3")
        mixer.music.play()


def prepare_title_for_win10_file(text):
    return text.replace('?', "").replace(':', "").replace('<', "").replace('>', "").replace('|', "").replace('/', "").replace(r'\ ', '').replace('"', "'").replace('*','')


def angle_find(x1, y1, x2, y2):
    angle = 0

    if x2 > x1 and y2 > y1:
        d_x = abs_dif(x1, x2)
        d_y = abs_dif(y1, y2)
        angle = math.degrees(math.atan(d_x / (d_y + 1)))
    elif x1 > x2 and y1 > y2:
        d_x = abs_dif(x1, x2)
        d_y = abs_dif(y1, y2)
        angle = math.degrees(math.atan(d_x / (d_y + 1))) + 180
    elif x2 > x1 and y1 > y2:
        d_x = abs_dif(x1, x2)
        d_y = abs_dif(y1, y2)
        angle = math.degrees(math.atan(d_y / (d_x + 1))) + 90
    elif x1 > x2 and y2 > y1:
        d_x = abs_dif(x1, x2)
        d_y = abs_dif(y1, y2)
        angle = math.degrees(math.atan(d_y / (d_x + 1))) + 270

    return angle


def return_percent(small, large, string):
    try:
        percent = string + ": " + str(round(((small / large) * 100), 2)) + "%"
    except ZeroDivisionError:
        print("Division by 0 error!")
        percent = "error"
    return percent


def round_ups(ups):
    ups_rounded = ups
    if ups > 1000:
        ups = round(ups, -3)
        ups_txt = str(ups)
        ups_rounded = ups_txt[0:len(ups_txt) - 3] + 'K'

    return ups_rounded
