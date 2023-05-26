import numpy as np
import torch
from model import Net
import random
import tkinter as tk
import tkinter.messagebox
import game, MCTS
MCTS_SEARCHES = 10
MCTS_BATCH_SIZE = 16


win = tk.Tk()                                 #新增一個視窗

win.title("quarto")                           #設定視窗的標題
win.geometry("1060x670")                       #設定視窗的大小
win.resizable(0, 0)                           #讓視窗的大小不能被改動
win.config(background="skyblue")              #視窗的背景色


table = np.zeros(64).reshape(4, 4, 4)  #棋盤，第一維為列，第二維為行，第三維為棋子種類，第三維的資料用1和2來表示不同的形態。
remaining_chess = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]  #剩餘的棋子
remaining_place = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]  #剩餘的位置
time = 1  #用來判斷現在是第幾回合
n = 0     #用來放勝利的回傳值
computer_good_place = []       #電腦判斷可以贏的地方
computer_remaining_chess = []  #電腦判斷不能選的棋
player_input = this_turn_place = this_turn_chess = this_turn_place_row = this_turn_place_column = 0
this_turn_chess_type = []

def win_row():  #判斷row方向的勝利
    for i in [0, 1, 2, 3]:
        for j in [0, 1, 2, 3]:
            list=[0, 0, 0, 0]  #list用來存放每次讀到的棋
            for k in [0, 1, 2, 3]:
                list[k]=table[j, k, i]
            if ((list == [1, 1, 1, 1]) or (list == [2, 2, 2, 2])):  
                return True       #如果讀到的棋符合勝利條件，就回傳1
                break
    return False

def win_column():  #判斷column方向的勝利
    for i in [0, 1, 2, 3]:
        for j in [0, 1, 2, 3]:
            list=[0, 0, 0, 0]
            for k in [0, 1, 2, 3]:
                list[k]=table[k, j, i]
            if ((list == [1, 1, 1, 1]) or (list == [2, 2, 2, 2])):
                return True
                break
    return False

def win_slope1(): #判斷右下斜方向的勝利
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        for j in [0, 1, 2, 3]:
            list[j]=table[j, j, i]
        if ((list == [1, 1, 1, 1]) or (list == [2, 2, 2, 2])):
            return True
            break
    return False

def win_slope2():  #判斷右上斜方向的勝利
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        for j in [0, 1, 2, 3]:
            list[j]=table[j, 3 - j, i]
        if ((list == [1, 1, 1, 1]) or (list == [2, 2, 2, 2])):
            return True
            break
    return False

def computer_remove(number, type1): #把不能選的棋子移除，number是型態，type1是第幾特徵。
    type1 += 1 
    if (number == 1):
        if (type1 == 1):
            for i in [1, 2, 3, 4, 5, 6, 7, 8]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 2):
            for i in [1, 2, 3, 4, 9, 10, 11, 12]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 3):
            for i in [1, 2, 5, 6, 9, 10, 13, 14]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 4):
            for i in [1, 3, 5, 7, 9, 11 ,13, 15]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i) 
    else:
        if (type1 == 1):
            for i in [9, 10, 11, 12, 13, 14, 15, 16]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 2):
            for i in [5, 6, 7, 8, 13, 14, 15, 16]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 3):
            for i in [3, 4, 7, 8, 11, 12, 15, 16]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)
        elif (type1 == 4):
            for i in [2, 4, 6, 8, 10, 12 ,14, 16]:
                if(i in computer_remaining_chess):
                    computer_remaining_chess.remove(i)



def computer_row_chess():  #判斷row有沒有要移除的棋子
    for i in [0, 1, 2, 3]:
        for j in [0, 1, 2, 3]:
            list=[0, 0, 0, 0]  
            for k in [0, 1, 2, 3]:
                list[k]=table[j, k, i]
            for l in [1, 2]:  # l是型態，看是1還是2。
                if (list == [0, l, l, l]):
                    computer_remove(l, i)
                if (list == [l, 0, l, l]):
                    computer_remove(l, i)
                if (list == [l, l, 0, l]):
                    computer_remove(l, i)
                if (list == [l, l, l, 0]):
                    computer_remove(l, i)

def computer_column_chess():  #判斷column有沒有要移除的棋子
    for i in [0, 1, 2, 3]:
        for j in [0, 1, 2, 3]:
            list=[0, 0, 0, 0]  
            for k in [0, 1, 2, 3]:
                list[k]=table[k, j, i]
            for l in [1, 2]:
                if (list == [0, l, l, l]):
                    computer_remove(l, i)
                if (list == [l, 0, l, l]):
                    computer_remove(l, i)
                if (list == [l, l, 0, l]):
                    computer_remove(l, i)
                if (list == [l, l, l, 0]):
                    computer_remove(l, i)


