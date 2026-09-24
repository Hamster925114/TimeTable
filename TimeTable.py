import pygame
import win32gui
import win32con
import win32api
import sys
import os
import json
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


pygame.init()

# time：星期，周数，节数（开始，长度）
with open('class.json', 'r', encoding='utf-8') as f:
    class_box = json.load(f)

with open('setting.json', 'r', encoding='utf-8') as e:
    setting = json.load(e)

# ---- 全局变量 ----
win_width = setting['WindowWidth']
win_height = setting['WindowHeight']
class_number = setting['ClassNumber']
fps = setting['Fps']

test_color = tuple(setting['TestColor'])
back_color = tuple(setting['BackColor'])
class_test_color = tuple(setting['ClassTestColor'])

font_simyout = pygame.font.Font(resource_path('font/SIMYOU.TTF'), 16)
font_time = pygame.font.Font(resource_path('font/SIMYOU.TTF'), 12)
font_tip = pygame.font.Font(resource_path('font/SIMYOU.TTF'), 12)

screen = pygame.display.set_mode((win_width, win_height), pygame.NOFRAME)
pygame.display.set_caption('课表')

hwnd = pygame.display.get_wm_info()['window']

WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


def apply_window_style():
    """应用无边框 + 透明(分层)窗口样式"""
    global hwnd
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, 0, setting['Transparency'], win32con.LWA_ALPHA)


apply_window_style()

table_width = int(win_width / 8)
table_height = int((win_height - 20) / (class_number + 1))


# ---- 周次 / 星期 辅助 ----
def parse_weeks(s):
    """把 "1-16" / "1,3,5-8" 解析成周次列表"""
    s = s.replace('，', ',').replace('－', '-').replace('—', '-').replace('~', '-').replace(' ', '')
    result = []
    for part in s.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            a, b = int(a), int(b)
            if a > b:
                a, b = b, a
            result += list(range(a, b + 1))
        else:
            result.append(int(part))
    return sorted(set(result))


def format_weeks(ws):
    """把周次列表压缩成 "1-16" / "1,3,5-8" 形式"""
    ws = sorted(set(ws))
    if not ws:
        return ''
    out = []
    start = prev = ws[0]
    for w in ws[1:]:
        if w == prev + 1:
            prev = w
        else:
            out.append(f'{start}-{prev}' if start != prev else f'{start}')
            start = prev = w
    out.append(f'{start}-{prev}' if start != prev else f'{start}')
    return ','.join(out)


def get_loc(Class, dex):
    """安全取地点：time 与 loc 长度不一致时返回默认值，避免越界崩溃"""
    locs = Class.get('loc', [])
    return locs[dex] if dex < len(locs) else '未定'


