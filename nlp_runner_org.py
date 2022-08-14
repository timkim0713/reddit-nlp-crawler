
# nlp
import json
import praw
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize.regexp import RegexpTokenizer
from io import StringIO
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.stem import *
import spacy
import string
import sys
# crawling
import main_org
# data processing


sw_f = open("sw.json")
sw = set(stopwords.words('english') + json.load(sw_f))
sentiment = SentimentIntensityAnalyzer()
tokenizer = RegexpTokenizer("\s+", gaps=True)
stemmer = PorterStemmer()
nlp = spacy.load("en_core_web_sm")  # entity extraction
sim = spacy.load("en_core_web_md")  # word vectorization
punct_list = string.punctuation
keydict_list = {}


def makePostList(topic):
    reddit = praw.Reddit(client_id='4qdOoP14AUe-SEN6rClKgg',
                         client_secret='I1UIBGpdg0ReVxyjxwomjR_vLSzlbg',
                         username='prawtutorial0803',
                         password='cookies0803',
                         user_agent='chaec0803')
    subreddit = reddit.subreddit(topic)
    hot_python = subreddit.hot(limit=100)
    subreddit_objs = [submission for submission in hot_python]
    posts = list()
    fdist = nltk.FreqDist()

    for submission in subreddit_objs:
        if not submission.stickied:  # not stickied
            submission_dict = dict()
            posts.append(submission_dict)
            submission_dict["id"] = str(submission.id)
            submission_dict["title"] = submission.title
            submission_dict["ups"] = submission.ups
            submission_dict["downs"] = submission.downs
            submission_dict["content"] = submission.selftext
            submission.comments.replace_more(limit=0)
            comments_list = list()
            submission_dict["comments"] = comments_list
            submission_dict["post link"] = submission.permalink
            fdist += nltk.FreqDist(nltk.word_tokenize(submission.title +
                                   " " + submission.selftext))
            index = 0

            for comment in submission.comments.list():
                comment_dict = dict()
                comments_list.append(comment_dict)
                comment_dict["dict Id"] = index
                comment_dict["Comment Id"] = comment.id
                comment_dict["Parent Id"] = comment.parent().id
                comment_dict["content"] = comment.body
                replies = list()
                comment_dict["replies"] = replies
                for com in comments_list:
                    if comment.parent() == com["Comment Id"]:
                        com["replies"].append(index)
                fdist += nltk.FreqDist(nltk.word_tokenize(comment.body))
                index += 1

    final_fdist = nltk.FreqDist()
    for word in fdist:
        if word.lower() not in sw_f and word not in punct_list:
            final_fdist[word] = fdist[word]

    return posts, final_fdist


def make_pos_cfdist(keypost_list):
    pos_cfdist = nltk.ConditionalFreqDist()
    for post in keypost_list:
        comment_set = set()
        contents = nltk.word_tokenize(post["title"] + " " + post["content"])
        pos_contents = nltk.pos_tag(contents, tagset="universal")
        for word, pos in pos_contents:
            pos_cfdist[word][pos] += 1
        for com in post["comments"]:
            contents = nltk.word_tokenize(com["content"])
            pos_contents = nltk.pos_tag(contents, tagset="universal")
            if com["dict Id"] not in comment_set:
                comment_set.add(com["dict Id"])
                for word, pos in pos_contents:
                    pos_cfdist[word][pos] += 1
    return pos_cfdist


