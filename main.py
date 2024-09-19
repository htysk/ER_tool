import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import os
import sqlite3
import random

entity_list = {}

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
    def __init__(self, main_window, canvas, point, text, size=20, is_move=True):
        self.main_window = main_window
        self.canvas = canvas
        self.point = Point(point.x+1, point.y+1)
        self.text = text
        self.size = size
        self.start_point = Point(None, None)
        self.id = {'rectangle':None, 'text':None}
        self.connections = []

        self.set_size()

        # エンティティを描画
        self.draw_entity()

        if is_move:
            for id in self.id.values():
                self.canvas.tag_bind(id, '<ButtonPress>', self.button_press)
                self.canvas.tag_bind(id, '<Motion>', self.move)
                self.canvas.tag_bind(id, '<ButtonRelease>', self.button_release)
        
        if self.canvas in entity_list:
            entity_list[self.canvas].append(self)
        else:
            entity_list[self.canvas] = [self]

    def draw_entity(self):
        self.point.x, self.point.y = self.check_point(self.point)
        
        self.id['rectangle'] = self.canvas.create_rectangle(self.point.x, self.point.y, self.point.x+self.width, self.point.y+self.height, fill='white')
        self.id['text'] = self.canvas.create_text(self.point.x+(self.width//2), self.point.y+(self.height//2), text=self.text, font=('', self.size))
    
    def set_size(self):
        # テキストの大きさを取得
        id = self.canvas.create_text(self.point.x, self.point.y, text=self.text, font=('', self.size))
        x1, y1, x2, y2 = self.canvas.bbox(id)
        self.width = (x2-x1)
        self.height = (y2-y1)
        self.canvas.delete(id)

    def update_text(self, new_text):
        self.text = new_text
        self.set_size()
        coords = self.canvas.coords(self.id['rectangle'])
        coords[0], coords[1] = self.check_point(self.point)
        coords[2] = coords[0] + self.width
        coords[3] = coords[1] + self.height
        self.canvas.coords(self.id['rectangle'], coords)
        self.canvas.itemconfigure(self.id['text'], text=new_text)
        coords[0] = coords[0] + (self.width//2)
        coords[1] = coords[1] + (self.height//2)
        self.canvas.coords(self.id['text'], coords[:2])

    def move_entity(self, canvas_point):
        sub_point = self.start_point - canvas_point
        coords = self.canvas.coords(self.id['rectangle'])
        for e in entity_list[self.canvas]:
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
        self.main_window.list_views['テーブル一覧'].selection_set(get_table_no(self.text)-1)
        self.main_window.list_views['テーブル一覧'].focus(get_table_no(self.text)-1)
        #self.main_window.draw()
    
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
    def __init__(self, canvas, start_entity, end_entity, width=5, color='black', sub_point=0):
        self.canvas = canvas
        self.start_e = start_entity
        self.end_e = end_entity
        self.start_e.add_listener(self)
        self.end_e.add_listener(self)
        self.sub_point = sub_point

        self.id = self.canvas.create_line(self.get_intersection(self.start_e), self.get_intersection(self.end_e), fill=color, width=width)
    
    def get_intersection(self, entity):
        point = entity.get_center()
        point = point - Point(self.sub_point, self.sub_point)
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

class RegistWindow(tk.Toplevel):
    def __init__(self, main_window):
        super().__init__()
        
        # 定数
        self.window_width = 300
        self.window_height = 300
        
        # 引数をインスタンス変数
        self.main_window = main_window
        self.canvas = main_window.canvas
        
        # インスタンス変数
        self.buttons = {}
        self.column_entry_list = []
        
        self.title('テーブル登録')
        self.geometry(f'{self.window_width}x{self.window_height}')
        
        self.buttons['ファイル読み込み'] = tk.Button(self, text='ファイル読み込み', command=self.file_dialog)
        self.buttons['列追加'] = tk.Button(self, text='列追加', command=self.add_entry)
        self.buttons['登録'] = tk.Button(self, text='登録', command=self.regist_table)
        self.buttons['キャンセル'] = tk.Button(self, text='キャンセル', command=self.destroy)
        self.buttons['ファイル読み込み'].grid(row=1, column=0)
        self.buttons['列追加'].grid(row=1, column=1)
        self.buttons['登録'].grid(row=1, column=2)
        self.buttons['キャンセル'].grid(row=1, column=3)
        
        label_table_name = tk.Label(self, text='テーブル名', anchor='center')
        self.entry_table_name = tk.Entry(self, width=20)
        label_table_name.grid(row=2, column=0, columnspan=1)
        self.entry_table_name.grid(row=2, column=2, columnspan=3)
        
        for _ in range(0, 5):
            self.add_entry()
        
    def file_dialog(self):
        filename = tk.filedialog.askopenfilename(parent=self, filetypes=[("", ".csv")], initialdir=os.path.abspath(os.path.dirname(__file__)))
        if len(filename) != 0:
            fp = open(filename, 'r', encoding='utf-8')
            columns = fp.readline().strip().split(',')
            fp.close()
            table_name = os.path.splitext(os.path.basename(filename))[0]
            #insert_table(table_name, columns)
            #self.draw_table_list()
            self.entry_table_name.insert(0, table_name)
            for l, e in self.column_entry_list:
                l.destroy()
                e.destroy()
            del self.column_entry_list[:]
            
            while len(self.column_entry_list) < len(columns):
                self.add_entry()
            for i in range(0, len(columns)):
                self.column_entry_list[i][1].insert(0, columns[i])
        
        self.lift()

    def add_entry(self):
        label = tk.Label(self, text=f'列{len(self.column_entry_list)+1}', anchor='center')
        entry = tk.Entry(self, width=20)
        label.grid(row=len(self.column_entry_list)+3, column=0, columnspan=1)
        entry.grid(row=len(self.column_entry_list)+3, column=2, columnspan=3)
        self.column_entry_list.append([label, entry])

    def regist_table(self):
        table_name = self.entry_table_name.get()
        
        if table_name == '':
            return

        table_list = get_tables()
        if table_name in table_list:
            print('既にテーブルがあります。')
            return

        columns = []
        for _, entry in self.column_entry_list:
            if entry.get() != '':
                if entry.get() in columns:
                    print('列名がかぶっています。')
                    return
                columns.append(entry.get())
        if len(columns) <= 0:
            print('列が入力されていない')
            return
        insert_table(table_name, columns)
        
        self.main_window.draw()
        self.destroy()

class EditWindow(tk.Toplevel):
    def __init__(self, main_window, table_name):
        super().__init__()
        
        # 定数
        self.window_width = 300
        self.window_height = 300
        
        # 引数をインスタンス変数
        self.main_window = main_window
        self.canvas = main_window.canvas
        self.table_name = table_name

        # インスタンス変数
        self.buttons = {}
        self.column_entry_list = []
        
        self.title('テーブル修正')
        self.geometry(f'{self.window_width}x{self.window_height}')

        self.buttons['元に戻す'] = tk.Button(self, text='元に戻す', command=self.init_data)
        self.buttons['列追加'] = tk.Button(self, text='列追加', command=self.add_entry)
        self.buttons['修正'] = tk.Button(self, text='修正', command=self.edit_table)
        self.buttons['キャンセル'] = tk.Button(self, text='キャンセル', command=self.destroy)
        self.buttons['元に戻す'].grid(row=1, column=0)
        self.buttons['列追加'].grid(row=1, column=1)
        self.buttons['修正'].grid(row=1, column=2)
        self.buttons['キャンセル'].grid(row=1, column=3)

        label_table_name = tk.Label(self, text='テーブル名', anchor='center')
        self.entry_table_name = tk.Entry(self, width=20)
        label_table_name.grid(row=2, column=0, columnspan=1)
        self.entry_table_name.grid(row=2, column=2, columnspan=3)

        self.init_data()

    def init_data(self):
        self.entry_table_name.delete(0, tk.END)
        for l, e in self.column_entry_list:
            l.destroy()
            e.destroy()
        self.column_entry_list = []

        self.entry_table_name.insert(0, self.table_name)

        columns = get_table_columns(self.table_name)
        while len(self.column_entry_list) < len(columns):
            self.add_entry()
        for i in range(0, len(columns)):
            self.column_entry_list[i][1].insert(0, columns[i])

    def add_entry(self):
        label = tk.Label(self, text=f'列{len(self.column_entry_list)+1}', anchor='center')
        entry = tk.Entry(self, width=20)
        label.grid(row=len(self.column_entry_list)+3, column=0, columnspan=1)
        entry.grid(row=len(self.column_entry_list)+3, column=2, columnspan=3)
        self.column_entry_list.append([label, entry])

    def edit_table(self):
        new_table_name = self.entry_table_name.get()
        if new_table_name == '':
            return
        
        columns = []
        for _, e in self.column_entry_list:
            columns.append(e.get())
        
        update_table(self.table_name, new_table_name)
        update_columns(new_table_name, columns)

        self.main_window.table_list[self.table_name].update_text(new_table_name)
        self.main_window.table_list[new_table_name] = self.main_window.table_list[self.table_name]
        del self.main_window.table_list[self.table_name]

        update_conn = []
        for k in self.main_window.connect_list:
            if f'{self.table_name}-' in k or f'-{self.table_name}' in k:
                self.main_window.connect_list[k.replace(self.table_name, new_table_name)] = self.main_window.connect_list[k]
                update_conn.append(k)
        for k in update_conn:
            del self.main_window.connect_list[k]

        self.main_window.draw()
        self.destroy()

class RegistERWindow(tk.Toplevel):
    def __init__(self, main_window):
        super().__init__()

        # 定数
        self.window_width = 700
        self.window_height = 600
        
        # 引数をインスタンス変数
        self.main_window = main_window
        self.canvas = main_window.canvas

        # インスタンス変数
        self.buttons = {}
        self.canvases = {}
        self.table_radiobtn = {'left': {}, 'right': {}}
        self.column_radiobtn = {'left': {}, 'right': {}}
        self.table_radiobtn_value = {'left': tk.StringVar(value=''), 'right': tk.StringVar(value='')}
        self.column_radiobtn_value = {'left': tk.StringVar(value=''), 'right': tk.StringVar(value='')}
        
        self.title('ER追加')
        self.geometry(f'{self.window_width}x{self.window_height}')

        button_frame = tk.Frame(self, background='white')
        self.buttons['完了'] = tk.Button(button_frame, text='完了', command=self.commit)
        self.buttons['キャンセル'] = tk.Button(button_frame, text='キャンセル', command=self.destroy)
        self.buttons['完了'].grid(row=0, column=1, sticky='w')
        self.buttons['キャンセル'].grid(row=0, column=2, sticky='w')
        button_frame.grid(row=0, column=0, columnspan=4)

        self.canvases['left_table'] = tk.Canvas(self, width=150, height=550, background='white')
        self.draw_table('left')
        self.canvases['left_table'].grid(row=1, column=0, rowspan=3)

        self.canvases['connection_table'] = tk.Canvas(self, width=300, height=250, background='white')
        self.canvases['connection_table'].grid(row=1, column=1, columnspan=2)

        self.canvases['right_table'] = tk.Canvas(self, width=150, height=550, background='white')
        self.draw_table('right')
        self.canvases['right_table'].grid(row=1, column=3, rowspan=3)

        self.buttons['ER追加'] = tk.Button(self, text='ER追加', command=self.add_er)
        self.buttons['ER追加'].grid(row=2, column=1)
        self.buttons['ER削除'] = tk.Button(self, text='ER削除', command=self.del_er)
        self.buttons['ER削除'].grid(row=2, column=2)

        self.canvases['left_column'] = tk.Canvas(self, width=150, height=250, background='white')
        self.canvases['left_column'].grid(row=3, column=1)


        self.canvases['right_column'] = tk.Canvas(self, width=150, height=250, background='white')
        self.canvases['right_column'].grid(row=3, column=2)

    def draw_table(self, side):
        table_list = get_tables()
        height_seq = 0
        for table in table_list:
            if self.table_radiobtn_value['right' if side=='left' else 'left'].get() != table:
                self.table_radiobtn[side][table] = tk.Radiobutton(self.canvases[f'{side}_table'], text=table, command=lambda : self.table_click('left'), variable=self.table_radiobtn_value['left'], value=table, background='white', font=('', 15))
                self.table_radiobtn[side][table].place(x=0, y=height_seq)
                self.table_radiobtn[side][table].update_idletasks()
                if height_seq == 0:
                    self.table_radiobtn[side][table].invoke()
                height_seq += self.table_radiobtn[side][table].winfo_height()

    def draw_columns(self, side):
        pass

    def add_er(self):
        pass

    def del_er(self):
        pass

    def commit(self):
        pass

    def table_click(self, side):
        if ('right_table' if side=='left' else 'left_table') in self.canvases:
            self.draw_table('right' if side=='left' else 'left')


class MainWindow(tk.Tk):
    def __init__(self):
        self.table_list = {}
        self.connect_list = {}
        
        self.buttons = {}
        self.list_views = {}

        super().__init__()
        self.title('ER図')
        self.geometry(f'{window_width}x{window_height}')

        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height, background='white')
        self.canvas.grid(row=0, column=0, rowspan=3)
        self.canvas.update_idletasks()

        table_list_frame = tk.Frame(self)
        self.list_views['テーブル一覧'] = ttk.Treeview(table_list_frame, show='headings', columns=('name', 'connect_num'), selectmode='browse', height=5)
        self.list_views['テーブル一覧'].bind('<<TreeviewSelect>>', self.view_select)
        self.list_views['テーブル一覧'].heading('name', text='テーブル名', anchor='center')
        self.list_views['テーブル一覧'].heading('connect_num', text='接続数', anchor='center')
        self.list_views['テーブル一覧'].column('name', width=150, anchor='center')
        self.list_views['テーブル一覧'].column('connect_num', width=75, anchor='center')
        self.list_views['テーブル一覧'].grid(row=0,column=0, rowspan=5)

        self.buttons['テーブル登録'] = tk.Button(table_list_frame, text='テーブル登録', command=self.regist_window)
        self.buttons['テーブルコピー'] = tk.Button(table_list_frame, text='テーブルコピー', command=self.copy_table)
        self.buttons['テーブル修正'] = tk.Button(table_list_frame, text='テーブル修正', command=self.edit_window)
        self.buttons['テーブル削除'] = tk.Button(table_list_frame, text='テーブル削除', command=self.delete_table)
        self.buttons['テーブル登録'].grid(row=1, column=1)
        self.buttons['テーブルコピー'].grid(row=2, column=1)
        self.buttons['テーブル修正'].grid(row=3, column=1)
        self.buttons['テーブル削除'].grid(row=4, column=1)
        table_list_frame.grid(row=0, column=1, sticky='nsew')

        table_detail_frame = tk.Frame(self)
        self.list_views['カラム一覧'] = ttk.Treeview(table_detail_frame, show='headings', columns=('name', 'type', 'unique'), selectmode='none', height=10)
        self.list_views['カラム一覧'].heading('name', text='列名', anchor='center')
        self.list_views['カラム一覧'].heading('type', text='型', anchor='center')
        self.list_views['カラム一覧'].heading('unique', text='ユニーク制約', anchor='center')
        self.list_views['カラム一覧'].column('name', width=150, anchor='w')
        self.list_views['カラム一覧'].column('type', width=75, anchor='center')
        self.list_views['カラム一覧'].column('unique', width=75, anchor='center')
        self.list_views['カラム一覧'].grid(row=0,column=0, rowspan=5, sticky='nsew')
        table_detail_frame.grid(row=1, column=1, sticky='nsew')

        connect_list_frame = tk.Frame(self)
        self.buttons['ER追加'] = tk.Button(connect_list_frame, text='ER追加', command=self.regist_er)
        self.buttons['ER修正'] = tk.Button(connect_list_frame, text='ER修正', command=self.regist_er)
        self.buttons['ER削除'] = tk.Button(connect_list_frame, text='ER削除', command=self.delete_er)
        self.buttons['ER追加'].grid(row=0, column=0, sticky='w')
        self.buttons['ER修正'].grid(row=0, column=1, sticky='w')
        self.buttons['ER削除'].grid(row=0, column=2, sticky='w')
        self.canvas_connect_list = tk.Canvas(connect_list_frame, height=400, background='white')
        self.canvas_connect_list.grid(row=1, column=0, columnspan=15)
        self.canvas_connect_list.update_idletasks()
        connect_list_frame.grid(row=2, column=1, sticky='nsew')

        #insert_connection('ターゲット', '店舗マスタ', [['得意先コード', '得意先コード']], [None])
        #insert_connection('ターゲット', '店舗マスタ', [['点数', '冷凍棚数']], [None])
        #self.draw_table_list()

        #entity1 = Entity(self.canvas, Point(40, 80), 'ターゲット')
        #entity2 = Entity(self.canvas, Point(800, 300), '店舗マスタ')
        #Connection(self.canvas, entity1, entity2)
        
        self.draw()
        

    def draw(self):
        self.draw_table_list()
        self.draw_columns_list()
        self.draw_entity()
        self.draw_connection()
        self.draw_connection_list()

    def draw_entity(self):
        tables = get_tables()
        for table in tables:
            if table not in self.table_list:
                self.table_list[table] = Entity(self, self.canvas, Point(random.randint(0, canvas_width), random.randint(0, canvas_height)), table)

    def draw_connection(self):
        tables, keys = get_connection()
        for st, es in tables:
            if f'{st}-{es}' not in self.connect_list:
                color = 'black'
                for key in keys[f'{st}-{es}']:
                    if key[2] is not None:
                        color = 'red'
                        break
                self.connect_list[f'{st}-{es}'] = Connection(self.canvas, self.table_list[st], self.table_list[es], color=color)

    def draw_table_list(self):
        #self.list_views['テーブル一覧'].delete(*self.list_views['テーブル一覧'].get_children())
        table_list = get_tables()
        for i in range(len(table_list)):
            con_table, _ = get_connection(table_list[i])
            if self.list_views['テーブル一覧'].exists(i):
                self.list_views['テーブル一覧'].set(i, 'name', table_list[i])
                self.list_views['テーブル一覧'].set(i, 'connect_num', len(con_table))
            else:
                self.list_views['テーブル一覧'].insert(parent='', index='end', iid=i, values=(table_list[i], len(con_table)))
        if len(table_list) < len(self.list_views['テーブル一覧'].get_children()):
            for i in range(len(self.list_views['テーブル一覧'].get_children())-len(table_list)+1, len(self.list_views['テーブル一覧'].get_children())):
                self.list_views['テーブル一覧'].delete(i)
    
    def draw_columns_list(self):
        self.list_views['カラム一覧'].delete(*self.list_views['カラム一覧'].get_children())
        slct_index = self.list_views['テーブル一覧'].focus()
        if slct_index == '':
            return
        columns = get_table_columns(get_tables()[int(slct_index)])
        for i in range(len(columns)):
            self.list_views['カラム一覧'].insert(parent='', index='end', iid=i, values=(columns[i]))

    def draw_connection_list(self):
        self.canvas_connect_list.delete('all')
        tables, keys = get_connection()
        height_seq = 0
        for st, es in tables:
            ckbttn_id = tk.Radiobutton(self.canvas_connect_list, text='', background='white')
            ckbttn_id.place(x=0, y=height_seq+1)
            ckbttn_id.update_idletasks()

            st_id = Entity(self, self.canvas_connect_list, Point(ckbttn_id.winfo_width(), height_seq+1), st, size=15, is_move=False)
            tmp_id = Entity(self, self.canvas_connect_list, Point(-1, -1), es, size=15, is_move=False)
            es_id = Entity(self, self.canvas_connect_list, Point(self.canvas_connect_list.winfo_width()-tmp_id.width-5, height_seq+1), es, size=15, is_move=False)
            self.canvas_connect_list.delete(tmp_id.id['text'])
            self.canvas_connect_list.delete(tmp_id.id['rectangle'])
            color = 'black'
            for key in keys[f'{st}-{es}']:
                if key[2] is not None:
                    color = 'red'
                    break
            Connection(self.canvas_connect_list, st_id, es_id, color=color)
            tmp_id = Entity(self, self.canvas_connect_list, Point(-1, -1), ' 1-1 ', size=15, is_move=False)
            Entity(self, self.canvas_connect_list, Point((self.canvas_connect_list.winfo_width()-ckbttn_id.winfo_width())//2-tmp_id.width//2+ckbttn_id.winfo_width(), height_seq+1), ' n-1 ', size=15, is_move=False)
            self.canvas_connect_list.delete(tmp_id.id['text'])
            self.canvas_connect_list.delete(tmp_id.id['rectangle'])
            height_seq += st_id.height

            for key in keys[f'{st}-{es}']:
                tmp_id = Entity(self, self.canvas_connect_list, Point(-1, -1), f'-----', size=15, is_move=False)
                con_id = Entity(self, self.canvas_connect_list, Point((self.canvas_connect_list.winfo_width()-ckbttn_id.winfo_width())//2-tmp_id.width//2+ckbttn_id.winfo_width(), height_seq+1), f'-----', size=15, is_move=False)
                self.canvas_connect_list.delete(tmp_id.id['text'])
                self.canvas_connect_list.delete(tmp_id.id['rectangle'])

                tmp_id = Entity(self, self.canvas_connect_list, Point(-1, -1), f' {key[0]}', size=15, is_move=False)
                col_st_id = Entity(self, self.canvas_connect_list, Point(con_id.point.x-tmp_id.width-1, height_seq+1), f' {key[0]}', size=15, is_move=False)
                self.canvas_connect_list.delete(tmp_id.id['text'])
                self.canvas_connect_list.delete(tmp_id.id['rectangle'])

                col_es_id = Entity(self, self.canvas_connect_list, Point(con_id.point.x+con_id.width-1, height_seq+1), f'{key[1]} ', size=15, is_move=False)

                self.canvas_connect_list.delete(con_id.id['text'])
                self.canvas_connect_list.delete(con_id.id['rectangle'])
                Connection(self.canvas_connect_list, col_st_id, col_es_id, color=color, width=2)
                height_seq += col_st_id.height

    def regist_window(self):
        RegistWindow(self)

    def copy_table(self):
        slct_index = self.list_views['テーブル一覧'].focus()
        if slct_index == '':
            return
        table_list = get_tables()
        ori_table_name = table_list[int(slct_index)]
        columns = get_table_columns(ori_table_name)
        table_name = ori_table_name
        num = 1
        while table_name in table_list:
            table_name = f'{ori_table_name}_{num}'
            num += 1
        insert_table(table_name, columns)
        self.draw()

    def edit_window(self):
        slct_index = self.list_views['テーブル一覧'].focus()
        if slct_index == '':
            return
        EditWindow(self, get_tables()[int(slct_index)])

    def delete_table(self):
        slct_index = self.list_views['テーブル一覧'].focus()
        if slct_index == '':
            return
        table_list = get_tables()
        table_name = table_list[int(slct_index)]
        delete_table(table_name)

        self.canvas.delete(self.table_list[table_name].id['text'])
        self.canvas.delete(self.table_list[table_name].id['rectangle'])
        del self.table_list[table_list[int(slct_index)]]

        delete_con_keys = []
        for k in self.connect_list:
            if f'{table_name}-' in k or f'-{table_name}' in k:
                delete_con_keys.append(k)
        for k in delete_con_keys:
            self.canvas.delete(self.connect_list[k].id)
            del self.connect_list[k]

        self.draw()

    def view_select(self, event):
        self.draw_columns_list()

    def regist_er(self):
        RegistERWindow(self)

    def delete_er(self):
        pass

def init_table():
    if not os.path.exists('table.db'):
        conn = sqlite3.connect('table.db')
        cur = conn.cursor()

        sql = """CREATE TABLE table_list (
        table_no INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL
        )"""
        cur.execute(sql)

        sql = """CREATE TABLE table_columns (
        table_no INTEGER NOT NULL,
        column_no INTEGER NOT NULL,
        column TEXT NOT NULL,
        type TEXT,
        unique_flag TEXT
        )"""
        cur.execute(sql)
    
        sql = """CREATE TABLE table_connection (
        start_table_no INTEGER NOT NULL,
        end_table_no INTEGER NOT NULL,
        start_column_no INTEGER NOT NULL,
        end_column_no INTEGER NOT NULL,
        timeER TEXT,
        start_cardinality TEXT,
        end_cardinality TEXT
        )"""
        cur.execute(sql)

        conn.commit()
        conn.close()

def insert_table(table_name, columns):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """INSERT INTO table_list (table_name) VALUES (?)"""
    cur.execute(sql, [table_name])
    conn.commit()

    for i, col in enumerate(columns):
        sql = """INSERT INTO table_columns (table_no,column_no,column) VALUES (?, ?, ?)"""
        cur.execute(sql, (get_table_no(table_name), i, col))
    conn.commit()
    conn.close()

def insert_connection(start_table, end_table, connection_columns, timeERs):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    for i, (start_col, end_col) in enumerate(connection_columns):
        if timeERs[i] is None:
            sql = """INSERT INTO table_connection (start_table_no, end_table_no, start_column_no, end_column_no) VALUES (?, ?, ?, ?)"""
            cur.execute(sql, [get_table_no(start_table), get_table_no(end_table), get_column_no(start_table, start_col), get_column_no(end_table, end_col)])
        else:
            sql = """INSERT INTO table_connection (start_table_no, end_table_no, start_column_no, end_column_no, timeER) VALUES (?, ?, ?, ?, ?)"""
            cur.execute(sql, [get_table_no(start_table), get_table_no(end_table), get_column_no(start_table, start_col), get_column_no(end_table, end_col), timeERs[i]])

    conn.commit()
    conn.close()

def update_table(old_table_name, new_table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """UPDATE table_list SET table_name=? WHERE table_name=?"""
    cur.execute(sql, [new_table_name, old_table_name])

    conn.commit()
    conn.close()

def update_columns(table_name, columns):
    old_columns = get_table_columns(table_name)

    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    for old_col, new_col in zip(old_columns, columns):
        sql = """UPDATE table_columns SET column=? WHERE table_no=? and column=?"""
        cur.execute(sql, [new_col, get_table_no(table_name), old_col])
    
    for i, col in enumerate(columns):
        if len(old_columns) > i:
            continue
        sql = """INSERT INTO table_columns (table_no,column_no,column) VALUES (?, ?, ?)"""
        cur.execute(sql, (get_table_no(table_name), i, col))

    conn.commit()
    conn.close()

def delete_table(table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    sql = """DELETE FROM table_list WHERE table_name=?"""
    cur.execute(sql, [table_name])

    sql = """DELETE FROM table_columns WHERE table_no=?"""
    cur.execute(sql, [get_table_no(table_name)])

    sql = """DELETE FROM table_connection WHERE start_table_no=?"""
    cur.execute(sql, [get_table_no(table_name)])
    sql = """DELETE FROM table_connection WHERE end_table_no=?"""
    cur.execute(sql, [get_table_no(table_name)])

    conn.commit()
    conn.close()

def get_column_no(table_name, column):
    ret = None
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT column_no FROM table_columns WHERE table_no=? and column=?'
    cur.execute(sql, [get_table_no(table_name), column])
    for value in cur.fetchall():
        ret = int(value[0])
    conn.close()
    return ret

def get_table_no(table_name):
    ret = None
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT table_no FROM table_list WHERE table_name=?'
    cur.execute(sql, [table_name])
    for value in cur.fetchall():
        ret = int(value[0])
    conn.close()
    return ret

def get_table_name(table_no):
    ret = None
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT table_name FROM table_list WHERE table_no=?'
    cur.execute(sql, [table_no])
    for value in cur.fetchall():
        ret = value[0]
    conn.close()
    return ret

def get_column_name(table_name, column_no):
    ret = None
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT column FROM table_columns WHERE table_no=? and column_no=?'
    cur.execute(sql, [get_table_no(table_name), column_no])
    for value in cur.fetchall():
        ret = value[0]
    conn.close()
    return ret

def get_tables():
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT * FROM table_list'
    cur.execute(sql)
    table_list = []
    for value in cur.fetchall():
        table_list.append(value[1])
    conn.close()
    return table_list

def get_table_columns(table_name):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()
    sql = 'SELECT column FROM table_columns WHERE table_no=?'
    cur.execute(sql, [get_table_no(table_name)])
    table_columns = []
    for col in cur.fetchall():
        table_columns.append(col[0])
    conn.close()
    return table_columns

def get_connection(start_table=None, end_table=None):
    conn = sqlite3.connect('table.db')
    cur = conn.cursor()

    tables = []
    keys = {}

    if start_table is None:
        sql = 'SELECT * FROM table_connection'
        cur.execute(sql)
        for col in cur.fetchall():
            start_table = get_table_name(col[0])
            end_table = get_table_name(col[1])
            con_key = f'{start_table}-{end_table}'
            start_column = get_column_name(start_table, col[2])
            end_column = get_column_name(end_table, col[3])

            tables.append([start_table, end_table])
            if con_key in keys:
                keys[con_key].append([start_column, end_column, col[4]])
            else:
                keys[con_key] = [[start_column, end_column, col[4]]]
    elif end_table is None:
        sql = 'SELECT * FROM table_connection WHERE start_table_no=?'
        cur.execute(sql, [get_table_no(start_table)])
        for col in cur.fetchall():
            end_table = get_table_name(col[1])
            con_key = f'{start_table}-{end_table}'
            start_column = get_column_name(start_table, col[2])
            end_column = get_column_name(end_table, col[3])

            tables.append([start_table, end_table])
            if con_key in keys:
                keys[con_key].append([start_column, end_column, col[4]])
            else:
                keys[con_key] = [[start_column, end_column, col[4]]]
        sql = 'SELECT * FROM table_connection WHERE end_table_no=?'
        cur.execute(sql, [get_table_no(start_table)])
        for col in cur.fetchall():
            end_table = get_table_name(col[0])
            con_key = f'{start_table}-{end_table}'
            start_column = get_column_name(end_table, col[3])
            end_column = get_column_name(start_table, col[2])

            tables.append([start_table, end_table])
            if con_key in keys:
                keys[con_key].append([start_column, end_column, col[4]])
            else:
                keys[con_key] = [[start_column, end_column, col[4]]]
    else:
        sql = 'SELECT * FROM table_connection WHERE start_table_no=? and end_table_no=?'
        cur.execute(sql, [start_table, end_table])
        for col in cur.fetchall():
            con_key = f'{start_table}-{end_table}'
            start_column = get_column_name(start_table, col[2])
            end_column = get_column_name(end_table, col[3])

            tables.append([start_table, end_table])
            if con_key in keys:
                keys[con_key].append([start_column, end_column, col[4]])
            else:
                keys[con_key] = [[start_column, end_column, col[4]]]
        sql = 'SELECT * FROM table_connection WHERE start_table=? and end_table=?'
        cur.execute(sql, [end_table, start_table])
        for col in cur.fetchall():
            con_key = f'{start_table}-{end_table}'
            start_column = get_column_name(end_table, col[3])
            end_column = get_column_name(start_table, col[2])

            tables.append([start_table, end_table])
            if con_key in keys:
                keys[con_key].append([start_column, end_column, col[4]])
            else:
                keys[con_key] = [[start_column, end_column, col[4]]]
    conn.close()
    return tables, keys


def main():
    init_table()
    main_window = MainWindow()
    main_window.mainloop()

if __name__ == '__main__':
    main()