def compute_actual_week():
    """根据开学日期计算当前是第几周"""
    try:
        start = date(*tuple(setting['TermStartDate']))
        delta = date.today() - start
        return max(1, delta.days // 7 + 1)
    except Exception:
        return 1


def save_class():
    with open('class.json', 'w', encoding='utf-8') as f:
        json.dump(class_box, f, ensure_ascii=False, indent=1)


def save_setting():
    with open('setting.json', 'w', encoding='utf-8') as f:
        json.dump(setting, f, ensure_ascii=False, indent=1)


# ---- 标题栏布局 ----
def layout_topbar():
    tb = {}
    x = 10
    x += font_simyout.size('课程表')[0] + 12
    tb['term_x'] = x
    x += font_simyout.size(setting['Term'])[0] + 10
    tb['prev_rect'] = pygame.Rect(x, 0, 22, 20)
    x += 24
    tb['week_x'] = x
    x += font_simyout.size('第99周')[0] + 8
    tb['next_rect'] = pygame.Rect(x, 0, 22, 20)
    x += 26
    tb['today_rect'] = pygame.Rect(x, 0, 42, 20)
    x += 46
    tb['dayleft_x'] = x
    set_w = font_simyout.size('+设置')[0]
    tb['settings_rect'] = pygame.Rect(win_width - set_w - 14, 0, set_w + 8, 20)
    return tb


TB = layout_topbar()

actual_week = compute_actual_week()
display_week = actual_week  # 当前显示的周数（可切换）


def apply_settings():
    """设置保存后重新应用（窗口尺寸、颜色、透明度等）"""
    global win_width, win_height, class_number, table_width, table_height
    global screen, hwnd, test_color, back_color, class_test_color, TB, actual_week, display_week
    try:
        old = win32gui.GetWindowRect(hwnd)
    except Exception:
        old = None
    win_width = setting['WindowWidth']
    win_height = setting['WindowHeight']
    class_number = setting['ClassNumber']
    table_width = int(win_width / 8)
    table_height = int((win_height - 20) / (class_number + 1))
    test_color = tuple(setting['TestColor'])
    back_color = tuple(setting['BackColor'])
    class_test_color = tuple(setting['ClassTestColor'])
    screen = pygame.display.set_mode((win_width, win_height), pygame.NOFRAME)
    pygame.display.set_caption('课表')
    hwnd = pygame.display.get_wm_info()['window']
    apply_window_style()
    if old:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, old[0], old[1], 0, 0,
                              win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
    actual_week = compute_actual_week()
    display_week = actual_week
    TB = layout_topbar()


# ---- 命中检测 / 提示框 ----
def get_class_at(pos):
    """返回鼠标所在位置的课程 (索引, 时间段下标)，无则返回 None"""
    x, y = pos
    if y < 20 or y >= win_height:
        return None
    col = int(x // table_width)
    row = int((y - 20) // table_height)
    if col < 1 or col > 7:
        return None
    for i, Class in enumerate(class_box):
        for dex, t in enumerate(Class['time']):
            cw, weeks, (start, length) = t
            if cw == col and display_week in weeks and start <= row < start + length:
                return i, dex
    return None


def draw_tooltip(pos, hit):
    i, dex = hit
    Class = class_box[i]
    t = Class['time'][dex]
    cw, weeks, (start, length) = t
    loc = get_loc(Class, dex)
    st = setting['ClassTime'][start - 1][0]
    en = setting['ClassTime'][start + length - 2][1]
    lines = [
        f'课程：{Class["name"]}',
        f'地点：{loc}',
        f'时间：{WEEKDAYS[cw - 1]} {st}~{en}',
        f'周次：{format_weeks(weeks)}',
    ]
    pad = 6
    lh = 16
    w = max(font_tip.size(l)[0] for l in lines) + pad * 2
    h = lh * len(lines) + pad * 2
    tx = pos[0] + 16
    ty = pos[1] + 18
    if tx + w > win_width:
        tx = pos[0] - w - 8
    if ty + h > win_height:
        ty = pos[1] - h - 8
    tx = max(0, min(tx, win_width - w))
    ty = max(0, min(ty, win_height - h))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (255, 255, 255, 238), surf.get_rect(), 0, border_radius=4)
    pygame.draw.rect(surf, (0, 0, 0, 255), surf.get_rect(), 1, border_radius=4)
    screen.blit(surf, (tx, ty))
    for k, l in enumerate(lines):
        screen.blit(font_tip.render(l, True, (0, 0, 0)), (tx + pad, ty + pad + k * lh))


# ---- 绘制 ----
def draw_now_line(weekday):
    now = datetime.now()
    minute_now = now.hour * 60 + now.minute
    ct = []
    for t in setting['ClassTime']:
        sh, sm = map(int, t[0].split(':'))
        eh, em = map(int, t[1].split(':'))
        ct.append([sh * 60 + sm, eh * 60 + em])
    for k in range(class_number):
        start_k, end_k = ct[k]
        if start_k <= minute_now < end_k:
            line_y = 20 + table_height + k * table_height + table_height * (minute_now - start_k) / 45
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y), 1)
            break
        elif k > 0 and ct[k - 1][1] <= minute_now < start_k:
            line_y = 20 + table_height + k * table_height
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y), 1)
            break
        elif k == 0 and minute_now < start_k:
            line_y = 20 + table_height
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y), 1)
            break
        elif k == class_number - 1 and minute_now >= end_k:
            line_y = win_height - 1
            pygame.draw.line(screen, (0, 0, 0), (table_width * weekday, line_y), (table_width * (weekday + 1), line_y), 1)
            break


