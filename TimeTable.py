import pygame
import win32gui
import win32con
import win32api
import sys
import os
import json
from datetime import datetime,date

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

pygame.init()

#time：星期，周数，节数（开始，长度）
with open('class.json','r',encoding='utf-8') as f:
    class_box = json.load(f)

with open('setting.json','r',encoding='utf-8') as e:
    setting = json.load(e)

win_width = setting['WindowWidth']
win_height = setting['WindowHeight']
class_number = setting['ClassNumber']
table_width = int(win_width / 8)
table_height = int(( win_height - 20 ) / ( class_number + 1 ))
fps = setting['Fps']

test_color = tuple(setting['TestColor'])
back_color = tuple(setting['BackColor'])
class_test_color = tuple(setting['ClassTestColor'])

font_simyout = pygame.font.Font(resource_path('font/SIMYOU.TTF'), 16)
font_time = pygame.font.Font(resource_path('font/SIMYOU.TTF'), 12)

screen = pygame.display.set_mode((win_width, win_height),pygame.NOFRAME)
pygame.display.set_caption('课表')

hwnd = pygame.display.get_wm_info()['window']

ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)

win32gui.SetLayeredWindowAttributes(hwnd,0,setting['Transparency'],win32con.LWA_ALPHA)

test_title = font_simyout.render('课程表', True,test_color)
test_term = font_simyout.render(setting['Term'], True, test_color)

class_time = setting['ClassTime']

