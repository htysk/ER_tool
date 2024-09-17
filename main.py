import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import os
import sqlite3
import random

entity_list = []

window_width = 1600
window_height = 1000
canvas_width = 1200
canvas_height = 800

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def set(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.x},{self.y}'

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

class Entity():
    def __init__(self, canvas, point, text, size=20):
        self.canvas = canvas
        self.point = Point(point.x+1, point.y+1)
        self.text = text
        self.size = size
        self.start_point = Point(None, None)
        self.id = {'rectangle':None, 'text':None}
        self.connections = []

        # テキストの大きさを取得
        id = self.canvas.create_text(self.point.x, self.point.y, text=self.text, font=('', self.size))
        x1, y1, x2, y2 = self.canvas.bbox(id)
        self.width = (x2-x1)
        self.height = (y2-y1)
        self.canvas.delete(id)

        # エンティティを描画
        self.draw_entity()

        for id in self.id.values():
            self.canvas.tag_bind(id, '<ButtonPress>', self.button_press)
            self.canvas.tag_bind(id, '<Motion>', self.move)
            self.canvas.tag_bind(id, '<ButtonRelease>', self.button_release)
        
        entity_list.append(self)

    def draw_entity(self):
        self.point.x, self.point.y = self.check_point(self.point)
        
        self.id['rectangle'] = self.canvas.create_rectangle(self.point.x, self.point.y, self.point.x+self.width, self.point.y+self.height, fill='white')
        self.id['text'] = self.canvas.create_text(self.point.x+(self.width//2), self.point.y+(self.height//2), text=self.text, font=('', self.size))
    
    def move_entity(self, canvas_point):
        sub_point = self.start_point - canvas_point
        coords = self.canvas.coords(self.id['rectangle'])
        for e in entity_list:
            if e == self:
                continue
            center_point = self.get_center()
            other_center_point = e.get_center()
            if abs(center_point.x - other_center_point.x) <= (self.width + e.width) / 2 and abs(center_point.y - other_center_point.y) <= (self.height + e.height) / 2:
                sub_point.set(1 if sub_point.x > 0 else -1, 0 if sub_point.y > 0 else -1)
        coords[0] -= sub_point.x
        coords[1] -= sub_point.y
        coords[0], coords[1] = self.check_point(Point(coords[0], coords[1]))
        coords[2] = coords[0] + self.width
        coords[3] = coords[1] + self.height
        self.canvas.coords(self.id['rectangle'], coords)

        coords[0] = coords[0] + (self.width//2)
        coords[1] = coords[1] + (self.height//2)
        self.canvas.coords(self.id['text'], coords[:2])

    def check_point(self, point):
        x = 0 if point.x < 0 else point.x
        y = 0 if point.y < 0 else point.y
        x = canvas_width-self.width if point.x > canvas_width-self.width else x
        y = canvas_height-self.height if point.y > canvas_height-self.height else y
        return x, y
    
    def button_press(self, event):
        self.start_point.set(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
    
    def move(self, event):
        if self.start_point.x is None:
            return
        if event.state & 256:
            canvas_point = Point(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self.move_entity(canvas_point)
            self.start_point.set(canvas_point.x, canvas_point.y)
            coords = self.canvas.coords(self.id['rectangle'])
            self.point.set(coords[0], coords[1])
            for connection in self.connections:
                connection.move(self)
    
    def button_release(self, event):
        self.start_point.set(None, None)
    
    def get_center(self):
        return self.point + Point(self.width//2, self.height//2)
    
    def add_listener(self, connection):
        self.connections.append(connection)

class Connection():
    def __init__(self, canvas, start_entity, end_entity, color='black'):
        self.canvas = canvas
        self.start_e = start_entity
        self.end_e = end_entity
        self.start_e.add_listener(self)
        self.end_e.add_listener(self)

        self.id = self.canvas.create_line(self.get_intersection(self.start_e), self.get_intersection(self.end_e), fill=color, width=5)
    
    def get_intersection(self, entity):
        point = entity.get_center()
        h = entity.height // 2
        w = entity.width // 2
        dx = self.end_e.point.x - self.start_e.point.x
        dy = self.end_e.point.y - self.start_e.point.y
        if entity == self.end_e:
            dx, dy = -dx, -dy
        if dx != 0 and abs(dy / dx) < (h / w):
            x_pos = point.x + w if dx > 0 else point.x - w
            y_pos = point.y + dy * w / abs(dx)
        else:
            x_pos = point.x + dx * h / abs(dy)
            y_pos = point.y + h if dy > 0 else point.y - h
        return x_pos, y_pos
    
    def move(self, entity):
        point = entity.get_center()
        coords = self.canvas.coords(self.id)
        if entity == self.start_e:
            coords[0:2] = self.get_intersection(entity)
            coords[2:4] = self.get_intersection(self.end_e)
        elif entity == self.end_e:
            coords[0:2] = self.get_intersection(self.start_e)
            coords[2:4] = self.get_intersection(entity)
        self.canvas.coords(self.id, coords)

class Application(tk.Tk):
    def __init__(self):
        self.table_list = {}
        self.connect_list = {}

        super().__init__()
        self.title('ER図')
        self.geometry(f'{window_width}x{window_height}')

        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height, background='white')
        self.canvas.grid(row=0, column=0)

        listframe = tk.Frame(self)
        self.list_view = ttk.Treeview(listframe, show='headings', columns=('t', 'l'), selectmode='browse', height=5)
        #self.list_view.bind('<<TreeviewSelect>>', self.view_select)
        self.list_view.heading('t', text='テーブル名', anchor='center')
        self.list_view.heading('l', text='接続数', anchor='center')
        self.list_view.column('t', anchor='center')
        self.list_view.column('l', width=75, anchor='center')
        self.draw_table_list()
        self.list_view.grid(row=0,column=0, rowspan=5)

        button_new_table = tk.Button(listframe, text='テーブル登録')
        button_copy_table = tk.Button(listframe, text='テーブルコピー')
        button_rename_table = tk.Button(listframe, text='テーブル修正')
        button_delete_table = tk.Button(listframe, text='テーブル削除')
        button_new_table.bind('<ButtonRelease-1>', self.regist_window)
        button_copy_table.bind('<ButtonRelease-1>', self.copy_table)
        button_rename_table.bind('<ButtonRelease-1>', self.edit_window)
        button_delete_table.bind('<ButtonRelease-1>', self.delete_table)
        button_new_table.grid(row=1, column=1)
        button_copy_table.grid(row=2, column=1)
        button_rename_table.grid(row=3, column=1)
        button_delete_table.grid(row=4, column=1)
        listframe.grid(row=0, column=1, sticky='nsew')

        buttonframe = tk.Frame(self)
        #self.list_view = ttk.Treeview(listframe, show='headings', columns=('t', 'l'), selectmode='browse', height=5)
        #self.list_view.bind('<<TreeviewSelect>>', self.view_select)
        #self.list_view.heading('t', text='テーブル名', anchor='center')
        #self.list_view.heading('l', text='接続数', anchor='center')
        #self.list_view.column('t', anchor='center')
        #self.list_view.column('l', width=75, anchor='center')
        #self.draw_table_detail()
        #self.list_view.grid(row=0,column=0, rowspan=5)
        buttonframe.grid(row=1, column=1, sticky='nsew')

        #insert_connection('ターゲット', '店舗マスタ', [['得意先コード', '得意先コード']], [None])
        #self.draw_table_list()

        #entity1 = Entity(self.canvas, Point(40, 80), 'ターゲット')
        #entity2 = Entity(self.canvas, Point(800, 300), '店舗マスタ')
        #Connection(self.canvas, entity1, entity2)
    
    def select_item(self, event):
        pass

    def draw_entity(self):
        tables = get_tables()
        for table in tables:
            table = table[0]
            if table not in self.table_list:
                self.table_list[table] = Entity(self.canvas, Point(random.randint(0, canvas_width), random.randint(0, canvas_height)), table)
                #self.canvas.tag_bind(self.table_list[table].id['text'], '<ButtonPress>', self.select_item)

    def draw_connection(self):
        tables, keys = get_connection()
        for i, (st, es) in enumerate(tables):
            if f'{st}-{es}' not in self.connect_list:
                self.connect_list[f'{st}-{es}'] = Connection(self.canvas, self.table_list[st], self.table_list[es], 'black' if keys[i][2] is None else 'red')

    def draw_table_list(self):
        self.list_view.delete(*self.list_view.get_children())
        table_list = get_tables()
        for i in range(len(table_list)):
            con_table, _ = get_connection(table_list[i][0])
            self.list_view.insert(parent='', index='end', iid=i, values=(table_list[i][0], len(con_table)))
        self.list_view.grid(row=0, column=0, sticky='nsew')
        self.draw_entity()
        self.draw_connection()

    def file_dialog(self, event, sub_win, entry, column_entry_list):
        filename = tk.filedialog.askopenfilename(filetypes=[("", ".csv")], initialdir=os.path.abspath(os.path.dirname(__file__)))
        if len(filename) != 0:
            fp = open(filename, 'r', encoding='utf-8')
            columns = fp.readline().strip().split(',')
            fp.close()
            table_name = os.path.splitext(os.path.basename(filename))[0]
            #insert_table(table_name, columns)
            #self.draw_table_list()
            entry.insert(0, table_name)
            for l, e in column_entry_list:
                l.destroy()
                e.destroy()
            del column_entry_list[:]
            self.num = 3
            while self.num-3 < len(columns):
                self.add_entry(event, sub_win)
            for i in range(0, len(columns)):
                column_entry_list[i][1].insert(0, columns[i])
    
    def regist_window(self, event):
        sub_win = tk.Toplevel()
        sub_win.geometry('300x300')

        button_file_dialog = tk.Button(sub_win, text='ファイル読み込み', command=lambda : self.file_dialog(event, sub_win, entry, self.column_entry_list))
        button_add = tk.Button(sub_win, text='列追加', command=lambda: self.add_entry(event, sub_win))
        button_regist = tk.Button(sub_win, text='登録', command=lambda: self.regist_table(event, sub_win, entry.get(), self.column_entry_list))
        button_cancel = tk.Button(sub_win, text='キャンセル', command=lambda : sub_win.destroy())
        button_file_dialog.grid(row=1, column=0)
        button_add.grid(row=1, column=1)
        button_regist.grid(row=1, column=2)
        button_cancel.grid(row=1, column=3)
        label = tk.Label(sub_win, text='テーブル名', anchor='center')
        entry = tk.Entry(sub_win, width=20)
        label.grid(row=2, column=0, columnspan=1)
        entry.grid(row=2, column=2, columnspan=3)
        self.num = 3
        self.column_entry_list = []
        for i in range(self.num, self.num+5):
            self.add_entry(event, sub_win)

    def add_entry(self, event, sub_win):
        label = tk.Label(sub_win, text=f'列{self.num-2}', anchor='center')
        entry = tk.Entry(sub_win, width=20)
        label.grid(row=self.num, column=0, columnspan=1)
        entry.grid(row=self.num, column=2, columnspan=3)
        self.column_entry_list.append([label, entry])
        self.num += 1

    def regist_table(self, event, sub_win, table_name, column_entry_list):
        if table_name == '':
            return

        table_list = get_tables()
        if (table_name,) in table_list:
            print('既にテーブルがあります。')
            return

        columns = []
        for _, entry in column_entry_list:
            if entry.get() != '':
                if entry.get() in columns:
                    print('列名がかぶっています。')
                    return
                columns.append(entry.get())
        if len(columns) <= 0:
            print('列が入力されていない')
            return
        insert_table(table_name, columns)
        self.draw_table_list()
        sub_win.destroy()

    def copy_table(self, event):
        slct_index = self.list_view.focus()
        if slct_index == '':
            return
        table_list = get_tables()
        ori_table_name = table_list[int(slct_index)][0]
        columns = get_table_columns(ori_table_name)
        table_name = ori_table_name
        num = 1
        while (table_name,) in table_list:
            table_name = f'{ori_table_name}_{num}'
            num += 1
            table_list = get_tables()
        insert_table(table_name, columns)
        self.draw_table_list()

    def init_data(self, event, sub_win, table_name, columns):
        label = tk.Label(sub_win, text='テーブル名', anchor='center')
        entry = tk.Entry(sub_win, width=20)
        entry.insert(0, table_name)
        label.grid(row=2, column=0, columnspan=1)
        entry.grid(row=2, column=2, columnspan=3)
        self.num = 3
        self.column_entry_list = [[label, entry]]
        while self.num-3 < len(columns):
            self.add_entry(event, sub_win)
        for i in range(0, len(columns)):
            self.column_entry_list[i+1][1].insert(0, columns[i])

    def edit_window(self, event):
        slct_index = self.list_view.focus()
        if slct_index == '':
            return
        table_list = get_tables()
        table_name = table_list[int(slct_index)][0]
        columns = get_table_columns(table_name)

        sub_win = tk.Toplevel()
        sub_win.geometry('300x300')

        button_file_dialog = tk.Button(sub_win, text='元に戻す', command=lambda : self.init_data(event, sub_win, table_name, columns))
        button_add = tk.Button(sub_win, text='列追加', command=lambda: self.add_entry(event, sub_win))
        button_regist = tk.Button(sub_win, text='修正', command=lambda: self.edit_table(event, sub_win, table_name, self.column_entry_list))
        button_cancel = tk.Button(sub_win, text='キャンセル', command=lambda : sub_win.destroy())
        button_file_dialog.grid(row=1, column=0)
        button_add.grid(row=1, column=1)
        button_regist.grid(row=1, column=2)
        button_cancel.grid(row=1, column=3)

        self.init_data(None, sub_win, table_name, columns)
        
        #label = tk.Label(sub_win, text=table_name, anchor='center')
        #down_label = tk.Label(sub_win, text='↓', anchor='center')
        #entry = tk.Entry(sub_win, width=20)
        #button_rename = tk.Button(sub_win, text='リネーム', command=lambda: self.rename_table(event, sub_win, table_name, entry.get()))
        #button_cancel = tk.Button(sub_win, text='キャンセル', command=lambda : sub_win.destroy())
        #label.grid(row=0, column=0, columnspan=2, sticky='nsew')
        #down_label.grid(row=1, column=0, columnspan=2, sticky='nsew')
        #entry.grid(row=2, column=0, columnspan=2, sticky='nsew')
        #button_rename.grid(row=3, column=0, sticky='nsew')
        #button_cancel.grid(row=3, column=1, sticky='nsew')

    def edit_table(self, event, sub_win, old_table_name, column_entry_list):
        new_table_name = column_entry_list[0][1].get()
        if new_table_name == '':
            return
        columns = []
        for _, e in column_entry_list[1:]:
            columns.append(e.get())
        update_table(old_table_name, new_table_name)
        update_columns(new_table_name, columns)
        self.draw_table_list()
        sub_win.destroy()

    def delete_table(self, event):
        slct_index = self.list_view.focus()
        if slct_index == '':
            return
        table_list = get_tables()
        delete_table(table_list[int(slct_index)][0])
        self.draw_table_list()

        self.canvas.delete(self.table_list[table_list[int(slct_index)][0]].id['text'])
        self.canvas.delete(self.table_list[table_list[int(slct_index)][0]].id['rectangle'])
        del self.table_list[table_list[int(slct_index)][0]]

        delete_con_keys = []
        for k in self.connect_list:
            if f'{table_list[int(slct_index)][0]}-' in k or f'-{table_list[int(slct_index)][0]}' in k:
                delete_con_keys.append(k)
        for k in delete_con_keys:
            self.canvas.delete(self.connect_list[k].id)
            del self.connect_list[k]

    def view_select(self, event):
        pass

def init_table():
    if not os.path.exists('table.db'):
        conn = sqlite3.connect('table.db')
        cur = conn.cursor()

        sql = """CREATE TABLE table_list (
        table_name TEXT PRIMARY KEY
        )"""
        cur.execute(sql)

        sql = """CREATE TABLE table_columns (
        table_name TEXT NOT NULL,
        column TEXT NOT NULL
        )"""
        cur.execute(sql)
    
        sql = """CREATE TABLE table_connection (
        start_table TEXT NOT NULL,
        end_table TEXT NOT NULL,
        start_column TEXT NOT NULL,
        end_column TEXT NOT NULL,
        timeER TEXT
        )"""
        cur.execute(sql)

        conn.commit()
        conn.close()

def insert_table(table_name, columns):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    table_list = get_tables()
    ori_table_name = table_name
    num = 1
    while (table_name,) in table_list:
        table_name = f'{ori_table_name}_{num}'
        num += 1
        table_list = get_tables()

    sql = """INSERT INTO table_list (table_name) VALUES (?)"""
    cur.execute(sql, [table_name])

    for col in columns:
        sql = """INSERT INTO table_columns (table_name,column) VALUES (?, ?)"""
        cur.execute(sql, (table_name, col))

    conn.commit()
    conn.close()

def insert_connection(start_table, end_table, connection_columns, timeERs):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    for i, (start_col, end_col) in enumerate(connection_columns):
        if timeERs[i] is None:
            sql = """INSERT INTO table_connection (start_table, end_table, start_column, end_column) VALUES (?, ?, ?, ?)"""
            cur.execute(sql, [start_table, end_table, start_col, end_col])
            cur.execute(sql, [end_table, start_table, end_col, start_col])
        else:
            sql = """INSERT INTO table_connection (start_table, end_table, start_column, end_column, timeER) VALUES (?, ?, ?, ?, ?)"""
            cur.execute(sql, [start_table, end_table, start_col, end_col, timeERs[i]])
            cur.execute(sql, [end_table, start_table, end_col, start_col, timeERs[i]])

    conn.commit()
    conn.close()

def update_table(old_table_name, new_table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """UPDATE table_list SET table_name=? WHERE table_name=?"""
    cur.execute(sql, [new_table_name, old_table_name])

    sql = """UPDATE table_columns SET table_name=? WHERE table_name=?"""
    cur.execute(sql, [new_table_name, old_table_name])

    conn.commit()
    conn.close()

def update_columns(table_name, columns):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """DELETE FROM table_columns WHERE table_name=?"""
    cur.execute(sql, [table_name])

    for col in columns:
        sql = """INSERT INTO table_columns (table_name,column) VALUES (?, ?)"""
        cur.execute(sql, (table_name, col))

    conn.commit()
    conn.close()

def delete_table(table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """DELETE FROM table_list WHERE table_name=?"""
    cur.execute(sql, [table_name])

    sql = """DELETE FROM table_columns WHERE table_name=?"""
    cur.execute(sql, [table_name])

    sql = """DELETE FROM table_connection WHERE start_table=?"""
    cur.execute(sql, [table_name])
    sql = """DELETE FROM table_connection WHERE end_table=?"""
    cur.execute(sql, [table_name])

    conn.commit()
    conn.close()

def get_tables():
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT * FROM table_list'
    cur.execute(sql)
    table_list = cur.fetchall()
    conn.close()
    return table_list

def get_table_columns(table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT column FROM table_columns WHERE table_name=?'
    cur.execute(sql, [table_name])
    table_columns = []
    for col in cur.fetchall():
        table_columns.append(col[0])
    conn.close()
    return table_columns

def get_connection(start_table=None, end_table=None):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    tables = []
    keys = []
    if start_table is None:
        sql = 'SELECT * FROM table_connection'
        cur.execute(sql)
        for col in cur.fetchall():
            tables.append([col[0], col[1]])
            keys.append([col[2], col[3], col[4]])
    elif end_table is None:
        sql = 'SELECT * FROM table_connection WHERE start_table=?'
        cur.execute(sql, [start_table])
        for col in cur.fetchall():
            tables.append(col[1])
            keys.append([col[2], col[3], col[4]])
    else:
        sql = 'SELECT * FROM table_connection WHERE start_table=? and end_table=?'
        cur.execute(sql, [start_table, end_table])
        for col in cur.fetchall():
            keys.append([col[2], col[3], col[4]])
    conn.close()
    return tables, keys


def main():
    init_table()
    application = Application()
    application.mainloop()

if __name__ == '__main__':
    main()
