from aqt.qt import *
from anki.hooks import addHook
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from time import sleep
import threading, queue

threads = [None] * 2


def pos_change(input):
    pos_list = {}
    pos_list['verb'] = 'v.'
    pos_list['noun'] = 'n.'
    pos_list['adjective'] = 'adj.'
    pos_list['preposition'] = 'prep.'
    pos_list['adverb'] = 'adv.'
    pos_list['conjunction'] = 'conj.'

    for key, value in pos_list.items():
        if key == input:
            input = value
            break

    return input


def cambridge(driver, input):
    try:
        driver.get('https://dictionary.cambridge.org/zht/')
        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable((By.XPATH, '//input['
                                                                                                      '@id="searchword"]')))
        search = driver.find_element_by_xpath('//input[@id="searchword"]')
        search.send_keys(input)
        search.send_keys(Keys.RETURN)
        output = {}
        english_ex = []

        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.pr .entry-body__el')))
        entry = driver.find_elements_by_css_selector('.pr .entry-body__el')

        for en in entry:
            item = en.find_elements_by_css_selector('.pr .dsense')
            pos = en.find_element_by_css_selector("span.pos.dpos").text
            pos = pos_change(pos)

            for i in item:
                try:
                    grid = i.find_elements_by_css_selector('div.sense-body.dsense_b > div.def-block.ddef_block')
                    explains = {"ph": {"yes": "False"}}
                    for g in grid:
                        chi = g.find_element_by_css_selector('div.def-body.ddef_b')
                        eng = g.find_element_by_css_selector('div.def.ddef_d.db').text
                        english_ex.append(eng)
                        explain = chi.find_element_by_css_selector('span.trans.dtrans.dtrans-se').text
                        examples = chi.find_elements_by_css_selector('div.examp.dexamp')
                        sentense = []
                        for e in examples:
                            eng_sen = e.find_elements_by_css_selector('span.eg.deg')
                            chi_sen = e.find_elements_by_css_selector('span.dtrans.hdb')
                            for w in range(len(eng_sen)):
                                sentense.append(eng_sen[w].text)
                                sentense.append(chi_sen[w].text)
                        explains[explain] = sentense
                    if pos in output:
                        output[pos].append(explains)
                    else:
                        output[pos] = [explains]
                except:
                    print("no")

                try:
                    grid = i.find_elements_by_css_selector('div.pr.phrase-block.dphrase-block')
                    explains = {"ph": {"yes": "True", "mean": {}}}
                    for g in grid:
                        phrase = g.find_element_by_css_selector('span.phrase-title.dphrase-title').text
                        mean = g.find_elements_by_css_selector('div.def-block.ddef_block')
                        ph_explains = {}
                        explains["ph"]["mean"][phrase] = []
                        for m in mean:
                            chi = m.find_element_by_css_selector('div.def-body.ddef_b')
                            eng = m.find_element_by_css_selector('div.def.ddef_d.db').text
                            english_ex.append(eng)
                            explain = chi.find_element_by_css_selector('span.trans.dtrans.dtrans-se').text
                            examples = chi.find_elements_by_css_selector('div.examp.dexamp')
                            sentense = []
                            for e in examples:
                                eng_sen = e.find_elements_by_css_selector('span.eg.deg')
                                chi_sen = e.find_elements_by_css_selector('span.dtrans.hdb')
                                for w in range(len(eng_sen)):
                                    sentense.append(eng_sen[w].text)
                                    sentense.append(chi_sen[w].text)
                            ph_explains[explain] = sentense
                        explains["ph"]["mean"][phrase].append(ph_explains)
                    if pos in output:
                        output[pos].append(explains)
                    else:
                        output[pos] = [explains]
                except:
                    print("no")


    except Exception as e:
        output = None
        english_ex = None
    finally:
        return [output, english_ex]


