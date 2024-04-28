#DeepWeight

import time

#Step 1: Load Cell
import pickle
import os
import RPi.GPIO as GPIO
from hx711 import HX711

GPIO.setmode(GPIO.BCM)
hx = HX711(dout_pin=21, pd_sck_pin=20)
swap_file_name = 'swap_file.swp' #swp file saves the load cell calibration
if os.path.isfile(swap_file_name):
        with open(swap_file_name, 'rb') as swap_file:
            hx = pickle.load(swap_file)

#Loading model
import fastbook
from fastbook import *
learn_inf = load_learner(r"export0_4.pkl")

while True:
    fruit_weight = 0

    #Step 1.1: Detect weight change
    counter = 0
    prev = 0
    while True:
        if(counter > 3):
            print(hx.get_weight_mean(5), 'g')
            #If there's an abrupt change in weight, the item has been placed on the load cell
            if(abs(prev - hx.get_weight_mean(5))>50):
                fruit_weight = hx.get_weight_mean(5)/1000 #store weight
                print("Fruit is placed on load cell, weighing ", fruit_weight," kg!!!")
                print("\nWeight data collected!")
                break
            counter += 1
            if(counter>40):
                sys.exit() 
        else:
            print(hx.get_weight_mean(5), 'g')
            prev = hx.get_weight_mean(5)
            counter += 1
            
    #Step 2: Capture Image
    import cv2

    webcam = cv2.VideoCapture(0)
    webcam.set(3,1920)
    webcam.set(4,1080)
    check, frame = webcam.read()
    cv2.imwrite(filename=r'input.jpg', img=frame)
    print("\nImage captured!")
    webcam.release()

    #Step 3: Pass through Deep Learning Model
    prediction = learn_inf.predict(r"input.jpg")
    print("\nThese are", prediction[0], "!!!")
    print("\nPrediction made!")
    print(prediction)
    fruit_pred = prediction[0]

    #Step 4: Calculate price
    import pandas as pd

    fruit_price_list = pd.read_csv(r"fruit_prices.csv")
    fruit_price_list = pd.DataFrame(fruit_price_list)
    fruit_price = list(fruit_price_list.loc[fruit_price_list['fruit'] == fruit_pred, 'price'])[0]
    total_price = fruit_price*fruit_weight
    print("Rs. ", total_price)
    print("\nPrice calculated!")

    #Step 5: Generate Receipt
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab_qrcode import QRCodeImage
    from reportlab.graphics.barcode import code128, code93, code39

    text_qr = fruit_pred + " x " + str(round(fruit_weight, 2)) + " kg = Rs " + str(round(total_price, 2))

    top_text = fruit_pred + " " + str(round(fruit_weight, 2)) + " kg"
    bot_text = "Price: Rs " + str(round(total_price, 2))
    doc = SimpleDocTemplate('sticker.pdf')
    style = getSampleStyleSheet()
    qr_flowable = QRCodeImage(text_qr)
    barcode128 = code128.Code128(123456789, humanReadable=True, barWidth=1,
                             barHeight=1)
    barcode93_1 = code93.Standard93(fruit_pred)
    flowables = [
        Paragraph(top_text, style['BodyText']),
        qr_flowable,
        barcode93_1,
        Paragraph(bot_text, style['BodyText'])
    ]
    doc.build(flowables)
    print("\nReceipt generated!")

    #Step 6: Print Receipt
    import os

    os.system("lp sticker.pdf")
    time.sleep(3)
