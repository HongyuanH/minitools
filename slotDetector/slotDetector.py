from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import chromedriver_autoinstaller
from time import sleep
import logging
import sys
import signal
import smtplib
import yaml
from email.message import EmailMessage

class Logger(object):

    __instance = None
    
    @classmethod
    def error(cls, msg):
        cls.__instance.rootLogger.error(msg)

    @classmethod
    def warn(cls, msg):
        cls.__instance.rootLogger.warning(msg)

    @classmethod
    def info(cls, msg):
        cls.__instance.rootLogger.info(msg)

    @classmethod
    def debug(cls, msg):
        cls.__instance.rootLogger.debug(msg)

    @classmethod
    def init(cls, log_path, level):
        if not cls.__instance:
            with open(log_path, 'w') as fid:
                pass
            cls.__instance = Logger(log_path, level)

    def __init__(self, log_path, level):
        self.rootLogger = logging.getLogger("root")
        if level == 'debug':
            self.rootLogger.setLevel(logging.DEBUG)
        elif level == 'info':
            self.rootLogger.setLevel(logging.INFO)
        elif level == 'warn':
            self.rootLogger.setLevel(logging.WARNING)
        elif level == 'error':
            self.rootLogger.setLevel(logging.ERROR)
        else:
            raise Exception(f'Unexpected logging level: {level}')
        logFormatter = logging.Formatter("[%(asctime)s][%(levelname)-4.4s] %(message)s")
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(logFormatter)
        self.rootLogger.addHandler(consoleHandler)
        fileHandler = logging.FileHandler(log_path)
        fileHandler.setFormatter(logFormatter)
        self.rootLogger.addHandler(fileHandler)

class SlotDetector(object):

    __stop = False

    @classmethod
    def stop(cls):
        cls.__stop = True

    def __init__(self, *args, **kwargs):
        chromedriver_autoinstaller.install() 
        self.sender = gmailSender(*args, **kwargs)
        if kwargs['first_time']:
            self.firstRun()
        else:
            self.run()
        
    def openChrome(self):
        chrome_options = Options()
        chrome_options.add_argument("user-data-dir=userdata") 
        self.driver = webdriver.Chrome(chrome_options=chrome_options, 
            executable_path='chromedriver')
        Logger.info('Opened Chrome.')
        
    def openPage(self, page):
        self.driver.get(page)
        Logger.info(f'Opened page {page}.')
        
    def findSlot(self):
        found_none = 0
        found_X = 0
        found_Sold = 0
        found_available = 0
        buttons = self.driver.find_elements_by_class_name('slot-button__slot-area')
        for button in buttons:
            txt = button.text
            if not txt:
                found_none += 1
            elif 'X' in txt:
                found_X += 1
            elif 'Sold Out' in txt:
                found_Sold += 1
            else:
                found_available += 1
        Logger.info(f'Result: Hidden: {found_none}, X: {found_X}, Sold Out: {found_Sold}, Available: {found_available}')
        if found_available:
            body = "Click here to go to ASDA: https://groceries.asda.com/checkout/book-slot?tab=deliver&origin=/"
            self.sender.sendGmail(f"ASDA: {found_available} slot found!", body)
        
    def closeDialog(self):
        try:
            button = self.driver.find_element_by_class_name('asda-dialog__close-icon')
            if button:
                button.click()
                Logger.info('Closed login dialog.')
        except NoSuchElementException as e:
            pass
            
    def navigateSlotTable(self):
        for i in range(4):
            try:
                button = self.driver.find_element_by_xpath("//button[@data-auto-id='btnLater']")
                if button:
                    button.click()
                    Logger.info('Clicked on "Later>"')
                    sleep(5)
            except ElementClickInterceptedException as e:
                Logger.warn('ElementClickInterceptedException')
                pass

    def run(self):
        self.openChrome()
        while not self.__stop:
            self.openPage('https://groceries.asda.com/checkout/book-slot?tab=deliver&origin=/')
            sleep(10)
            self.closeDialog()
            self.findSlot()
            self.navigateSlotTable()
            self.findSlot()
            for i in range(60):
                sleep(1)
                if self.__stop:
                    break

    def firstRun(self):
        self.openChrome()
        self.openPage('https://www.asda.com/login')

class gmailSender(object):
    
    def __init__(self, *args, **kwargs):
        self.email = kwargs['email']
        self.passwd = kwargs['passwd']
        self.sent_from = self.email
        self.send_to = kwargs['send_to']
        
    def sendGmail(self, subject, body):
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(self.email, self.passwd)
        ## Does not work in Python3
        # email_text = (f"From: {self.sent_from}\n"
        #     f"To: {self.send_to}\n"
        #     f"Subject: {subject}\n\n\n{body}")
        # server.sendmail(from_addr=self.sent_from, 
        #     to_addrs=', '.join(self.send_to), 
        #     msg=email_text)
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sent_from
        msg['To'] = ', '.join(self.send_to)
        msg.set_content(body)
        server.send_message(msg)
        server.close()
        Logger.info('Gmail sent.')

def signalHandler(s, f):
    if s == signal.SIGINT:
        Logger.info('CTRL+C detected, terminating...')
        SlotDetector.stop()
                    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, help="cfg file", default="cfg.yaml")
    args = parser.parse_args()
    Logger.init('slotDetector.log', 'info')
    signal.signal(signal.SIGINT, signalHandler)
    with open(args.cfg, 'r') as fid:
        cfg = yaml.safe_load(fid)
    sd = SlotDetector(**cfg)