def computer_slope1_chess():  #判斷slope1有沒有要移除的棋子
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        for j in [0, 1, 2, 3]:
            list[j]=table[j, j, i]
            for l in [1, 2]:  
                if (list == [0, l, l, l]):
                    computer_remove(l, i)
                if (list == [l, 0, l, l]):
                    computer_remove(l, i)
                if (list == [l, l, 0, l]):
                    computer_remove(l, i)
                if (list == [l, l, l, 0]):
                    computer_remove(l, i)

def computer_slope2_chess():  #判斷slope2有沒有要移除的棋子
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        for j in [0, 1, 2, 3]:
            list[j]=table[j, 3 - j, i]
            for l in [1, 2]:
                if (list == [0, l, l, l]):
                    computer_remove(l, i)
                if (list == [l, 0, l, l]):
                    computer_remove(l, i)
                if (list == [l, l, 0, l]):
                    computer_remove(l, i)
                if (list == [l, l, l, 0]):
                    computer_remove(l, i)

def computer_choose_chess():  #電腦判斷選棋
    global computer_remaining_chess
    computer_remaining_chess = remaining_chess.copy()  #建立電腦用的剩餘棋子列表
    computer_row_chess()                        #判斷四個方向有沒有棋子不能選
    computer_column_chess()
    computer_slope1_chess()
    computer_slope2_chess()
    if(computer_remaining_chess==[]):           #如果沒有的話，隨機選一顆
        return random.choice(remaining_chess)
    else:                                       #如果有的話，從裡面選一顆
        return random.choice(computer_remaining_chess)


def computer_row_place(number2):         #電腦判斷row方向有沒有能贏的地方
    give_chess = chess(number2)    #把玩家給的數字轉成棋子的形式
    for i in [0, 1, 2, 3]:
        if (give_chess[i] == 1):   #如果這回合要判斷的特徵是1，就判斷1的
            for j in [0, 1, 2, 3]:
                list=[0, 0, 0, 0]  
                for k in [0, 1, 2, 3]:
                    list[k]=table[j, k, i]
                if (list == [0, 1, 1, 1]):
                    if(not ((j*4+1) in computer_good_place)): 
                        computer_good_place.append(j*4+1)
                if (list == [1, 0, 1, 1]):
                    if(not ((j*4+2) in computer_good_place)):
                        computer_good_place.append(j * 4 + 2)
                if (list == [1, 1, 0, 1]):
                    if(not ((j*4+3) in computer_good_place)):
                        computer_good_place.append(j * 4 + 3)
                if (list == [1, 1, 1, 0]):
                    if(not ((j*4+4) in computer_good_place)):
                        computer_good_place.append(j * 4 + 4)
        else :
            for j in [0, 1, 2, 3]:
                list=[0, 0, 0, 0]  
                for k in [0, 1, 2, 3]:
                    list[k]=table[j, k, i]
                if (list == [0, 2, 2, 2]):
                    if(not ((j * 4 + 1) in computer_good_place)):
                        computer_good_place.append(j * 4 + 1)
                if (list == [2, 0, 2, 2]):
                    if(not ((j * 4 + 2) in computer_good_place)):
                        computer_good_place.append(j * 4 + 2)
                if (list == [2, 2, 0, 2]):
                    if(not ((j * 4 + 3) in computer_good_place)):
                        computer_good_place.append(j * 4 + 3)
                if (list == [2, 2, 2, 0]):
                    if(not ((j * 4 + 4) in computer_good_place)):
                        computer_good_place.append(j * 4 + 4)      

def computer_column_place(number3):
    give_chess = chess(number3)
    for i in [0, 1, 2, 3]:
        if (give_chess[i] == 1):
            for j in [0, 1, 2, 3]:
                list=[0, 0, 0, 0]  
                for k in [0, 1, 2, 3]:
                    list[k]=table[k, j, i]
                if (list == [0, 1, 1, 1]):
                    if(not ((j + 1) in computer_good_place)):
                        computer_good_place.append(j + 1)
                if (list == [1, 0, 1, 1]):
                    if(not ((j + 5) in computer_good_place)):
                        computer_good_place.append(j + 5)
                if (list == [1, 1, 0, 1]):
                    if(not ((j + 9) in computer_good_place)):
                        computer_good_place.append(j + 9)
                if (list == [1, 1, 1, 0]):
                    if(not ((j + 13) in computer_good_place)):
                        computer_good_place.append(j + 13)
        else :
            for j in [0, 1, 2, 3]:
                list=[0, 0, 0, 0]  
                for k in [0, 1, 2, 3]:
                    list[k] = table[k, j, i]
                if (list == [0, 2, 2, 2]):
                    if(not ((j + 1) in computer_good_place)):
                        computer_good_place.append(j + 1)
                if (list == [2, 0, 2, 2]):
                    if(not ((j + 5) in computer_good_place)):
                        computer_good_place.append(j + 5)
                if (list == [2, 2, 0, 2]):
                    if(not ((j + 9) in computer_good_place)):
                        computer_good_place.append(j + 9)
                if (list == [2, 2, 2, 0]):
                    if(not ((j + 13) in computer_good_place)):
                        computer_good_place.append(j + 13)      