def merriam(driver, input):
    try:
        driver.get('https://www.merriam-webster.com')
        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable((By.XPATH, '//input[@aria-label="Search"]')))
        search = driver.find_element_by_xpath('//input[@aria-label="Search"]')
        search.send_keys(input)
        search.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.entry-attr>div>.prs>.play-pron')))
        item = driver.find_elements_by_css_selector(".entry-attr>div>.prs>.play-pron")[0]
        dir = item.get_attribute("data-dir")
        file = item.get_attribute("data-file")
        audio_url = "http://media.merriam-webster.com/audio/prons/en/us/mp3/" + dir + "/" + file + ".mp3"
    except Exception as e:
        audio_url = None

    return audio_url


def start_c(word, queue):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument('blink-settings=imagesEnabled=false')

    prefs = {'profile.default_content_setting_values': {'images': 2}}
    chrome_options.add_experimental_option('prefs', prefs)
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) + '/chromedriver.exe'

    driver = webdriver.Chrome(executable_path=PATH, options=chrome_options)
    output = cambridge(driver, word)
    queue.put(output)
    driver.quit()


def start_m(word, queue):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument('blink-settings=imagesEnabled=false')

    prefs = {'profile.default_content_setting_values': {'images': 2}}
    chrome_options.add_experimental_option('prefs', prefs)
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) + '/chromedriver.exe'
    driver = webdriver.Chrome(executable_path=PATH, options=chrome_options)
    output = merriam(driver, word)
    queue.put(output)
    driver.quit()


def find(editor):
    word = editor.note.fields[0]
    if word:
        q = queue.Queue()
        threads[0] = threading.Thread(target=start_c, args=(word, q))
        threads[1] = threading.Thread(target=start_m, args=(word, q))
        threads[0].start()
        threads[1].start()

        q.join()

        tem1 = q.get()
        if type(tem1) is list:
            output = tem1[0]
            eng = tem1[1]
            link = q.get()
        else:
            link = tem1
            [output, eng] = q.get()

        if link is not None:
            editor.note.fields[0] += editor.urlToLink(link).strip()
            editor.loadNote()

            editor.note.fields[2] = link
            editor.loadNote()

        mean_text = ""
        text = ""
        count = 0

        if output is not None:
            for pos in output:
                for explains in output[pos]:
                    if explains["ph"]["yes"] == "False":
                        for explain in explains:
                            if explain != "ph":
                                text += pos + " " + explain + "<br>"
                                mean_text += pos + " " + explain + "<br>"
                                text += eng[count] + "<br>"
                                count += 1
                                for sentense in explains[explain]:
                                    text += sentense + "<br>"
                                text += "---" + "<br>"
                    else:
                        for word in explains["ph"]["mean"]:
                            text += "@" + word + "<br>"
                            for mean_arr in explains["ph"]["mean"][word]:
                                for mean in mean_arr:
                                    text += pos + " " + mean + "<br>"
                                    mean_text += pos + " " + mean + "<br>"
                                    text += eng[count] + "<br>"
                                    count += 1
                                    for sentense in mean_arr[mean]:
                                        text += sentense + "<br>"
                                    text += "---" + "<br>"

            text = text.replace('"', '\\"')

            editor.note.fields[3] = mean_text
            editor.loadNote()

            editor.note.fields[4] = text
            editor.loadNote()


# for explain in explains:
#     if explains[explain]["ph"] != "False":
#         text += explains[explain]["ph"] + "<br>"
#
#     else:
#         text += pos + " " + explain + "<br>"
#         text += eng[count] + "<br>"
#         count += 1
#         for sentense in explains[explain]["sen"]:
#             text += sentense + "<br>"
#         text += "---" + "<br>"
def setup_buttons(buttons, editor):
    both_button = editor.addButton(icon=os.path.join(os.path.dirname(__file__), "images", "magnifier.png"),
                                   cmd="",
                                   tip="妹的外掛",
                                   func=find,
                                   toggleable=False,
                                   label="",
                                   disables=False)

    buttons.append(both_button)
    return buttons


# c_output = ""
# m_output = ""
addHook("setupEditorButtons", setup_buttons)
