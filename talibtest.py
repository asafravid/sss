'''Auto coded candlestick recogntion with talib combined with technical strategies for educational purposes.'''

import talib
import numpy
import csv
    
symbols_file=open("Auto generated Dataset\Tickers.csv",'r')
tickers=csv.reader(symbols_file)

def can_strat(openn,high,low,close):
    res_strike=talib.CDL3LINESTRIKE(openn,high,low,close)
    res_ab_baby=talib.CDLABANDONEDBABY(openn,high,low,close)
    res_doji=talib.CDLDOJI(openn,high,low,close)
    res_doji_star=talib.CDLDOJISTAR(openn,high,low,close)
    res_dragonfly=talib.CDLDRAGONFLYDOJI(openn,high,low,close)
    res_englufing=talib.CDLENGULFING(openn,high,low,close)
    res_evening_doji=talib.CDLEVENINGDOJISTAR(openn,high,low,close)
    res_evening=talib.CDLEVENINGSTAR(openn,high,low,close)
    res_gravestone=talib.CDLGRAVESTONEDOJI(openn,high,low,close)
    res_hammer=talib.CDLHAMMER(openn,high,low,close)
    #res_hanging=talib.CDLHANGINGMAN(openn,high,low,close)
    res_harami=talib.CDLHARAMI(openn,high,low,close)
    res_hamari_cross=talib.CDLHARAMICROSS(openn,high,low,close)
    res_inverted_hammer=talib.CDLINVERTEDHAMMER(openn,high,low,close)
    res_longlegged=talib.CDLLONGLEGGEDDOJI(openn,high,low,close)
    res_marubozu=talib.CDLMARUBOZU(openn,high,low,close)
    res_morning_doji=talib.CDLMORNINGDOJISTAR(openn,high,low,close)
    #res_morning=talib.CDLLONGLEGGEDDOJI(openn,high,low,close)
    res_shooting=talib.CDLSHOOTINGSTAR(openn,high,low,close)
    res_spinning=talib.CDLSPINNINGTOP(openn,high,low,close)
    res_takuri=talib.CDLTAKURI(openn,high,low,close)
    res_tristar=talib.CDLTRISTAR(openn,high,low,close)

    if(res_strike[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": 3 Line Strike")
            print(res_strike)

    if(res_ab_baby[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Abandoned Baby")
            print(res_ab_baby)

    if(res_doji[-1]!=0 or res_longlegged[-1]!=0 or res_spinning[-1]!=0 or res_doji_star[-1]!=0 or res_dragonfly[-1]!=0 or res_takuri[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Doji")
            print(res_doji)

    if(res_englufing[-1]!=0):
        if(res_englufing[-1]<0):
                print("\n")
                print(ticker)
                print(hold[0][-1]+": Bearish Engulfing")
                print(res_englufing)
        else:
                print("\n")
                print(ticker)
                print(hold[0][-1]+": Bullish Engulfing")
                print(res_englufing)
                

    if(res_evening_doji[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Evening Doji")
            print(res_evening_doji)

    if(res_evening[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Evening Star")
            print(res_evening)

    if(res_gravestone[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Gravestone doji")
            print(res_gravestone)

    if(res_hammer[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Hammer")
            print(res_hammer)

    if(res_hamari_cross[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Harami Cross")
            print(res_hamari_cross)

    '''if(res_hanging[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Hanging Man")
            print(res_hanging)'''

    if(res_harami[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Harami")
            print(res_harami)

    if(res_inverted_hammer[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Inverted Hammer")
            print(res_inverted_hammer)

    if(res_marubozu[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Marubozu")
            print(res_marubozu)

    if(res_morning_doji[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Morning Doji")
            print(res_morning_doji)

    '''if(res_morning[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Morning Star")
            print(res_morning)'''

    if(res_shooting[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Shooting Star")
            print(res_shooting)

    if(res_tristar[-1]!=0):
            print("\n")
            print(ticker)
            print(hold[0][-1]+": Tri-Star")
            print(res_tristar)

def rsibull(index):
            rsi_val=talib.RSI(close,timeperiod=14)
            if(rsi_val[index]>44 and rsi_val[index]<49.9):
                return True
            return False

def rsibear(index):
        rsi_val=talib.RSI(close,timeperiod=14)
        if(rsi_val[index]>75):
                return True
        return False

def mfibear(index):
        mfi_val=talib.MFI(high,low,close,volume,timeperiod=14)
        if(mfi_val[index]>85):
                return True
        return False

def mfibull(index):
        mfi_val=talib.MFI(high,low,close,volume,timeperiod=14)
        if(mfi_val[index]<25):
                return True
        return False

def marsibull():
    ma5=talib.EMA(close,timeperiod=5)
    ma22=talib.EMA(close,timeperiod=22)
    ma34=talib.EMA(close,timeperiod=34)
    ma200=talib.EMA(close,timeperiod=200)

    if(close[-1]>ma5[-1] and close[-1]>ma22[-1] and ma5[-1]>ma22[-1]):
            if(rsibull(-1)):
                if(close[-2]<ma5[-2] and close[-2]<ma22[-2] and close[-3]<ma5[-3] and close[-3]<ma22[-3] and close[-4]<ma5[-4] and 
                   close[-4]<ma22[-4] and close[-5]<ma5[-5] and close[-5]<ma22[-5]):
                    print(ticker, " Bull Criteria met")

def marsibear():
    ma5=talib.EMA(close,timeperiod=5)
    ma22=talib.EMA(close,timeperiod=22)
    ma34=talib.EMA(close,timeperiod=34)
    ma200=talib.EMA(close,timeperiod=200)
    
    if(close[-1]<ma5[-1] and close[-1]<ma22[-1] and ma5[-1]<ma22[-1]):
            if(rsibear(-1)):
                if(close[-2]>ma5[-2] and close[-2]>ma22[-2] and close[-3]>ma5[-3] and close[-3]>ma22[-3] and close[-4]>ma5[-4] and 
                   close[-4]>ma22[-4] and close[-5]>ma5[-5] and close[-5]>ma22[-5]):
                    print(ticker, " Bear Criteria met")

a = 0

for company in tickers:
        ticker=company[0]
        first = True
        try:
                with open("Auto generated Dataset\\{}.csv".format(ticker)) as csv_file:
                                csv_object=csv.reader(csv_file)
                                hold=list()
                                for line in csv_object:
                                        if first:
                                                first = False
                                                continue
                                        hold.append(line[0:6])
                                        
                                        hold=hold[-10:]

                                        hold=numpy.column_stack(hold)
                                        
                                        openn=hold[1].astype(float)
                                        high=hold[2].astype(float)
                                        low=hold[3].astype(float)
                                        close=hold[4].astype(float)
                                        volume=hold[5].astype(float)  
                                        can_strat(openn,high,low,close)
        
        except Exception as e:
                a += 1
                print(e)
                continue



        




        
        