def draw_frame():
    screen.fill(back_color)

    # ---- 标题栏 ----
    screen.blit(font_simyout.render('课程表', True, test_color), (10, 2))
    screen.blit(font_simyout.render(setting['Term'], True, test_color), (TB['term_x'], 2))

    prev_r = TB['prev_rect']
    pygame.draw.rect(screen, test_color, prev_r, 1, border_radius=2)
    screen.blit(font_simyout.render('<', True, test_color), (prev_r.x + 6, 2))
    wk_color = test_color if display_week == actual_week else (220, 30, 30)
    screen.blit(font_simyout.render(f'第{display_week}周', True, wk_color), (TB['week_x'], 2))
    next_r = TB['next_rect']
    pygame.draw.rect(screen, test_color, next_r, 1, border_radius=2)
    screen.blit(font_simyout.render('>', True, test_color), (next_r.x + 6, 2))
    today_r = TB['today_rect']
    pygame.draw.rect(screen, test_color, today_r, 1, border_radius=2)
    screen.blit(font_simyout.render('今天', True, test_color), (today_r.x + 3, 2))

    today = date.today()
    try:
        day_term_end = date(*tuple(setting['TermEndDate']))
        day_left = (day_term_end - today).days
        screen.blit(font_simyout.render(f'本学期剩余{day_left}天', True, test_color), (TB['dayleft_x'], 2))
    except Exception:
        pass

    sr = TB['settings_rect']
    pygame.draw.rect(screen, test_color, sr, 1, border_radius=3)
    screen.blit(font_simyout.render('+设置', True, test_color), (sr.x + 4, 2))

    month = today.month
    weekday = today.isoweekday()

    # 今天高亮圈
    pygame.draw.circle(screen, (255, 255, 255), (table_width / 2 + weekday * table_width, 20 + table_height / 2),
                       (min(table_width, table_height) - 5) / 2)

    # 网格
    for i in range(20, win_height, table_height):
        pygame.draw.line(screen, test_color, (0, i), (win_width, i), 1)
    for j in range(0, win_width, table_width):
        pygame.draw.line(screen, test_color, (j, 20), (j, win_height), 1)

    # 节数标签与时间（第一列）
    for k in range(1, class_number + 1):
        screen.blit(font_simyout.render(f'第{k}节', True, test_color), (20, 22 + table_height * k))
    for a in range(class_number):
        ct = setting['ClassTime'][a]
        screen.blit(font_time.render(f'{ct[0]}~{ct[1]}', True, test_color), (table_width / 8, 40 + table_height * (a + 1)))

    # 星期名称
    for b in range(1, 8):
        screen.blit(font_simyout.render(WEEKDAYS[b - 1], True, test_color),
                    (table_width - 55 + table_width * b, 20 + table_height / 10))

    # 月份 + 每天日期
    screen.blit(font_simyout.render(f'{month}月', True, test_color), (table_width - 53, 20 + table_height / 3.5))
    for col in range(1, 8):
        d = today + timedelta(days=col - weekday)
        txt = f'{d.month}月{d.day}日' if d.month != today.month else f'{d.day}日'
        surf = font_time.render(txt, True, test_color)
        screen.blit(surf, (table_width * col + (table_width - surf.get_width()) / 2, 20 + table_height / 1.75))

    # 课程
    for Class in class_box:
        for dex in range(len(Class['time'])):
            cw, weeks, (start, length) = Class['time'][dex]
            if display_week in weeks:
                pygame.draw.rect(screen, tuple(Class['color']),
                                 (table_width * cw, 20 + table_height * start, table_width, table_height * length),
                                 0, 15)
                screen.blit(font_simyout.render(Class['name'], True, class_test_color),
                            (table_width * cw + 5, 20 + table_height * start + 5))
                screen.blit(font_simyout.render(get_loc(Class, dex), True, class_test_color),
                            (table_width * cw + 5, 20 + table_height * start + 35))

    # 当前时间线（仅在查看本周时显示）
    if display_week == actual_week:
        draw_now_line(weekday)

    # 悬停提示框
    if not dragging:
        hit = get_class_at(pygame.mouse.get_pos())
        if hit:
            draw_tooltip(pygame.mouse.get_pos(), hit)


# ---- tkinter 弹窗 ----
_tk_root = None


def get_root():
    global _tk_root
    if _tk_root is None:
        _tk_root = tk.Tk()
        _tk_root.withdraw()
    return _tk_root


def _rgb_hex(c):
    return '#%02x%02x%02x' % tuple(int(v) for v in c)