is_drag = False
drag_offset = (0,0)
clock = pygame.time.Clock()
running = True
dragging = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if event.pos[1] < 20:
                    mx, my = my_screen = win32api.GetCursorPos()
                    win_rect = win32gui.GetWindowRect(hwnd)
                    win_x,win_y = win_rect[0],win_rect[1]
                    drag_offset = (mx - win_x, my - win_y)
                    dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        if event.type == pygame.MOUSEMOTION and dragging:
            mx, my = win32api.GetCursorPos()
            new_x = mx - drag_offset[0]
            new_y = my - drag_offset[1]
            win32gui.SetWindowPos(hwnd,win32con.HWND_TOP, new_x,new_y, 0, 0,win32con.SWP_NOSIZE |
                                  win32con.SWP_NOZORDER )
    screen.fill(back_color)
    screen.blit(test_title, (10,2))
    month = datetime.now().month
    day = datetime.now().day
    weekday = datetime.now().isoweekday()
    day_term_start = date(*tuple(setting['TermStartDate']))
    day_term_end = date(*tuple(setting['TermEndDate']))
    day_now = date.today()
    delta = day_now - day_term_start
    left = day_term_end - day_now
    day_delta = delta.days
    day_left = left.days
    week_number = (day_delta // 7) + 1
    test_week_number = font_simyout.render(f'第{week_number}周',True,test_color)
    test_day_left = font_simyout.render(f'本学期剩余{day_left}天',True,test_color)
    screen.blit(test_week_number,(220,2))
    screen.blit(test_day_left,(300,2))

    pygame.draw.circle(screen,(255,255,255),(table_width/2+weekday*table_width,20+table_height/2),(min(table_width,table_height)-5)/2)

    for i in range(20,win_height,table_height):
        pygame.draw.line(screen,test_color,(0,i),(win_width,i),1)
    for j in range(0,win_width,table_width):
        pygame.draw.line(screen,test_color,(j,20),(j,win_height),1)
    for k in range(1,setting['ClassNumber']+1):
        test_class = font_simyout.render(f'第{k}节',True,test_color)
        screen.blit(test_class,(20,(22+table_height*k)))
    for a in range(0,setting['ClassNumber']):
        test_class_time = font_time.render(f'{class_time[a][0]}~{class_time[a][1]}',True,test_color)
        screen.blit(test_class_time,(table_width/8,(40+table_height*(a+1))))
    for b in range(1,8):
        if b == 1:
            test_week = font_simyout.render('周一',True,test_color)
        elif b == 2:
            test_week = font_simyout.render('周二',True,test_color)
        elif b == 3:
            test_week = font_simyout.render('周三',True,test_color)
        elif b == 4:
            test_week = font_simyout.render('周四',True,test_color)
        elif b == 5:
            test_week = font_simyout.render('周五',True,test_color)
        elif b == 6:
            test_week = font_simyout.render('周六',True,test_color)
        elif b == 7:
            test_week = font_simyout.render('周日',True,test_color)
        screen.blit(test_week,((table_width-55+table_width*b),20+table_height/10))

    test_month = font_simyout.render(f'{month}月',True,test_color)
    screen.blit(test_month,(table_width-53,20+table_height/3.5))
    screen.blit(test_term,(100,2))

    for d in range(weekday,weekday+8):
        if d >= 8:
            d -= 7
        today_date = day+(d-weekday)
        if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
            if today_date >31:
                test_day = font_time.render(f'{today_date-31}日',True,test_color)
            elif today_date <1:
                if ((month-1) == 0 or (month-1) == 1 or (month-1) == 3 or (month-1) == 5 or (month-1) == 7 or
                        (month-1) == 8 or (month-1) == 10):
                    test_day = font_time.render(f'{today_date + 31}日', True, test_color)
                elif (month-1) == 4 or (month-1) == 6 or (month-1) == 9 or (month-1) == 11:
                    test_day = font_time.render(f'{today_date + 30}日', True, test_color)
                else:
                    test_day = font_time.render(f'{today_date + 28}日', True, test_color)
            else:
                test_day = font_time.render(f'{today_date}日', True, test_color)
        if month == 4 or month == 6 or month == 9 or month == 11:
            if today_date > 30:
                test_day = font_time.render(f'{today_date - 30}日', True, test_color)
            elif today_date < 1:
                if ((month - 1) == 0 or (month - 1) == 1 or (month - 1) == 3 or (month - 1) == 5 or (month - 1) == 7 or
                        (month - 1) == 8 or (month - 1) == 10):
                    test_day = font_time.render(f'{today_date + 31}日', True, test_color)
                elif (month - 1) == 4 or (month - 1) == 6 or (month - 1) == 9 or (month - 1) == 11:
                    test_day = font_time.render(f'{today_date + 30}日', True, test_color)
                else:
                    test_day = font_time.render(f'{today_date + 28}日', True, test_color)
            else:
                test_day = font_time.render(f'{today_date}日', True, test_color)
        screen.blit(test_day,((30+table_width*d),20+table_height/1.75))

    for Class in class_box:
        class_number_box = len(Class['time'])
        for dex in range(0,class_number_box):
            if week_number in Class['time'][dex][1]:
                class_start = Class['time'][dex][2][0]
                class_len = Class['time'][dex][2][1]
                class_week = Class['time'][dex][0]
                pygame.draw.rect(screen,tuple(Class['color']),(table_width*class_week,20+table_height*class_start,table_width,table_height*class_len),0,15)
                test_class_name = font_simyout.render(f"{Class['name']}",True,class_test_color)
                test_class_loc = font_simyout.render(f"{Class['loc'][dex]}",True,class_test_color)
                screen.blit(test_class_name,(table_width*class_week+5,20+table_height*class_start+5))
                screen.blit(test_class_loc,(table_width*class_week+5,20+table_height*class_start+35))

    now = datetime.now()
    minute_now = now.hour * 60 + now.minute
    class_time_list = []
    for t in setting['ClassTime']:
        start_hour,start_minute = map(int,t[0].split(':'))
        start = start_hour*60 + start_minute
        end_hour,end_minute = map(int,t[1].split(':'))
        end = end_hour*60 + end_minute
        class_time_list.append([start,end])
    for k in range(class_number):
        start_k,end_k = class_time_list[k]
        if start_k <= minute_now < end_k:
            line_y = 20 + table_height + k * table_height + table_height * (minute_now - start_k)/45
            pygame.draw.line(screen,(0,0,0),(table_width*weekday,line_y),(table_width*(weekday+1),line_y),1)
            break
        elif k > 0 and class_time_list[k-1][1] <= minute_now < start_k:
            line_y = 20 + table_height + k * table_height
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y),1)
            break
        elif k == 0 and minute_now < start_k:
            line_y = 20 + table_height
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y),1)
            break
        elif k == class_number-1 and minute_now >= end_k:
            line_y = win_height - 1
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y),1)
            break
    pygame.display.update()
    clock.tick(fps)

pygame.quit()
sys.exit()