def associativityScore(word1, word2, postDict_list):
    score = 0
    word1_commentids = set()
    word2_commentids = set()
    for post in postDict_list:
        for comment in post["comments"]:
            if word1 in comment["content"]:
                word1_commentids.add(comment["dict Id"])
            if word2 in comment["content"]:
                word2_commentids.add(comment["dict Id"])
    # coming from the same comment or #coming from replies to the same comment or one was in reply to the comment that the other was in

    word1_commentids = sorted(word1_commentids)
    word2_commentids = sorted(word2_commentids)
    # t = 0
    idx1, idx2 = 0, 0
    while (idx1 != len(word1_commentids) and idx2 != len(word2_commentids)):
        if (word1_commentids[idx1] == word2_commentids[idx2]):
            score += 2
            idx1 += 1
            idx2 += 1
        elif (word1_commentids[idx1] > word2_commentids[idx2]):
            idx2 += 1
        else:
            idx1 += 1

    for post in postDict_list:  # 1000
        for comment in post["comments"]:  # 100
            len_c_w1 = len(comment["replies"]) + len(word1_commentids)
            len_c_w2 = len(comment["replies"]) + len(word2_commentids)
            set_c_w1 = len(set(comment["replies"] + word1_commentids))
            set_c_w2 = len(set(comment["replies"] + word2_commentids))
            if set_c_w1 < len_c_w1 and set_c_w2 < len_c_w2:
                score += 1
            if comment["Comment Id"] in word1_commentids and set_c_w2 < len_c_w2:
                score += 1
            if comment["Comment Id"] in word2_commentids and set_c_w1 < len_c_w1:
                score += 1
    # both are lemmas of same synset (top priority)

    try:
        syn1 = wn.synsets(word1.lower())
        syn2 = wn.synsets(word2.lower())
        syn1.sort()
        syn2.sort()
        # t = 0
        idx1, idx2 = 0, 0
        while (idx1 != len(syn1) and idx2 != len(syn2)):
            if (syn1[idx1] == syn2[idx2]):
                score += 5
                idx1 += 1
                idx2 += 1
            elif (syn1[idx1] > syn2[idx2]):
                idx2 += 1
            else:
                idx1 += 1
    except (AttributeError, ValueError):
        print(word1, word2)
    return score


def get_wiki_def(word):
    old_stdout = sys.stdout
    new_stdout = StringIO()
    sys.stdout = new_stdout
    # word_wiki = wikiscrape.wiki(word)
    output = new_stdout.getvalue()
    sys.stdout = old_stdout
    lines = output.split("\n")
    for i in range(len(lines)):
        if "Wikipedia page loaded successfully" in lines[i]:
            if i + 3 < len(lines) - 1:
                return nltk.sent_tokenize(lines[i + 3])
    return "blank"


def makeNE(keypost_list, fdist):
    ne_list = []
    for post in keypost_list:
        doc_post = nlp(post["title"] + post["content"])
        for entity in doc_post.ents:
            if not entity.text.isalpha():
                continue
            if len(entity.text.split()) == 2 and entity.text[0].isupper():
                ne_list.append(entity.text)
            elif fdist[entity.text.lower()] < fdist[entity.text]:
                add = True
                for syn in wn.synsets(entity.text):
                    if syn.pos() != "n":
                        add = False
                        break
                if add:
                    ne_list.append(entity.text)

        for com in post["comments"]:
            doc_com = nlp(com["content"])
            for entity in doc_com.ents:
                if not entity.text.isalpha():
                    continue
                if len(entity.text.split()) == 2 and entity.text[0].isupper() and entity.text.isalpha():
                    ne_list.append(entity.text)
                elif fdist[entity.text.lower()] < fdist[entity.text] and entity.text.isalpha():
                    add = True
                    for syn in wn.synsets(entity.text):
                        if syn.pos() != "n":
                            add = False
                            break
                    if add:
                        ne_list.append(entity.text)

    return list(set(ne_list))


def listTwentyWords(scores, keyword, topic):
    length = 0
    words = {}
    for word, score in scores:
        if length >= 20:
            break
        if word.lower() in keyword.lower() or word.lower() in topic.lower() or keyword.lower() in word.lower() or topic.lower() in word.lower() or not word.isalpha():
            continue
        add = True
        word_token = sim(word)[0]
        for chosen in words:
            chosen_token = sim(chosen)[0]
            sim_score = word_token.similarity(chosen_token)
            if sim_score > 0.7:
                add = False
                break
        if add:
            words[word] = []
            length += 1
        else:
            words[chosen].append(word)
    return words