def _position_near_main(win):
    try:
        x, y = win32gui.GetWindowRect(hwnd)[0:2]
        win.geometry(f'+{x + 50}+{y + 50}')
    except Exception:
        pass
    win.attributes('-topmost', True)


def open_course_editor(class_index=None):
    """编辑已有课程（class_index 指定）或新增课程（class_index 为 None）"""
    root = get_root()
    top = tk.Toplevel(root)
    top.title('编辑课程' if class_index is not None else '新增课程')
    top.resizable(False, False)

    editing = class_index is not None
    src = class_box[class_index] if editing else None

    name_var = tk.StringVar(value=src['name'] if src else '')
    color = list(src['color']) if src else [200, 200, 200]

    top_frame = tk.Frame(top)
    top_frame.pack(padx=10, pady=8, anchor='w')
    tk.Label(top_frame, text='课程名称:').pack(side='left')
    tk.Entry(top_frame, textvariable=name_var, width=18).pack(side='left', padx=4)
    swatch = tk.Label(top_frame, text='  颜色  ', bg=_rgb_hex(color), relief='ridge', cursor='hand2')
    swatch.pack(side='left', padx=6)

    def pick_color(_=None):
        c = colorchooser.askcolor(color=_rgb_hex(color), parent=top, title='选择颜色')
        if c and c[1]:
            color[:] = [int(c[1][i:i + 2], 16) for i in (1, 3, 5)]
            swatch.config(bg=_rgb_hex(color))

    swatch.bind('<Button-1>', pick_color)

    # 时间段列表
    list_frame = tk.Frame(top)
    list_frame.pack(padx=10, pady=6, fill='both')
    hdr = tk.Frame(list_frame)
    hdr.pack(anchor='w')
    for t, w in [('星期', 7), ('开始节', 6), ('节数', 5), ('周次(如1-16)', 18), ('地点', 12), ('', 4)]:
        tk.Label(hdr, text=t, width=w, anchor='w').pack(side='left', padx=2)

    rows = []

    def add_row(weekday=1, start=1, length=2, weeks='', loc=''):
        rowf = tk.Frame(list_frame)
        rowf.pack(anchor='w', pady=1)
        wd_var = tk.StringVar(value=WEEKDAYS[weekday - 1])
        st_var = tk.StringVar(value=str(start))
        ln_var = tk.StringVar(value=str(length))
        wk_var = tk.StringVar(value=weeks)
        lo_var = tk.StringVar(value=loc)
        wd = ttk.Combobox(rowf, textvariable=wd_var, values=WEEKDAYS, width=6, state='readonly')
        st = tk.Spinbox(rowf, from_=1, to=class_number, textvariable=st_var, width=5)
        ln = tk.Spinbox(rowf, from_=1, to=class_number, textvariable=ln_var, width=4)
        wk = tk.Entry(rowf, textvariable=wk_var, width=18)
        lo = tk.Entry(rowf, textvariable=lo_var, width=12)
        wd.pack(side='left', padx=2)
        st.pack(side='left', padx=2)
        ln.pack(side='left', padx=2)
        wk.pack(side='left', padx=2)
        lo.pack(side='left', padx=2)
        rec = {'wd': wd_var, 'st': st_var, 'ln': ln_var, 'wk': wk_var, 'lo': lo_var}

        def remove():
            rowf.destroy()
            if rec in rows:
                rows.remove(rec)

        tk.Button(rowf, text='删除', command=remove, width=4).pack(side='left', padx=2)
        rows.append(rec)

    if src:
        for idx, t in enumerate(src['time']):
            cw, weeks, (start, length) = t
            loc = src['loc'][idx] if idx < len(src['loc']) else ''
            add_row(cw, start, length, format_weeks(weeks), loc)
    else:
        add_row()

    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text='+ 添加时间段', command=lambda: add_row()).pack(side='left', padx=6)

    result = {'ok': False}

    def do_save():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning('提示', '请填写课程名称', parent=top)
            return
        new_time, new_loc = [], []
        for rec in rows:
            try:
                weekday = WEEKDAYS.index(rec['wd'].get()) + 1
                start = int(rec['st'].get())
                length = int(rec['ln'].get())
                weeks = parse_weeks(rec['wk'].get())
            except Exception:
                messagebox.showwarning('提示', '周次或节数格式错误', parent=top)
                return
            loc = rec['lo'].get().strip() or '未定'
            new_time.append([weekday, weeks, [start, length]])
            new_loc.append(loc)
        if not new_time:
            messagebox.showwarning('提示', '请至少添加一个时间段', parent=top)
            return
        if editing:
            class_box[class_index]['name'] = name
            class_box[class_index]['color'] = color
            class_box[class_index]['time'] = new_time
            class_box[class_index]['loc'] = new_loc
        else:
            class_box.append({'name': name, 'time': new_time, 'loc': new_loc, 'color': color})
        save_class()
        result['ok'] = True
        top.destroy()

    tk.Button(btn_frame, text='保存', command=do_save).pack(side='left', padx=6)
    tk.Button(btn_frame, text='取消', command=top.destroy).pack(side='left', padx=6)

    _position_near_main(top)
    root.wait_window(top)
    return result['ok']


