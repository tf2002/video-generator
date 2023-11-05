import time,os,utils
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils import config

# Huge credits to redianmarku
# https://github.com/redianmarku/tiktok-autouploader

def upload_to_tiktok(name,title):
    bot = utils.create_bot(headless=False) # Might not work in headless mode
    bot.set_window_size(1920, 1080*2) # Ensure upload button is visible, does not matter if it goes off screen

    # Fetch main page to load cookies, sometimes infinte loads, except and pass to keep going
    try:
        bot.get('https://www.tiktok.com/')
    except:
        pass

    for cookie in config['tiktok_cookies'].split('; '):
        data = cookie.split('=')
        bot.add_cookie({'name':data[0],'value':data[1]})

    try:
        bot.get('https://www.tiktok.com/creator-center/upload')
    except:
        pass
    time.sleep(10)
    bot.switch_to.frame(bot.find_element(By.CSS_SELECTOR, "[data-tt='Upload_index_iframe']"))

    # Wait for 1 second
    time.sleep(5)

    # Upload video
    #file_uploader = WebDriverWait(bot, 100).until(EC.presence_of_element_located((By.TAG_NAME, 'input')))
    file_uploader = bot.find_element(by=By.TAG_NAME, value="input")
    #p = os.getcwd()+f'\\render\\{name}.mp4'#
    p = r"E:\VideoGenerator\video-generator\OutputVideos\version_2.mp4"
    file_uploader.send_keys(p)

    # Focus caption element
    caption = WebDriverWait(bot, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.public-DraftStyleDefault-block.public-DraftStyleDefault-ltr')))
    ActionChains(bot).click(caption).perform()

    # Input title & tags
    
    print('📝 Writing title & tags...')
    time.sleep(0.6)
    print(title)
    if len(title) < 70:
        try:
            ActionChains(bot).send_keys(title+" ").perform()
            tags = ["quiz","wwm","frage"]
            for tag in tags:
                ActionChains(bot).send_keys("#"+tag).perform()
                WebDriverWait(bot, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.mentionSuggestions')))
                ActionChains(bot).send_keys(Keys.RETURN).perform()
                time.sleep(0.05)
        except:
            pass

    try:
        print("⏱ Waiting to post...")
        # Scroll to bottom to make sure post button is visible
        print("start scroll")
        #bot.execute_script("window.scrollBy(0, 500);")
        bot.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.CONTROL, Keys.END)
        print("end scroll")
        # Wait for 'Post' button to be active, then click
        time.sleep(2)
        post = WebDriverWait(bot, 300).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.btn-post>button:not([disabled])')))
        print(post.text)
        time.sleep(0.4)
        bot.execute_script("arguments[0].scrollIntoView()", post)
        #post = bot.find_element(by=By.CLASS_NAME, value="css-y1m958")
        #ActionChains(bot).move_to_element(post).perform()
        
        #ActionChains(bot).click(post).perform()
        print("clicked")
        time.sleep(1.25)
        #post.click()
        # Wait for confirmation, then exit
        WebDriverWait(bot,120).until(EC.presence_of_element_located((By.CLASS_NAME,'tiktok-modal__modal-button is-highlight')))
        time.sleep(0.2)
        bot.close()
        return True
    except:
        bot.close()
        return False
    
upload_to_tiktok("test", "Schreibe deine Antwort in die Kommentare")