def computer_slope1_place(number4):
    give_chess = chess(number4)
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        if (give_chess[i] == 1): 
            for j in [0, 1, 2, 3]:
                list[j]=table[j, j, i]
                if (list == [0, 1, 1, 1]):
                    if(not (1 in computer_good_place)):
                        computer_good_place.append(1)
                if (list == [1, 0, 1, 1]):
                    if(not (6 in computer_good_place)):
                        computer_good_place.append(6)
                if (list == [1, 1, 0, 1]):
                    if(not (11 in computer_good_place)):
                        computer_good_place.append(11)
                if (list == [1, 1, 1, 0]):
                    if(not (16 in computer_good_place)):
                        computer_good_place.append(16)
        else:
            for j in [0, 1, 2, 3]:
                list[j]=table[j, j, i]
                if (list == [0, 2, 2, 2]):
                    if(not (1 in computer_good_place)):
                        computer_good_place.append(1)
                if (list == [2, 0, 2, 2]):
                    if(not (6 in computer_good_place)):
                        computer_good_place.append(6)
                if (list == [2, 2, 0, 2]):
                    if(not (11 in computer_good_place)):
                        computer_good_place.append(11)
                if (list == [2, 2, 2, 0]):
                    if(not (16 in computer_good_place)):
                        computer_good_place.append(16)         

def computer_slope2_place(number5):
    give_chess = chess(number5)
    for i in [0, 1, 2, 3]:
        list=[0, 0, 0, 0]
        if (give_chess[i] == 1): 
            for j in [0, 1, 2, 3]:
                list[j]=table[j, 3 - j, i]
                if (list == [0, 1, 1, 1]):
                    if(not (4 in computer_good_place)):
                        computer_good_place.append(4)
                if (list == [1, 0, 1, 1]):
                    if(not (7 in computer_good_place)):
                        computer_good_place.append(7)
                if (list == [1, 1, 0, 1]):
                    if(not (10 in computer_good_place)):
                        computer_good_place.append(10)
                if (list == [1, 1, 1, 0]):
                    if(not (13 in computer_good_place)):
                        computer_good_place.append(13)
        else:
            for j in [0, 1, 2, 3]:
                list[j]=table[j, 3 - j, i]
                if (list == [0, 2, 2, 2]):
                    if(not (4 in computer_good_place)):
                        computer_good_place.append(4)
                if (list == [2, 0, 2, 2]):
                    if(not (7 in computer_good_place)):
                        computer_good_place.append(7)
                if (list == [2, 2, 0, 2]):
                    if(not (10 in computer_good_place)):
                        computer_good_place.append(10)
                if (list == [2, 2, 2, 0]):
                    if(not (13 in computer_good_place)):
                        computer_good_place.append(13)         

def computer_choose_place(number1):  #電腦判斷勝利位置的函示
    global computer_good_place
    computer_good_place = []         #建立電腦判斷有沒有勝利地方的列表
    computer_row_place(number1)
    computer_column_place(number1)
    computer_slope1_place(number1)
    computer_slope2_place(number1)
    computer_can_choose_good_place = list(set(computer_good_place) & set(remaining_place))  #勝利地方和剩餘地方取聯集
    if (computer_can_choose_good_place == []):  #如果沒有的話就從剩餘的隨便選一個地方
        return random.choice(remaining_place)
    else:                                       #如果有的話就從裡面隨機選一個地方
        return random.choice(computer_can_choose_good_place)


def turn_choose():                                                  #用time判斷誰要選棋
    if (time%2==1):                                                #電腦選
        this_turn_computer_choose_chess = computer_choose_chess()  #跑電腦選棋的函式
        #棋放到選區
        return this_turn_computer_choose_chess
    else:                                                          #玩家選
        hint.config(text="請選擇棋子")
        return player_input