def open_settings():
    """设置窗口：可改窗口、颜色、节数、上课时间、日期等"""
    root = get_root()
    top = tk.Toplevel(root)
    top.title('设置')
    top.resizable(False, False)

    def row(parent, r, label, var):
        tk.Label(parent, text=label).grid(row=r, column=0, sticky='e', padx=4, pady=2)
        tk.Entry(parent, textvariable=var, width=16).grid(row=r, column=1, padx=4)

    frm = tk.Frame(top)
    frm.pack(padx=12, pady=10)

    var_width = tk.StringVar(value=str(setting['WindowWidth']))
    var_height = tk.StringVar(value=str(setting['WindowHeight']))
    var_classnum = tk.StringVar(value=str(setting['ClassNumber']))
    var_term = tk.StringVar(value=setting['Term'])
    var_transp = tk.StringVar(value=str(setting['Transparency']))
    var_start = tk.StringVar(value='-'.join(map(str, setting['TermStartDate'])))
    var_end = tk.StringVar(value='-'.join(map(str, setting['TermEndDate'])))

    row(frm, 0, '窗口宽度', var_width)
    row(frm, 1, '窗口高度', var_height)
    row(frm, 2, '节数', var_classnum)
    row(frm, 3, '学期名称', var_term)
    row(frm, 4, '透明度(0-255)', var_transp)
    row(frm, 5, '开学日期(年-月-日)', var_start)
    row(frm, 6, '结束日期(年-月-日)', var_end)

    colors = {'TestColor': list(setting['TestColor']),
              'BackColor': list(setting['BackColor']),
              'ClassTestColor': list(setting['ClassTestColor'])}
    color_labels = {'TestColor': '线条颜色', 'BackColor': '背景颜色', 'ClassTestColor': '课程文字颜色'}
    tk.Label(frm, text='颜色').grid(row=7, column=0, sticky='ne', padx=4, pady=2)
    color_frame = tk.Frame(frm)
    color_frame.grid(row=7, column=1, sticky='w')

    def make_color_button(parent, key):
        f = tk.Frame(parent)
        f.pack(anchor='w', pady=1)
        tk.Label(f, text=color_labels[key], width=10, anchor='e').pack(side='left')
        sw = tk.Label(f, text='    ', bg=_rgb_hex(colors[key]), relief='ridge', cursor='hand2')
        sw.pack(side='left', padx=4)

        def pick(_=None):
            c = colorchooser.askcolor(color=_rgb_hex(colors[key]), parent=top)
            if c and c[1]:
                colors[key][:] = [int(c[1][i:i + 2], 16) for i in (1, 3, 5)]
                sw.config(bg=_rgb_hex(colors[key]))

        sw.bind('<Button-1>', pick)

    for k in colors:
        make_color_button(color_frame, k)

    tk.Label(top, text='每节课时间(每行一条, 格式 HH:MM~HH:MM)').pack(anchor='w', padx=12)
    txt = tk.Text(top, width=30, height=max(6, min(12, len(setting['ClassTime']))), font=('Consolas', 10))
    txt.insert('1.0', '\n'.join(f'{a}~{b}' for a, b in setting['ClassTime']))
    txt.pack(padx=12, pady=4)

    tk.Label(top, text='窗口大小、节数修改后立即生效').pack(anchor='w', padx=12, pady=(0, 4))

    result = {'ok': False}

    def do_save():
        try:
            w = int(var_width.get())
            h = int(var_height.get())
            n = int(var_classnum.get())
            t = int(var_transp.get())
        except ValueError:
            messagebox.showwarning('提示', '数值格式错误', parent=top)
            return
        if not (1 <= t <= 255):
            messagebox.showwarning('提示', '透明度需在 0-255 之间', parent=top)
            return
        if w < 200 or h < 200 or n < 1 or n > 20:
            messagebox.showwarning('提示', '尺寸或节数超出范围', parent=top)
            return
        try:
            sd = [int(x) for x in var_start.get().replace('/', '-').split('-')]
            ed = [int(x) for x in var_end.get().replace('/', '-').split('-')]
            if len(sd) != 3 or len(ed) != 3:
                raise ValueError
            date(*sd)
            date(*ed)
        except Exception:
            messagebox.showwarning('提示', '日期格式错误(应为 年-月-日)', parent=top)
            return
        ct = []
        for line in txt.get('1.0', 'end').splitlines():
            line = line.strip()
            if not line:
                continue
            line = line.replace('－', '-').replace('—', '-').replace('：', ':').replace(' ', '')
            if '~' in line:
                a, b = line.split('~', 1)
            elif '-' in line:
                a, b = line.split('-', 1)
            else:
                messagebox.showwarning('提示', '时间格式错误', parent=top)
                return
            try:
                datetime.strptime(a, '%H:%M')
                datetime.strptime(b, '%H:%M')
            except ValueError:
                messagebox.showwarning('提示', '时间格式错误', parent=top)
                return
            ct.append([a, b])
        if len(ct) != n:
            messagebox.showwarning('提示', f'时间条数({len(ct)})应与节数({n})一致', parent=top)
            return

        setting['WindowWidth'] = w
        setting['WindowHeight'] = h
        setting['ClassNumber'] = n
        setting['Term'] = var_term.get().strip() or setting['Term']
        setting['Transparency'] = t
        setting['TermStartDate'] = sd
        setting['TermEndDate'] = ed
        setting['TestColor'] = colors['TestColor']
        setting['BackColor'] = colors['BackColor']
        setting['ClassTestColor'] = colors['ClassTestColor']
        setting['ClassTime'] = ct
        save_setting()
        result['ok'] = True
        top.destroy()

    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text='保存', command=do_save).pack(side='left', padx=8)
    tk.Button(btn_frame, text='取消', command=top.destroy).pack(side='left', padx=8)

    _position_near_main(top)
    root.wait_window(top)
    if result['ok']:
        apply_settings()
    return result['ok']