def keyword_comments(postList, keywords):
    result = []
    fdist = nltk.FreqDist()
    post_set = set()
    score = 0
    length = 0
    for post in postList:
        add = False
        content = post["title"] + " " + post["content"]
        content_words = nltk.word_tokenize(content)
        for keyword in keywords:
            if len(keyword.split()) > 1 and keyword.lower() in content.lower():
                add = True
            elif keyword.lower() in content:
                add = True
            if add:
                contents = nltk.sent_tokenize(content)
                length = len(contents)
                s_score = 0
                for s in contents:
                    s_score += sentiment.polarity_scores(s)["compound"]
                score += s_score/length
                result.append(post)
                post_set.add(post["id"])
                fdist += nltk.FreqDist(content_words)
                break

        for com in post["comments"]:
            add = False
            content = com["content"]
            content_words = nltk.word_tokenize(content)
            for keyword in keywords:
                if len(keyword.split()) > 1 and keyword.lower() in content.lower():
                    add = True
                elif keyword.lower() in content:
                    add = True
                if add:
                    if post["id"] not in post_set:
                        post_set.add(post["id"])
                        result.append(post)
                    contents = nltk.sent_tokenize(content)
                    length = len(contents)
                    s_score = 0
                    for s in contents:
                        s_score += sentiment.polarity_scores(s)["compound"]
                    score += s_score / length
                    fdist += nltk.FreqDist(content_words)
                    break
        if score != 0:
            score /= length

    result_fdist = nltk.FreqDist()

    for word in fdist:
        if word.lower() not in sw and word not in punct_list:
            result_fdist[word] = fdist[word]

    return result, result_fdist, score


def makeHighlight(pos_tags, comwords, pos_cfdist):
    highlight_indices = set()
    for keyword in comwords:
        length = len(keyword.split())
        for i in range(0, len(pos_tags) - length, length):
            words = ' '.join([w for w, pos in pos_tags[i: i + length]])
            if not words.isalpha() or words.lower() in sw or words in punct_list:
                continue
            word = pos_tags[i][0]
            pos = pos_tags[i][1]
            sim_score = 0
            """if length == 1:
                sim_score = sim(keyword)[0].similarity(sim(words)[0])"""
            if keyword.lower() == words.lower() or sim_score > 0.7 or words.lower() in keyword.lower() or keyword.lower():
                highlight_indices.update(set(range(i, i + length)))
                for j in range(1, 4):
                    if i - j > 0:
                        w2, pos2 = pos_tags[i - j]
                        polarity = sentiment.polarity_scores(w2)
                        if (pos2 == "ADJ" or pos2 == "ADV") and abs(polarity["compound"]) > 0.05:
                            highlight_indices.add(i - j)
                    if i + j < len(pos_tags) - length:
                        w2, pos2 = pos_tags[i + j + length]
                        polarity = sentiment.polarity_scores(w2)
                        if (pos2 == "ADJ" or pos2 == "ADV") and abs(polarity["compound"]) > 0.05:
                            highlight_indices.add(i + j + length)
            polarity = sentiment.polarity_scores(word)
            polarity1 = sentiment.polarity_scores(stemmer.stem(word).lower())
            if abs(polarity["pos"] - polarity["neg"]) > 0.3 or abs(abs(polarity1["pos"] - polarity1["neg"]) > 0.3):
                freq_pos = pos_cfdist[word]
                if freq_pos.N() > 1 and freq_pos.most_common(1)[0][0] == pos:
                    highlight_indices.add(i)
                else:
                    continue
    return list(highlight_indices)


def getPolarity(content):
    post_score = 0
    ss = nltk.sent_tokenize(content)
    for s in ss:
        post_score += sentiment.polarity_scores(s)["compound"]
    post_score /= len(ss)
    return post_score


