import pyetherbalance
import time
import os
import sys
import json

#Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import Select

#PyQt5
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

#Kill Old Firefox Instances
try:
    os.system('taskkill /f /im firefox.exe')
    os.system('taskkill /f /im geckodriver.exe')
    os.system('cls')
except:
    pass

#Enable Headless
options = Options()
options.headless = True

#Open Browser for Mturk
driver = webdriver.Firefox(options=options)

#Binance Smart Chain URL
Binance_Chain = 'https://bsc-dataseed1.binance.org:443'

#Wallet Address
Binance_Address = '0x0000000000000000000000000000000000000001'
Original_Balance = 295543915391500.7

#Create BNB Balance Object
BNB_Balance = pyetherbalance.PyEtherBalance(Binance_Chain)

#Initialize SafeMoon Token
Token = "SafeMoon"
Details = {'symbol': 'SafeMoon', 'address': '0x8076c74c5e3f5852037f31ff0093eeb8c8add8d3', 'decimals': 9, 'name': 'SafeMoon'}
BEP20Token = BNB_Balance.add_token(Token, Details)


reset = True

class Emitter(QObject):
    bal = pyqtSignal(str) #PLACEHOLDER
    avg = pyqtSignal(str)
    refl = pyqtSignal(str)
    t_refl = pyqtSignal(str)
    price = pyqtSignal(str)


class safemoonrun(QRunnable):
    
    def __init__(self):
        super(safemoonrun, self).__init__()
        self.emitter = Emitter()    

        #Variables
        self.Current_Balance = 0.0
        self.Total_Reflections = 0.0
        self.Num_Reflections = 0
        self.Avg_Gain_Per_Reflection = 0.0
        self.Running_Gain = 0.0
        self.x = 0
        self.Gain = 0.0

    @pyqtSlot()
    def run(self):
        while True:

            #Variables
            global reset
            if reset:
                self.Current_Balance = 0.0
                self.Total_Reflections = 0.0
                self.Num_Reflections = 0
                self.Avg_Gain_Per_Reflection = 0.0
                self.Running_Gain = 0.0
                self.x = 0
                self.Gain = 0.0
                reset = False

			#Get SafeMoon Token info for Wallet
            SafeMoon = BNB_Balance.get_token_balance('SafeMoon', Binance_Address)

			#Only update when SafeMoon balance changes
            if float(SafeMoon['balance']) > self.Current_Balance:

				#Only Calculate Gain and Total Reflections after first loop
                if self.Current_Balance != 0.0:

					#Update self.Num_Reflections
                    self.Num_Reflections += 1

					#Only update SafeMoon price once every x loops
                    if self.x == 0:
                        driver.get('https://www.coingecko.com/en/coins/safemoon')
                        SafeMoon_Price = driver.find_element_by_css_selector('div.text-3xl > span:nth-child(1)').text.replace('$','')
                        self.emitter.price.emit(SafeMoon_Price)
                        self.x += 1
                    if self.x == 20:
                        self.x = 0

					#Print SafeMoon Balance
                    #print(str(round(SafeMoon['balance'],9)) + ' SafeMoon' + ' ($' + str(round(float(SafeMoon['balance']) * float(SafeMoon_Price),2)) + ')')

					#Calculate Gain and Total from Reflections
                    self.Gain = SafeMoon['balance'] - self.Current_Balance
                    self.Running_Gain += self.Gain
                    self.Total_Reflections = float(SafeMoon['balance']) - float(Original_Balance)
                    self.Avg_Gain_Per_Reflection = self.Running_Gain / float(self.Num_Reflections)
                    #print('+' + str(round(self.Avg_Gain_Per_Reflection,3)) + ' SafeMoon/Reflection' + ' ($' + str(round(float(self.Avg_Gain_Per_Reflection) * float(SafeMoon_Price),2)) + ')')
                    #print('+' + str(round(self.Gain,9)) + ' SafeMoon' + ' ($' + str(round(float(self.Gain) * float(SafeMoon_Price),2)) + ')')
                    #print('+' + str(round(self.Total_Reflections,9)) + ' SafeMoon' + ' ($' + str(round(float(self.Total_Reflections) * float(SafeMoon_Price),2)) + ')')
                    #print('')

					#Calucate SafeMoon Value ($USD)
                    SafeMoon_Value = float(SafeMoon['balance']) * float(SafeMoon_Price)
				
				#Update Current Balance	
                self.Current_Balance = float(SafeMoon['balance'])
                self.emitter.bal.emit(str(SafeMoon['balance']))
                self.emitter.avg.emit(str(self.Avg_Gain_Per_Reflection))
                self.emitter.refl.emit(str(self.Gain))
                self.emitter.t_refl.emit(str(self.Total_Reflections))