def open_main_menu():
    """右上角按钮：新增课程 / 设置"""
    root = get_root()
    top = tk.Toplevel(root)
    top.title('菜单')
    top.resizable(False, False)

    def add():
        top.destroy()
        open_course_editor(None)

    def st():
        top.destroy()
        open_settings()

    tk.Button(top, text='新增课程', width=16, command=add).pack(padx=16, pady=(12, 8))
    tk.Button(top, text='设置', width=16, command=st).pack(padx=16, pady=(0, 12))

    _position_near_main(top)
    root.wait_window(top)


# ---- 点击处理 ----
def handle_click(pos):
    global display_week
    if pos[1] < 20:
        if TB['settings_rect'].collidepoint(pos):
            open_main_menu()
            return True
        if TB['prev_rect'].collidepoint(pos):
            display_week = max(1, display_week - 1)
            return True
        if TB['next_rect'].collidepoint(pos):
            display_week = min(30, display_week + 1)
            return True
        if TB['today_rect'].collidepoint(pos):
            display_week = actual_week
            return True
        return False
    hit = get_class_at(pos)
    if hit:
        open_course_editor(hit[0])
        return True
    return False


# ---- 主循环 ----
drag_offset = (0, 0)
clock = pygame.time.Clock()
running = True
dragging = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not handle_click(event.pos) and event.pos[1] < 20:
                mx, my = win32api.GetCursorPos()
                win_rect = win32gui.GetWindowRect(hwnd)
                drag_offset = (mx - win_rect[0], my - win_rect[1])
                dragging = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False

        if event.type == pygame.MOUSEMOTION and dragging:
            mx, my = win32api.GetCursorPos()
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, mx - drag_offset[0], my - drag_offset[1], 0, 0,
                                  win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)

    draw_frame()
    pygame.display.update()
    clock.tick(fps)

pygame.quit()
sys.exit()