def chess(number):  #把選棋打的數字轉換成棋的形式
    chess = int(format(number, "b"))+1111  #把輸入的數字轉2進制，再加上基礎的1111
    list=[0, 0, 0, 0]
    for i in [3, 2, 1, 0]:     #用迴圈放進列表裡
        list[i] = int(chess%10)
        chess /= 10
    return list

def chooseplace(number):   #把下棋打的數字轉成棋盤的位置
    a = int((number - 1) / 4)  
    b = int((number - 1) % 4)
    return [a, b]

def renew_windows(number, place):
    x = int((place - 1) % 4) 
    y = int((place - 1) / 4)
    print(x, y)
    x = 300 + (120 * x)
    y = 30 + (120 * y)
    print(x,y)
    chesses[number - 1].place(x = x, y = y)

def put_computer_chess(number):
    chesses[number - 1].place(x = 300, y = 540)

def ok():
    global player_input, this_turn_place, this_turn_chess, this_turn_place_row, this_turn_place_column, time, n
    global this_turn_chess_type, remaining_place, remaining_chess
    global table
    player_input = int(choose.get())
    if(time % 2 == 1):        #玩家選位置
        try:
            this_turn_place = player_input
            remaining_place.remove(this_turn_place)
            
            this_turn_chess_type = chess(this_turn_chess - 1)
            (this_turn_place_row, this_turn_place_column) =  chooseplace(this_turn_place)
            table[this_turn_place_row, this_turn_place_column] = this_turn_chess_type
            remaining_chess.remove(this_turn_chess)
            
            renew_windows(this_turn_chess, this_turn_place)
            
            if win_row() or win_column() or win_slope1() or win_slope2():
                tkinter.messagebox.showinfo(message = "你贏了")
            
            hint.config(text = "請選擇棋子")
            time += 1
        except:
            hint.config(text = "請重新選擇")
    else:                 #玩家選棋子
        this_turn_chess = player_input
        remaining_chess.remove(this_turn_chess)
        
        this_turn_place = computer_choose_place(this_turn_chess - 1) 
        remaining_place.remove(this_turn_place)
        
        this_turn_chess_type = chess(this_turn_chess - 1)
        (this_turn_place_row, this_turn_place_column) =  chooseplace(this_turn_place)
        table[this_turn_place_row, this_turn_place_column] = this_turn_chess_type
        
        renew_windows(this_turn_chess, this_turn_place)
        
        if win_row() or win_column() or win_slope1() or win_slope2():
            tkinter.messagebox.showinfo(message = "你輸了")
        if (time == 16):
            tkinter.messagebox.showinfo(message = "平手")
        
        this_turn_chess = computer_choose_chess()
        put_computer_chess(this_turn_chess)
        # renew_windows(this_turn_chess, this_turn_place)
        
        hint.config(text = "請選擇位置")
        time += 1

img_table = tk.PhotoImage(file = "pic/table.png")   #新增一個圖片
img_wait = tk.PhotoImage(file = "pic/wait.png")
img_give = tk.PhotoImage(file = "pic/give.png")

tktable = tk.Label()                            #新增一個格子   
tktable.config(image = img_table, bg = "skyblue") #設定這個格子的圖片
tktable.place(x = "280", y = "10")                  #把他放在絕對座標 (10, 10)

wait1 = tk.Label()                            
wait1.config(image = img_wait, bg = "skyblue") 
wait1.place(x = "10", y = "10")                   

wait2 = tk.Label()                               
wait2.config(image = img_wait, bg = "skyblue") 
wait2.place(x = "790", y = "10")                 

give = tk.Label()                            
give.config(image = img_give, bg = "skyblue") 
give.place(x = "280", y = "520")           

imgs = []
chesses = []

for i in range(16):
    index = int(format(i, "b")) + 1111
    imgs.append(tk.PhotoImage(file = "pic/" + str(index) + ".png"))

for i in range(16):
    tmp = tk.Label()
    tmp.config(image = imgs[i], bg = "white")
    x = [30, 150, 810, 930]
    y = (i % 4) * 120 + 30
    tmp.place(x = str(x[int(i / 4)]), y = str(y))
    chesses.append(tmp)


choose = tk.Entry()
choose.config(font="標楷體 15")
choose.place(x = "20", y = "520")

enter = tk.Button()
enter.config(text="OK", command= ok)
enter.place(x = "20", y = "550")

hint = tk.Label()
hint.config(text="請選擇位置", bg = "skyblue", font="標楷體 70")
hint.place(x = "510", y = "520")


this_turn_chess = random.choice(remaining_chess)
put_computer_chess(this_turn_chess)

win.mainloop()