class AddWalletUI(QMainWindow):
    def __init__(self):
        super(AddWalletUI, self).__init__() # Call the inherited classes __init__ method

        #Load UI File
        uic.loadUi('AddWallet.ui', self) # Load the .ui file
        self.show()

class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        #Initialize Threadpool
        self.threadpool = QThreadPool()

        #Load UI File
        uic.loadUi('SafeMoon.ui', self) # Load the .ui file

        #Run Main Loop
        runner = safemoonrun()
        self.threadpool.start(runner) 

        #Update GUI Labels 
        runner.emitter.price.connect(self.price)
        runner.emitter.bal.connect(self.texts)
        runner.emitter.avg.connect(self.texts1)
        runner.emitter.refl.connect(self.texts2)
        runner.emitter.t_refl.connect(self.texts3)

        #Buttons
        self.pushButton.clicked.connect(self.add_wallet)
        self.pushButton_2.clicked.connect(self.refresh)

        self.pop_wallets()
        self.comboBox.activated.connect(self.select_wallet)

        #Show the GUI
        self.show() 

    def add_wallet(self):
        self.window2 = AddWalletUI()
        self.window2.pushButton_2.clicked.connect(lambda: self.save_new_wallet(self.window2))
        #Save Data to file

    def save_new_wallet(self, window):
        file = open('wallets.json', 'r')
        data = json.load(file)
        file.close()
        new_wallet =  {
                window.textEdit.toPlainText():
                [
                    {
                        "address": window.textEdit_2.toPlainText(),
                        "starting": window.textEdit_3.toPlainText()      
                    }
                ]
            }
        data.update(new_wallet)
        file2 = open("wallets.json", "w")
        json.dump(data, file2)
        file2.close()
        window.close()
        self.pop_wallets()


    def select_wallet(self, index):
        file = open('wallets.json', 'r')
        data = json.load(file)
        file.close()
        global Binance_Address
        Binance_Address = data[self.comboBox.itemText(index)][0]["address"]
        global Original_Balance
        Original_Balance = data[self.comboBox.itemText(index)][0]["starting"]
        self.refresh()

    def pop_wallets(self):
        file = open('wallets.json', 'r')
        data = json.load(file)
        file.close()
        self.comboBox.clear()
        for x in data:
            self.comboBox.addItem(x)

    def refresh(self):
        global reset
        reset = True

    def price(self, data):

        self.price = float(data)

    def texts(self, data):
        if isinstance(self.price, float):
            value = round(float(data) * float(self.price),2)
            self.label_5.setText(format(float(data),",") + ' SafeMoon' + '  ($' + str(format(float(value),",")) + ')')
        else:
            self.label_5.setText(data + ' SafeMoon')

    def texts1(self, data):
        if isinstance(self.price, float):
            value = round(float(data) * float(self.price),2)
            value2 = round(float(data),3)
            self.label_6.setText(str(format(float(value2),",")) + ' SafeMoon/Reflection' + '  ($' + str(format(float(value),",")) + ')')
        else:
            self.label_5.setText(data + ' SafeMoon')

    def texts2(self, data):
        if isinstance(self.price, float):
            value = round(float(data) * float(self.price),2)
            self.label_7.setText(format(float(data),",") + ' SafeMoon' + '  ($' + str(format(float(value),",")) + ')')
        else:
            self.label_5.setText(data + ' SafeMoon')

    def texts3(self, data):
        if isinstance(self.price, float):
            value = round(float(data) * float(self.price),2)
            self.label_8.setText(format(float(data),",") + ' SafeMoon' + '  ($' + str(format(float(value),",")) + ')')
        else:
            self.label_5.setText(data + ' SafeMoon')

    


app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application

