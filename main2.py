# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# PYTHON 3
import asyncio
import tkinter as tk
import sys
from io import StringIO
from collections import defaultdict
import string
from threading import Timer


from nlp_runner2 import nlp_runner
#
root = tk.Tk()
root.title("NLP Project")
canvas1 = tk.Canvas(root, width=1200, height=1500,  relief='raised')
canvas1.pack()

canvas1.create_text(600, 50, fill="darkblue", font="Times 40 italic bold",
                    text="Daniel's Reddit NLP Project")

label2 = tk.Label(
    root, text='What topic would you like to browse on Reddit?: ')
label2.config(font=('helvetica', 20))
canvas1.create_window(600, 200, window=label2)

entry1 = tk.Entry(root)
canvas1.create_window(600, 250, window=entry1)

label3 = tk.Label(
    root, text='What keyword would you like to search upon this topic?: ')
label3.config(font=('helvetica', 20))
canvas1.create_window(600, 350, window=label3)

entry2 = tk.Entry(root)
canvas1.create_window(600, 400, window=entry2)


# PASS "entry1 & entry2 to nlp_runner"
# print(entry1, entry2, "from main2")

# nlp_proj = nlp_runner(entry1.get(), entry2.get()).main()
# print("nlp ran.", nlp_proj)

# output = nlp_proj
# # RUN nlp_runner & wait for result from nlp_runner
# # It should return an output like below example.
# output = {"archer":
#           [0.55, ["An San is a great archer!",
#                   "She won three gggg medals for archery",
#                   "She is like a Korean Artemis."],
#            [[4, 5], [1, 2, 3, 4], [4, 5, 6]]],
#           "medals": [0.9,
#                      ["She won three gold medals for archery",
#                       "She may be the first one to win three gold medals"],
#                      [[2, 3, 4, 5], [4, 5, 6, 7, 8, 9]]]
#           }


# A / AA -> list of output
A = []
chk = {}
buttons = []
AA = []
gobackbuttonwin = None
output = {}


async def handle_reddit_crawler():
    # IMPORTANT  main.py __main__ goes here

    print("handling reddit crawler.......5 sec")
    await asyncio.sleep(5)
    print("5 seconds finished!")

    global output
    output = {"archer":
              [0.55, ["An San is a great archer!",
                      "She won three gggg medals for archery",
                      "She is like a Korean Artemis."],
               [[4, 5], [1, 2, 3, 4], [4, 5, 6]]],
              "medals": [0.9,
                         ["She won three gold medals for archery",
                          "She may be the first one to win three gold medals"],
                         [[2, 3, 4, 5], [4, 5, 6, 7, 8, 9]]]
              }

    return output


def deleteButtons():
    print("deleting...!")
    global buttons
    for button in buttons:
        canvas1.delete(button)

    buttons = []


def display():
    global AA
    global gobackbuttonwin
    if len(AA):
        for com in AA:
            canvas1.delete(com)
        AA = []
        canvas1.delete(gobackbuttonwin)
    for i in range(len(A)):
        buttonKey = tk.Button(text=A[i], command=lambda x=i: showComments(A[x]),
                              bg='brown', fg='black', font=('helvetica', 15, 'bold'))
        buttonKeyWindow = canvas1.create_window(
            600, 300+i * 40, window=buttonKey)
        buttons.append(buttonKeyWindow)


def showComments(key):
    i = 0
    deleteButtons()
    global gobackbuttonwin
    goback2 = tk.Button(text="Go Back", command=lambda: display(),
                        bg='brown', fg='black', font=('helvetica', 15, 'bold'))
    gobackbuttonwin = canvas1.create_window(100, 50, window=goback2)

    # if key not in chk or chk[key] == 0:
    chk[key] = 1
    for m, j in enumerate(output[key][1]):
        sentence = output[key][1][m].split()

        psum = [0] * (len(sentence)+5)
        psum[0] = len(sentence[0]) + 17
        for k in range(1, len(sentence)):
            psum[k] += psum[k-1] + len(sentence[k]) + 17

        index_label = canvas1.create_text(
            160, 280+35*i, font="Times 20 italic bold", text=str(m+1) + ". ")

        AA.append(index_label)

        for wordIndex in range(0, len(sentence)):
            handled_spacing = 0
            if wordIndex == 0:
                handled_spacing = 200
            else:
                handled_spacing = 200 + psum[wordIndex-1]*2.8

            if(wordIndex not in output[key][2][m]):
                text = canvas1.create_text(handled_spacing, 280+35*i, font="Times 20 italic bold",
                                           text=sentence[wordIndex])
            else:
                if output[key][0] < 0.3:
                    text = canvas1.create_text(handled_spacing, 280+35*i, font="Times 20 italic bold",
                                               text=sentence[wordIndex], fill="red")
                else:
                    text = canvas1.create_text(handled_spacing, 280+35*i, font="Times 20 italic bold",
                                               text=sentence[wordIndex], fill="blue")

            AA.append(text)
        i += 1
    # else:
    # chk[key] = 0
    # display()
        # 현재 display 된 코멘트 지우기


def deleteLabelsEntriesButton():
    label2.after(0, label2.destroy())
    label3.after(0, label3.destroy())
    entry1.after(0, entry1.destroy())
    entry2.after(0, entry2.destroy())
    enter.after(0, enter.destroy())


def createLoadingScreen():

    deleteLabelsEntriesButton()
    loading_text = canvas1.create_text(400, 200, fill="red", font="Times 25 italic bold",
                                       text="Processing... (Please wait a few minutes...)")

    return loading_text


async def handleSearch():
    print("HANDLING SEARCH")

    loading_text = createLoadingScreen()

    output = await handle_reddit_crawler()
    global A
    A = list(output.keys())
    canvas1.delete(loading_text)

    x1 = entry1.get()
    x2 = entry2.get()

    label4 = tk.Label(root, text='The result of the topic: "' +
                      x1 + '" and keyword: "'+x2+'" is shown below...', font=('helvetica', 20))

    label5 = tk.Label(root, text='Highlighted Words', font=('helvetica', 14))
    label6 = tk.Label(root, text='Negative',  fg="red",
                      font=('helvetica', 14))
    label7 = tk.Label(root, text='Positive',  fg="blue",
                      font=('helvetica', 14))

    canvas1.create_window(600, 150, window=label4)
    canvas1.create_window(600, 200, window=label5)
    canvas1.create_window(560, 230, window=label6)
    canvas1.create_window(640, 230, window=label7)

    deleteLabelsEntriesButton()
    display()


enter = tk.Button(text='Search', command=lambda: asyncio.run(handleSearch()),
                  bg='brown', fg='black', font=('helvetica', 16, 'bold'))
canvas1.create_window(600, 500, window=enter)


root.mainloop()


# Create 10-20 buttons (keywords)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# make highlights better
# make sentimentAnalyzer with wordnet emotions, vader, sim --> dataset