def toggleComments(words, keyDict_list, comwords, pos_cfdist):
    keywords_result = [0]

    for post in keyDict_list:
        add = False
        com_done = set()
        for word in words:
            add = False
            content = post["title"] + " " + post["content"]
            content_words = nltk.word_tokenize(content)
            if len(word.split()) > 1 and word.lower() in content.lower():
                add = True
            else:
                for w in content_words:
                    if word.lower() == w.lower():
                        add = True
                        break
            if add:
                pos_tags = nltk.pos_tag(content_words, tagset="universal")
                highlight_indices = makeHighlight(
                    pos_tags, comwords, pos_cfdist)
                post_score = getPolarity(post["title"])
                keywords_result[0] += post_score
                keywords_result.append(
                    (content, post["id"], post["post link"], post_score, highlight_indices))
                break

        for com in post["comments"]:
            add = False
            if com["dict Id"] in com_done:
                continue
            else:
                com_done.add(com["dict Id"])
            content = nltk.word_tokenize(com["content"])
            for word in keywords:
                if len(word.split()) > 1 and word.lower() in com["content"].lower():
                    add = True
                else:
                    for w in content:
                        if word.lower() == w.lower():
                            add = True
                            break
                if add:
                    pos_tags = nltk.pos_tag(content, tagset="universal")
                    highlight_indices = makeHighlight(
                        pos_tags, comwords, pos_cfdist)
                    post_score = getPolarity(com["content"])
                    keywords_result[0] += post_score
                    keywords_result.append(
                        (com["content"], com["Comment Id"], post["post link"], post_score, highlight_indices))
                    break

    keywords_result[0] = keywords_result[0]/(len(keywords_result) - 1)
    return keywords_result


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    topic, keyword = main_org.proc1()

    #topic = input("What topic would you like to browse on Reddit?: ")
    #keyword = input("What keyword would you like to search upon this topic?: ")

    print("Prawling Data")
    postDict_list, fdist = makePostList(topic)
    with open("postDict_list.json", "w") as outfile:
        json.dump(postDict_list, outfile)
    with open("fdist.json", "w") as outfile:
        json.dump(fdist, outfile)

    f = open("postDict_list.json", "r")
    postDict_list = json.load(f)

    f = open("fdist.json", "r")
    temp_fdist = json.load(f)
    fdist = nltk.FreqDist()
    for word in temp_fdist:
        fdist[word] = temp_fdist[word]

    print("making pos_cfdist")
    pos_cfdist = make_pos_cfdist(postDict_list)
    with open("pos_cfdist.json", "w") as outfile:
        json.dump(pos_cfdist, outfile)

    print("making ne_list")
    ne_list = makeNE(postDict_list, fdist)
    with open("ne_list.json", "w") as outfile:
        json.dump(ne_list, outfile)

    f = open("pos_cfdist.json", "r")
    pos_cfdist = json.load(f)

    f = open("ne_list.json", "r")
    ne_list = json.load(f)

    f = open("buzzwords.json")
    buzzwords = json.load(f)
    top_words = [word for word,
                 freq in fdist.most_common(int(len(fdist) * 0.3))]

    print("scoring words")
    scores = []

    token_key = sim(keyword)
    for word in top_words:
        if (word[0].isupper() and word.lower() in top_words) or word.lower() in buzzwords or word.lower() in sw:
            continue
        score = associativityScore(word, keyword, postDict_list) * 0.5
        print(word, score)
        for ne in ne_list:
            if word in ne.split():
                continue
        sim_score = token_key.similarity(sim(word)[0])
        if sim_score > 0.5:
            print(word)
            score += 500 * sim_score
        scores.append((word, score))

    print("scoring ne_list")
    ne_defs = {}

    for ne in ne_list:
        score = 0
        freq = 0
        words = ne.split()
        max_score = 0
        for word in words:
            score += associativityScore(word, keyword, postDict_list) * 0.5
            sim_score = token_key.similarity(sim(word)[0])
            if sim_score > max_score:
                max_score = sim_score

        ent_wiki = get_wiki_def(ne)

        if (isinstance(ent_wiki, list)) and len(ent_wiki) > 0:
            print(ne, ent_wiki[0])
            ne_defs[ne] = ent_wiki
            definition = ent_wiki[0]
            tokens = nlp(definition)
            max_score = 0
            for tok in tokens:
                if "obj" in tok.dep_:
                    token_word = sim(tok.text)[0]
                    sim_score = token_key.similarity(token_word)
                    if sim_score > max_score:
                        max_score = sim_score
        score += 500 * max_score
        score += 50
        scores.append((ne, score))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    with open("ne_defs.json", "w") as outfile:
        json.dump(ne_defs, outfile)
    with open("scores.json", "w") as outfile:
        json.dump(scores, outfile)

    f = open("postDict_list.json", "r")
    postDict_list = json.load(f)

    f = open("fdist.json", "r")
    temp_fdist = json.load(f)
    fdist = nltk.FreqDist()
    for word in temp_fdist:
        fdist[word] = temp_fdist[word]

    f = open("pos_cfdist.json", )
    temp_pos_cfdist = json.load(f)
    pos_cfdist = nltk.ConditionalFreqDist()

    for word in temp_pos_cfdist:
        pos_cfdist[word] = nltk.FreqDist()
        for entry in temp_pos_cfdist[word]:
            pos_cfdist[word][entry] = temp_pos_cfdist[word][entry]

    f = open("ne_list.json", "r")
    ne_list = json.load(f)

    f = open("buzzwords.json", "r")
    buzzwords = json.load(f)

    f = open("scores.json", "r")
    scores = json.load(f)

    f = open("ne_defs.json", "r")
    ne_defs = json.load(f)

    keywords_dict = listTwentyWords(scores, keyword, topic)
    keywords = list(keywords_dict.keys())
    keywords.append("politics")
    keydict_list, key_fdist, total_pscore = keyword_comments(
        postDict_list, keywords)
    print(keywords)
    with open("keydict_list.json", "w") as outfile:
        json.dump(keydict_list, outfile)

    with open("key_fdist.json", "w") as outfile:
        json.dump(key_fdist, outfile)

    print(total_pscore)
    for post in keydict_list:
        print(post["title"])

    keyword_toggle = {}
    for key in keywords:
        comwords = set()
        comwords.update(set(key.split() + topic.split()))

        token_topic = sim(topic)[0]
        token_key = sim(key)[0]
        for ne in ne_list:
            token_ne = sim(ne)[0]
            sim_key = token_key.similarity(token_ne)
            sim_topic = token_topic.similarity(token_ne)
            if sim_key > 0.5 or sim_topic > 0.5:
                print(ne, sim_key, sim_topic)
                comwords.add(ne)
        for word in list(key_fdist.keys())[:int(len(key_fdist) * 0.3)]:
            token_word = sim(word)[0]
            sim_key = token_key.similarity(token_word)
            sim_topic = token_topic.similarity(token_word)
            if sim_key > 0.5 or sim_topic > 0.5:
                print(word, sim_key, sim_topic)
                comwords.add(word)
        print(comwords)
        result = toggleComments(keywords, keydict_list,
                                list(comwords), pos_cfdist)

        avg_score = result[0]
        keyword_toggle[word] = result
        reviews = result[1:11]
        for rev in reviews:
            content, user_id, post_link, post_score, highlight_indices = rev
            print(post_score)
            for i, word in enumerate(nltk.word_tokenize(content)):
                if i in highlight_indices:
                    print("\"\"{}\"\"".format(word), end=" ")
                else:
                    print(word, end=" ")
            print()
        print()
