from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

import os
import shutil

from tkinter import font as tkFont

from polish import to_reverse_polish, str_polish
from rows import RowWithEntrys, RowWithLabels, EmptyRow, RowWithImage
from scrollable_canvas import add_scrollable_canvas


def check_float(s, accept_none=True):
    try:
        if s.lower() == 'none':
            return accept_none
        float(s)
        return len(s) < 12
    except ValueError:
        return False


def check_positive(s):
    try:
        return int(s) >= 0
    except ValueError:
        return False


class InfoCreator:
    FONT = None

    def __init__(self, name, clas, game):
        self.name = name
        self.clas = clas
        self.game = game
        self.next_id = 0

    def create(self, *args):
        info = self.clas(self.game, self.FONT, *args)

        info.cur_id = self.name + str(self.next_id)
        self.next_id += 1

        info.name = self.name

        return info


class Game:
    sep = '#'
    enter = '{'

    MAXINT = '999999'

    def clear_initialize(self):
        self.info_creators = dict({'p': InfoCreator('p', RowWithEntrys, self),
                                   't': InfoCreator('t', RowWithEntrys, self),
                                   'r': InfoCreator('r', RowWithEntrys, self),
                                   're': InfoCreator('re', RowWithLabels, self),
                                   'an': InfoCreator('an', RowWithEntrys, self)})

        self.cur_infos = dict({'p': dict(),
                               't': dict(),
                               'r': dict(),
                               're': dict(),
                               'an': dict(),
                               't_': dict(),
                               'r_': dict(),
                               'p_': dict(),
                               'empty': [EmptyRow()]
                               })

        self.empty_info = ('empty', 0)
        self.cur_info = self.empty_info

        self.cur_tab = 't'
        self.cur_role = 'r'
        self.cur_param = 'p'

        self.edit_frame = EmptyRow()
        self.edit_id = None
        self.edit_name = None

        self.reaction_id = None
        self.refunction_id = None

        self.win_cond = ''
        self.loose_cond = ''
        self.name = ''

        self.func_list = dict()

        self.last_dirname = '/'

        self.is_fullscreen = True

    def __init__(self):
        self.clear_initialize()

        self.root = Tk()

        self.myFont = tkFont.Font(family="Comic Sans MS", size=10)
        self.myFontBold = tkFont.Font(family="Comic Sans MS", size=10, weight='bold')
        InfoCreator.FONT = self.myFont

        self.root.title("Main menu")
        self.root.geometry("300x300+0+100")

        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True)

        self.btn_start = Button(self.main_frame, text='Создать сценарий', font=self.myFont,
                                command=self.begin).pack(pady=(10, 80))
        self.btn_continue = Button(self.main_frame, text='Редактировать сценарий', font=self.myFont,
                                   command=self.cont).pack(pady=(0, 10))

        self.last_param_thresh = Frame()
        self.last_tab_thresh = Frame()
        self.last_role_thresh = Frame()

    def start(self):
        self.root.mainloop()

    def to_label(self):
        row = self.cur_infos[self.cur_info[0]][self.cur_info[1]]
        if hasattr(row, 'has_entry'):
            row.to_label(row.has_entry)

    def restore_canvas(self, canvas, frame):
        canvas.yview_scroll(-10 * (frame.winfo_height() //
                                   canvas.winfo_height()), "units")

        canvas.thresh.destroy()
        canvas.thresh = Frame(frame, height=1)
        canvas.thresh.pack()

    def click_on_item(self, name, cur_id):
        self.to_label()

        if (name, cur_id) == self.cur_info:
            return

        row = self.cur_infos[self.cur_info[0]][self.cur_info[1]]
        row.turn_off()

        if name == 't':
            for i in self.cur_infos[self.cur_tab + '_'].values():
                i.pack_forget()
            self.cur_tab = cur_id

            self.restore_canvas(self.lists_canvas, self.lists_scroll_frame)

        if name == 'r':
            for i in self.cur_infos[self.cur_role + '_'].values():
                i.pack_forget()
            self.cur_role = cur_id

            self.restore_canvas(self.actions_canvas, self.actions_scroll_frame)

        if name == 'p':
            for i in self.cur_infos[self.cur_param + '_'].values():
                i.pack_forget()

            self.cur_param = cur_id
            self.restore_canvas(self.functions_canvas, self.functions_scroll_frame)

        self.cur_info = (name, cur_id)
        self.cur_infos[name][cur_id].turn_on()

    def destroy_edit_frame(self):
        self.edit_frame.destroy()
        self.edit_frame = EmptyRow()
        self.edit_id = None
        self.edit_name = None

        self.reaction_id = None
        self.refunction_id = None

        self.cur_infos['re'] = dict()
        if self.cur_info[0] == 're':
            self.cur_info = self.empty_info

        self.cur_infos['an'] = dict()
        if self.cur_info[0] == 'an':
            self.cur_info = self.empty_info

    def add_parameters(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        Label(frame, text='Переменные', font=self.myFontBold).grid(row=0, column=0)
        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        def add_param(frame):
            self.to_label()
            import random
            visibility = random.choice([1, 0])
            self.show_param(frame, 'Деньги', visibility, '100', '0', 'None')

        canvas, scroll_frame = add_scrollable_canvas(params_frame)
        self.param_scroll = scroll_frame
        Button(frame, text='Добавить переменную', font=self.myFont,
               command=lambda: add_param(scroll_frame)).grid(row=0, column=1)

    def show_param(self, frame, name, visibility, *values, force_id=None):
        creator = self.info_creators['p']
        if force_id:
            creator.next_id = force_id
        row = creator.create(name, *values)
        row.show(frame)

        row.items[4].func = lambda x: check_float(x, False)
        for label in row.items[6::2]:
            label.func = check_float

        row.add_id()
        row.change_visibility(visibility)
        row.bind('<Button-1>', lambda e: self.click_on_item(creator.name, row.cur_id))
        row.bind('<Button-1>', lambda e: self.add_functions(name, row.cur_id), add=True)
        row.add_func = self.add_functions

        self.cur_infos[creator.name][row.cur_id] = row

        self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithLabels, self)
        self.cur_infos[f'{row.cur_id}_'] = dict()

        self.func_list[f'{row.cur_id}_'] = []

    def maket_functions(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.functions_label = Label(frame, text='Нет переменной', font=self.myFontBold, anchor='w')
        self.functions_label.grid(row=0, column=0)

        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        self.functions_params_frame = params_frame

        self.functions_canvas, self.functions_scroll_frame = add_scrollable_canvas(self.functions_params_frame)
        self.functions_canvas.thresh = Frame()

        self.functions_btn = Button(frame, text='Добавить функцию', state='disabled', font=self.myFont)
        self.functions_btn.grid(row=0, column=1)

    def add_functions(self, param_name, param_id):
        self.functions_label['text'] = f'Функции {param_name}'

        self.functions_btn.configure(command=lambda: self.add_function(self.functions_scroll_frame, param_id))
        self.functions_btn['state'] = 'normal'

        for func_id in self.func_list[param_id + '_']:
            self.cur_infos[f'{param_id}_'][func_id].pack_again()

    def add_function(self, frame, param_id, edit=False):
        self.to_label()
        self.destroy_edit_frame()

        edit_frame = Frame(self.main_frame)
        edit_frame.pack_propagate(0)
        edit_frame.grid_propagate(0)
        edit_frame.grid(row=0, column=3, rowspan=3, sticky="nsew")
        self.edit_frame = edit_frame
        self.edit_name = param_id

        Label(edit_frame, text='Функция', font=self.myFont).pack()
        function = ScrolledText(edit_frame, height=7, font=self.myFont)
        function.pack()

        Label(edit_frame, text='Условие на функцию', font=self.myFont).pack()
        condition = ScrolledText(edit_frame, height=7, font=self.myFont)
        condition.pack()

        if edit:
            row = self.function_row

            function.insert('1.0', row.function)
            condition.insert('1.0', row.cond)

            self.edit_id = row.cur_id

        btn = Button(edit_frame, text='Добавить функцию' if not edit else 'Редактировать функцию', font=self.myFont)

        def check_correct(btn, param_id, frame, func, cond, edit):
            if to_reverse_polish(func[:-1], self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в описании функции')
                # btn.config(relief=RAISED)
            elif to_reverse_polish(cond[:-1], self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в условии функции')
            else:
                self.show_function(frame, param_id,
                                   func, cond,
                                   edit)
                self.destroy_edit_frame()

        btn.bind('<Button-1>', lambda e: check_correct(btn, param_id, frame,
                                                       function.get('1.0', 'end'), condition.get('1.0', 'end'),
                                                       edit))
        btn.pack()

    def show_function(self, frame, param_id,
                      function, condition,
                      edit=False,
                      force_id=None):
        self.to_label()

        creator = self.info_creators[f'{param_id}_']

        if edit:
            row = self.function_row
            row.items[2]['text'] = function.split('\n')[0]
        else:
            if force_id:
                creator.next_id = force_id
            row = creator.create(function.split('\n')[0])
            row.show(frame)
            self.func_list[param_id + '_'].append(row.cur_id)

        row.function = function[:-1]
        row.cond = condition[:-1]

        if edit:
            return

        def double_click(row):
            self.function_row = row
            self.add_function(self.functions_scroll_frame, row.cur_id.split('_')[0], True)

        row.bind('<Double-Button-1>', lambda e: double_click(row))
        row.add_id(85)
        row.items[-1].bind('<Double-Button-1>', lambda e: double_click(row))
        row.items[-2].bind('<Double-Button-1>', lambda e: double_click(row))
        row.bind('<Button-1>', lambda e: self.click_on_item(f'{param_id}_', row.cur_id))

        self.cur_infos[f'{param_id}_'][row.cur_id] = row

        if param_id != self.cur_param:
            row.pack_forget()

    def add_tabs(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        Label(frame, text='Вкладки', font=self.myFontBold).grid(row=0, column=0)
        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        def add_tab(frame):
            self.to_label()
            import random
            visibility = random.choice([1, 0])
            self.show_tab(frame, 'Название', visibility)

        canvas, scroll_frame = add_scrollable_canvas(params_frame)
        self.tab_scroll = scroll_frame
        Button(frame, text='Добавить вкладку', font=self.myFont,
               command=lambda: add_tab(scroll_frame)).grid(row=0, column=1)

    def show_tab(self, frame, name, visibility, force_id=None):
        creator = self.info_creators['t']
        if force_id:
            creator.next_id = force_id
        row = creator.create(name)
        row.show(frame)
        row.add_id()
        row.change_visibility(visibility)

        row.bind('<Button-1>', lambda e: self.click_on_item(creator.name, row.cur_id))
        row.bind('<Button-1>', lambda e: self.add_lists(name, row.cur_id), add=True)
        row.add_func = self.add_lists

        self.cur_infos[creator.name][row.cur_id] = row

        self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithImage, self)
        self.cur_infos[f'{row.cur_id}_'] = dict()

    def maket_lists(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.lists_label = Label(frame, text='Нет вкладки', font=self.myFontBold, anchor='w')
        self.lists_label.grid(row=0, column=0)

        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        self.lists_params_frame = params_frame

        self.lists_canvas, self.lists_scroll_frame = add_scrollable_canvas(self.lists_params_frame)
        self.lists_canvas.thresh = Frame()

        self.lists_btn = Button(frame, text='Добавить лист', state='disabled', font=self.myFont)
        self.lists_btn.grid(row=0, column=1)

    def add_lists(self, tab_name, tab_id):
        self.lists_label['text'] = f'Листы {tab_name}'

        self.lists_btn.configure(command=lambda: self.add_list(self.lists_scroll_frame, tab_id))
        self.lists_btn['state'] = 'normal'

        for i in self.cur_infos[f'{tab_id}_'].values():
            i.pack_again()

    def add_list(self, frame, tab_id, visibility=0, filename=None, force_id=None):
        self.to_label()
        if filename is None:
            filename = filedialog.askopenfilename(initialdir=self.last_dirname,
                                                  title='Выберите изображение',
                                                  filetypes=(("all files", "*.*"),)
                                                  )
            if filename == '':
                return
            self.last_dirname = os.path.dirname(os.path.realpath(filename))

        if filename is None:
            filename = 'C:/Users/o.verbin/Downloads/Illidan.png'
        try:
            default_img = Image.open(filename)
        except:
            messagebox.showerror('Ошибка', 'Изображение не удаётся открыть')
            return

        w, h = default_img.size
        k = min(320 / w, 180 / h)

        img = default_img.resize((int(w * k), int(h * k)))
        img = ImageTk.PhotoImage(img)

        creator = self.info_creators[f'{tab_id}_']
        if force_id:
            creator.next_id = force_id
        row = creator.create(img, default_img, filename)
        row.show(frame)
        row.add_id()
        row.change_visibility(visibility)
        row.bind('<Button-1>', lambda e: self.click_on_item(f'{tab_id}_', row.cur_id))

        self.cur_infos[f'{tab_id}_'][row.cur_id] = row

        if tab_id != self.cur_tab:
            row.pack_forget()

    def add_roles(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        Label(frame, text='Роли', font=self.myFontBold).grid(row=0, column=0)
        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        canvas, scroll_frame = add_scrollable_canvas(params_frame)
        self.role_scroll = scroll_frame
        Button(frame, text='Добавить роль', font=self.myFont,
               command=lambda: self.add_role(scroll_frame)).grid(row=0, column=1)

    def add_role(self, frame, role_id=None):
        self.to_label()
        self.destroy_edit_frame()

        edit_frame = Frame(self.main_frame)
        edit_frame.pack_propagate(0)
        edit_frame.grid_propagate(0)
        edit_frame.grid(row=0, column=3, rowspan=3, sticky="nsew")
        self.edit_frame = edit_frame
        self.edit_name = role_id

        Label(edit_frame, text='Название роли', font=self.myFont).pack()
        name = Entry(edit_frame, font=self.myFont)
        name.pack()

        Label(edit_frame, text='Описание роли', font=self.myFont).pack()
        descr = ScrolledText(edit_frame, height=7, font=self.myFont)
        descr.pack()

        if role_id:
            row = self.cur_infos['r'][role_id]

            name.insert(0, row.items[2]['text'])
            descr.insert('1.0', row.descr)

            self.edit_id = row.cur_id

        btn = Button(edit_frame, text='Добавить роль' if not role_id else 'Редактировать роль', font=self.myFont)

        btn.bind('<Button-1>', lambda e: self.show_role(frame,
                                                        name.get(),
                                                        descr.get('1.0', 'end'),
                                                        role_id))
        btn.bind('<Button-1>', lambda e: self.destroy_edit_frame(), add=True)
        btn.pack()

    def show_role(self, frame, name, descr, role_id=None, force_id=None):
        if role_id:
            row = self.cur_infos['r'][role_id]
            row.items[2]['text'] = name
            row.descr = descr[:-1]
        else:
            creator = self.info_creators['r']
            if force_id:
                creator.next_id = force_id
            row = creator.create(name)
            row.descr = descr[:-1]
            row.show(frame)
            row.add_id()
            row.bind('<Button-1>', lambda e: self.click_on_item(creator.name, row.cur_id))
            row.bind('<Button-1>', lambda e: self.add_actions(name, row.cur_id), add=True)
            row.add_func = self.add_actions

            row.bind('<Double-Button-1>', lambda e: self.add_role(frame, row.cur_id))

            self.cur_infos[creator.name][row.cur_id] = row

            self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithEntrys, self)
            self.cur_infos[f'{row.cur_id}_'] = dict()

    def maket_actions(self, frame):
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.actions_label = Label(frame, text='Нет роли', font=self.myFontBold, anchor='w')
        self.actions_label.grid(row=0, column=0)

        params_frame = Frame(frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        self.actions_params_frame = params_frame

        self.actions_canvas, self.actions_scroll_frame = add_scrollable_canvas(self.actions_params_frame)
        self.actions_canvas.thresh = Frame()

        self.actions_btn = Button(frame, text='Добавить действие', state='disabled', font=self.myFont)
        self.actions_btn.grid(row=0, column=1)

    def add_actions(self, role_name, role_id):
        self.actions_label['text'] = f'Действия {role_name}'

        self.actions_btn.configure(command=lambda: self.add_action(self.actions_scroll_frame, role_id))
        self.actions_btn['state'] = 'normal'

        for i in self.cur_infos[f'{role_id}_'].values():
            i.pack_again()

    def add_action(self, frame, role_id, edit=False):
        self.to_label()
        self.destroy_edit_frame()

        edit_frame = Frame(self.main_frame)
        edit_frame.pack_propagate(0)
        edit_frame.grid_propagate(0)
        edit_frame.grid(row=0, column=3, rowspan=3, sticky="nsew")
        self.edit_frame = edit_frame
        self.edit_name = role_id

        Label(edit_frame, text='Описание действия', font=self.myFont).pack()
        description = ScrolledText(edit_frame, height=3, font=self.myFont)
        description.pack()

        Label(edit_frame, text='Условие на действие', font=self.myFont).pack()
        requirement = ScrolledText(edit_frame, height=3, font=self.myFont)
        requirement.pack()

        tmp_frame = Frame(edit_frame)
        Label(tmp_frame, text='Варианты ответа:', font=self.myFont).pack(fill='x', expand=True, side='left')
        ans_button = Button(tmp_frame, text='Добавить ответ', font=self.myFont)
        ans_button.pack(side='right')
        tmp_frame.pack(fill='x')

        ans_frame = Frame(edit_frame)
        ans_frame.pack_propagate(0)
        ans_frame.pack(fill='both', expand=True)

        canvas, scroll_frame = add_scrollable_canvas(ans_frame)
        self.ans_scroll_frame = scroll_frame

        self.info_creators['an'] = InfoCreator('an', RowWithEntrys, self)

        def add_ans(ans_text='Ответ', ans_id=None):
            self.to_label()

            creator = self.info_creators['an']
            if ans_id is not None:
                creator.next_id = ans_id
            row = creator.create(ans_text)

            row.show(self.ans_scroll_frame)
            row.add_id()
            row.bind('<Button-1>', lambda e: self.click_on_item(creator.name, row.cur_id))

            self.cur_infos[creator.name][row.cur_id] = row

        ans_button.bind('<Button-1>', lambda e: add_ans())

        Label(edit_frame, text='Реакция', font=self.myFont).pack()
        action = ScrolledText(edit_frame, height=4, font=self.myFont)
        action.pack()

        Label(edit_frame, text='Условие на реакцию', font=self.myFont).pack()
        condition = ScrolledText(edit_frame, height=4, font=self.myFont)
        condition.pack()

        btn_action = Button(edit_frame, text='Добавить реакцию', font=self.myFont)
        btn_action.pack()

        action_frame = Frame(edit_frame)
        action_frame.pack(fill='both', expand=True)

        action_frame.grid_rowconfigure(1, weight=1)
        action_frame.grid_columnconfigure(0, weight=1)

        Label(action_frame, text='Реакции', font=self.myFont).grid(row=0, column=0)

        params_frame = Frame(action_frame)
        params_frame.pack_propagate(0)
        params_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)

        canvas, scroll_frame = add_scrollable_canvas(params_frame)

        self.info_creators['re'] = InfoCreator('re', RowWithLabels, self)

        def add_reaction(row=None):
            self.to_label()
            action_text = self.reaction_action.get('1.0', 'end')
            self.reaction_action.delete('1.0', 'end')

            condition_text = self.reaction_condition.get('1.0', 'end')
            self.reaction_condition.delete('1.0', 'end')

            if row is not None:
                row.items[2]['text'] = action_text.split('\n')[0]
                row.items[4]['text'] = condition_text.split('\n')[0]

                row.action = action_text
                row.condition = condition_text

                self.reaction_btn.configure(text='Добавить реакцию')
                self.reaction_btn.bind('<Button-1>', lambda e: add_reaction(None))

                self.reaction_id = None
            else:
                creator = self.info_creators['re']
                row = creator.create(action_text.split('\n')[0], condition_text.split('\n')[0])
                row.action = action_text
                row.condition = condition_text

                row.show(self.reaction_scroll_frame)
                row.bind('<Button-1>', lambda e: self.click_on_item(creator.name, row.cur_id))

                row.bind('<Double-Button-1>', lambda e: edit_reaction(row))

                self.cur_infos[creator.name][row.cur_id] = row

        def edit_reaction(row):
            self.to_label()
            self.reaction_action.delete('1.0', 'end')
            self.reaction_action.insert('1.0', row.action[:-1])

            self.reaction_condition.delete('1.0', 'end')
            self.reaction_condition.insert('1.0', row.condition[:-1])

            self.reaction_btn.configure(text='Редактировать реакцию')
            self.reaction_btn.bind('<Button-1>', lambda e: add_reaction(row))

            self.reaction_id = row.cur_id

        btn_action.bind('<Button-1>', lambda e: add_reaction(None))

        self.reaction_btn = btn_action
        self.reaction_action = action
        self.reaction_condition = condition
        self.reaction_scroll_frame = scroll_frame
        self.reaction_func = add_reaction

        if edit:
            row = self.action_row

            description.insert('1.0', row.desc)
            requirement.insert('1.0', row.req)

            for action_text, cond_text in zip(row.action, row.cond):
                action.insert('1.0', action_text)
                condition.insert('1.0', cond_text)
                add_reaction(None)
                action.delete('1.0', 'end')
                condition.delete('1.0', 'end')

            for ans_text, ans_id in zip(row.ans, row.ans_id):
                add_ans(ans_text, int(ans_id[2:]))

            self.edit_id = row.cur_id

        btn = Button(edit_frame, text='Добавить действие' if not edit else 'Редактировать действие', font=self.myFont)

        def check_correct(role_id, frame, description, requirement, edit):
            if to_reverse_polish(requirement.get('1.0', 'end')[:-1], self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в условии')
            elif to_reverse_polish('\n'.join([x.action[:-1]
                                              for x in self.cur_infos['re'].values()]), self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в описании действия')
            elif to_reverse_polish('\n'.join([x.condition[:-1]
                                              for x in self.cur_infos['re'].values()]), self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в условии на действие')
            else:
                self.show_action(frame, role_id,
                                 description.get('1.0', 'end'),
                                 requirement.get('1.0', 'end'),
                                 edit
                                 )
                self.destroy_edit_frame()

        btn.bind('<Button-1>', lambda e: check_correct(role_id, frame,
                                                       description,
                                                       requirement,
                                                       edit
                                                       ))
        btn.pack()

    def show_action(self, frame, role_id,
                    description,
                    requirement,
                    edit=False,
                    force_id=None):
        self.to_label()

        creator = self.info_creators[f'{role_id}_']

        desc = description

        if edit:
            row = self.action_row
            row.items[2]['text'] = desc.split('\n')[0]
        else:
            if force_id:
                creator.next_id = force_id
            row = creator.create(desc.split('\n')[0])
            row.add_func = lambda *args: None
            row.show(frame)

        row.desc = desc[:-1]
        row.req = requirement[:-1]
        row.action = [x.action[:-1]
                      for x in self.cur_infos['re'].values()]
        row.cond = [x.condition[:-1]
                    for x in self.cur_infos['re'].values()]
        row.ans = [x.items[2]['text'].replace(',', '')
                   for x in self.cur_infos['an'].values()]
        row.ans_id = [x.cur_id
                      for x in self.cur_infos['an'].values()]

        l = [*map(lambda x: int(x[2:]), row.ans_id)]
        assert (l == sorted(l))  # Отсортированы python>3.7

        if edit:
            return

        def double_click(row):
            self.action_row = row
            self.add_action(self.actions_scroll_frame, row.cur_id.split('_')[0], True)

        row.bind('<Double-Button-1>', lambda e: double_click(row))

        frame = Frame(row.items[0], width=70)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(0)

        l = Label(frame, text='0', font=self.myFont)
        l.pack(anchor='w')
        l.func = check_positive

        l.bind('<Double-Button-1>', lambda e: row.to_entry(4))
        frame.bind('<Double-Button-1>', lambda e: row.to_entry(4))

        row.items.append(frame)
        row.items.append(l)

        row.turn_off()

        row.add_id(100)
        row.items[-1].bind('<Double-Button-1>', lambda e: double_click(row))
        row.items[-2].bind('<Double-Button-1>', lambda e: double_click(row))
        row.bind('<Button-1>', lambda e: self.click_on_item(f'{role_id}_', row.cur_id))

        self.cur_infos[f'{role_id}_'][row.cur_id] = row

        if role_id != self.cur_role:
            row.pack_forget()

    def add_additional(self, frame):
        btn_save = Button(frame, text='Сохранить сценарий', command=self.save_game, font=self.myFont)
        btn_save.pack(pady=(5, 0))

        btn_win = Button(frame, text='Условие для победы', command=self.add_cond, font=self.myFont)
        btn_win.pack(pady=(5, 0))

    def add_cond(self):
        self.to_label()
        self.destroy_edit_frame()

        edit_frame = Frame(self.main_frame)
        edit_frame.pack_propagate(0)
        edit_frame.grid_propagate(0)
        edit_frame.grid(row=0, column=3, rowspan=3, sticky="nsew")
        self.edit_frame = edit_frame
        self.edit_name = None

        Label(edit_frame, text='Название сценария', font=self.myFont).pack()
        name = ScrolledText(edit_frame, height=3, font=self.myFont)
        name.insert('1.0', self.name)
        name.pack()

        Label(edit_frame, text='Условие на победу', font=self.myFont).pack()
        win = ScrolledText(edit_frame, height=5, font=self.myFont)
        win.insert('1.0', self.win_cond)
        win.pack()

        Label(edit_frame, text='Условие на проигрыш', font=self.myFont).pack()
        loose = ScrolledText(edit_frame, height=4, font=self.myFont)
        loose.insert('1.0', self.loose_cond)
        loose.pack()

        def save_cond():
            self.name = name.get('1.0', 'end')[:-1]
            self.win_cond = win.get('1.0', 'end')[:-1]
            self.loose_cond = loose.get('1.0', 'end')[:-1]

            self.to_label()

            if to_reverse_polish(self.loose_cond, self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в условии на проигрышь')
            elif to_reverse_polish(self.win_cond, self) is None:
                messagebox.showerror('Ошибка', 'Ошибка в условии на победу')
            else:
                self.destroy_edit_frame()

        btn = Button(edit_frame, text='Сохранить условия', command=save_cond, font=self.myFont)
        btn.pack()

    def begin(self, filename=None):
        self.main_frame.destroy()
        # self.root.overrideredirect(True)
        # self.root.geometry("{0}x{1}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.geometry("1000x500+250+100")

        self.root.attributes("-fullscreen", True)

        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        self.main_frame.grid_rowconfigure(0, weight=2)
        self.main_frame.grid_rowconfigure(1, weight=6)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(3, weight=1)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=0, column=0, sticky="nsew")

        self.add_parameters(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=1, column=0, sticky="nsew")

        self.maket_functions(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=0, column=1, sticky="nsew")

        self.add_tabs(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=1, column=1, sticky="nsew")

        self.maket_lists(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=0, column=2, sticky="nsew")

        self.add_roles(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=1, column=2, sticky="nsew")

        self.maket_actions(frame)

        frame = Frame(self.main_frame)
        frame.pack_propagate(0)
        frame.grid_propagate(0)
        frame.grid(row=2, column=0, columnspan=3, sticky="nsew")

        self.add_additional(frame)

        self.define_collbacks()

        if filename:
            try:
                self.restore(filename)
            except:
                self.root.destroy()
        else:
            self.initial_values()

    def create_host(self, name, descr):
        creator = self.info_creators['r']
        self.show_role(self.role_scroll, name, descr, force_id=0)
        row = self.cur_infos['r']['r0']
        del self.info_creators[f'{row.cur_id}_']
        del self.cur_infos[f'{row.cur_id}_']
        del self.cur_infos[creator.name][row.cur_id]
        creator.next_id = 0
        row.cur_id = 'rhost'
        row.items[-1]['text'] = row.cur_id

        self.cur_infos[creator.name][row.cur_id] = row
        self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithEntrys, self)
        self.cur_infos[f'{row.cur_id}_'] = dict()

    def create_leader(self, name, descr):
        creator = self.info_creators['r']
        self.show_role(self.role_scroll, name, descr, force_id=0)
        row = self.cur_infos['r']['r0']
        del self.info_creators[f'{row.cur_id}_']
        del self.cur_infos[f'{row.cur_id}_']
        del self.cur_infos[creator.name][row.cur_id]
        creator.next_id = 0
        row.cur_id = 'rleader'
        row.items[-1]['text'] = row.cur_id

        self.cur_infos[creator.name][row.cur_id] = row
        self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithEntrys, self)
        self.cur_infos[f'{row.cur_id}_'] = dict()

    def create_time(self, value, min_value, max_value):
        creator = self.info_creators['p']
        self.show_param(self.param_scroll, 'Номер раунда', 1, value, min_value, max_value, force_id=0)
        row = self.cur_infos['p']['p0']

        del self.cur_infos[creator.name][row.cur_id]
        del self.info_creators[f'{row.cur_id}_']
        del self.cur_infos[f'{row.cur_id}_']
        del self.func_list[f'{row.cur_id}_']
        creator.next_id = 0

        row.cur_id = 'ptime'

        row.items[-1]['text'] = row.cur_id

        def check_positive(s, accept_none=True):
            if s.lower() == 'none':
                return accept_none
            try:
                i = int(s)
                return len(s) < 12 and i >= 0
            except:
                return False

        row.items[4].func = lambda x: check_positive(x, False)
        row.items[8].func = check_positive

        self.cur_infos[creator.name][row.cur_id] = row
        self.info_creators[f'{row.cur_id}_'] = InfoCreator(f'{row.cur_id}_', RowWithLabels, self)
        self.cur_infos[f'{row.cur_id}_'] = dict()
        self.func_list[f'{row.cur_id}_'] = []

        row.items[-1].unbind('<Double-Button-1>')
        row.items[-2].unbind('<Double-Button-1>')

        row.items[1].unbind('<Double-Button-1>')
        row.items[2].unbind('<Double-Button-1>')

        row.items[5].unbind('<Double-Button-1>')
        row.items[6].unbind('<Double-Button-1>')

    def initial_values(self):
        self.create_host('Хост', 'Создатель игры\n')
        self.create_leader('Лидер',
                           'Все действия игроков отправляются лидеру\nИ он самолично выбирает, какое из этих действий отправить хосту\n')
        self.create_time('0', '0', '10')

    def define_collbacks(self):
        def escape_key(_):
            self.is_fullscreen = self.is_fullscreen ^ 1
            self.root.attributes("-fullscreen", self.is_fullscreen)

            # if self.cur_info is self.empty_info:
            #     return
            # self.to_label()
            # self.cur_infos[self.cur_info[0]][self.cur_info[1]].configure(bg='snow')
            # self.cur_info = self.empty_info

        def delete_key(_):
            if self.cur_info is self.empty_info:
                return
            if self.cur_info[1] in ['ptime', 'rhost', 'rleader']:
                return

            if self.cur_info[0] == 't':
                for i in self.cur_infos[f'{self.cur_info[1]}_'].values():
                    i.destroy()
                self.restore_canvas(self.lists_canvas, self.lists_scroll_frame)

                del self.cur_infos[f'{self.cur_info[1]}_']
                del self.info_creators[f'{self.cur_info[1]}_']

                self.lists_label['text'] = 'Нет вкладки'
                self.lists_btn['state'] = 'disabled'

                self.cur_tab = 't'

            if self.cur_info[0] == 'r':
                for i in self.cur_infos[f'{self.cur_info[1]}_'].values():
                    i.destroy()
                self.restore_canvas(self.actions_canvas, self.actions_scroll_frame)

                del self.cur_infos[f'{self.cur_info[1]}_']
                del self.info_creators[f'{self.cur_info[1]}_']

                self.actions_label['text'] = 'Нет роли'
                self.actions_btn['state'] = 'disabled'

                self.cur_role = 'r'

            if self.cur_info[0] == 'p':
                for i in self.cur_infos[f'{self.cur_info[1]}_'].values():
                    i.destroy()
                self.restore_canvas(self.functions_canvas, self.functions_scroll_frame)

                del self.cur_infos[f'{self.cur_info[1]}_']
                del self.info_creators[f'{self.cur_info[1]}_']

                self.functions_label['text'] = 'Нет переменной'
                self.functions_btn['state'] = 'disabled'

                self.cur_param = 'p'

                del self.func_list[f'{self.cur_info[1]}_']

            if self.reaction_id == self.cur_info[1]:
                self.reaction_action.delete('1.0', 'end')
                self.reaction_condition.delete('1.0', 'end')
                self.reaction_btn['text'] = 'Добавить реакцию'
                self.reaction_btn.bind('<Button-1>', lambda e: self.reaction_func(None))

            if self.refunction_id == self.cur_info[1]:
                self.refunction_function.delete('1.0', 'end')
                self.refunction_condition.delete('1.0', 'end')
                self.refunction_btn['text'] = 'Добавить функцию'
                self.refunction_btn.bind('<Button-1>', lambda e: self.refunction_func(None))

            if (self.cur_info[1] == self.edit_id or
                    self.cur_info[1] == self.edit_name):
                self.destroy_edit_frame()

            if self.cur_info[0] in self.func_list:
                self.func_list[self.cur_info[0]].remove(self.cur_info[1])

            self.cur_infos[self.cur_info[0]].pop(self.cur_info[1]).destroy()
            self.cur_info = self.empty_info

        def move_up(_):
            if self.cur_info[0] in self.func_list:
                func_list = self.func_list[self.cur_info[0]]
                i = func_list.index(self.cur_info[1])
                if i == 0:
                    self.func_list[self.cur_info[0]] = func_list[1:] + func_list[:1]
                else:
                    func_list[i - 1], func_list[i] = func_list[i], func_list[i - 1]

                func_list = self.func_list[self.cur_info[0]]

                for func_id in func_list:
                    self.cur_infos[self.cur_info[0]][func_id].pack_forget()
                for func_id in func_list:
                    self.cur_infos[self.cur_info[0]][func_id].pack_again()

        def move_down(_):
            if self.cur_info[0] in self.func_list:
                func_list = self.func_list[self.cur_info[0]]
                i = func_list.index(self.cur_info[1])
                if i + 1 == len(func_list):
                    self.func_list[self.cur_info[0]] = func_list[-1:] + func_list[:-1]
                else:
                    func_list[i], func_list[(i + 1) % len(func_list)] = func_list[(i + 1) % len(func_list)], func_list[i]

                func_list = self.func_list[self.cur_info[0]]

                for func_id in func_list:
                    self.cur_infos[self.cur_info[0]][func_id].pack_forget()
                for func_id in func_list:
                    self.cur_infos[self.cur_info[0]][func_id].pack_again()

        self.root.bind('<Escape>', escape_key)
        self.root.bind('<Delete>', delete_key)
        self.root.bind('<Up>', move_up)
        self.root.bind('<Down>', move_down)

    def cont(self):
        filename = filedialog.askopenfilename(initialdir=r'C:\Users\o.verbin\Oleg\ScenarioEditor',
                                              title='Выберите сценарий',
                                              filetypes=(("Сценарий.txt", "*.txt"),)
                                              )
        if not filename:
            return
        #         filename = r'C:\Users\o.verbin\Oleg\ScenarioEditor\Default Scenaryd\scenary.txt'
        self.begin(filename)

    def save_game(self):
        ftypes = [('All files', '*')]
        filename = filedialog.asksaveasfilename(filetypes=ftypes,
                                                defaultextension='.txt')
        if filename == '':
            return

        dirname = os.path.dirname(os.path.realpath(filename))
        filename = filename.rsplit('/', 2)[-1].split('.')[0]

        dirpath = os.path.join(dirname, filename)
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        os.makedirs(dirpath)

        filename1 = os.path.join(dirpath, filename + '.txt')
        filename2 = os.path.join(dirpath, filename + '.rp')

        sep = self.sep
        enter = self.enter
        try:
            with open(filename1, 'w', encoding='utf-8') as f1, open(filename2, 'w', encoding='utf-8') as f2:
                for row in self.cur_infos['p'].values():
                    value, min_value, max_value = [*map(lambda x: x['text'], row.items[4:-2:2])]

                    f1.write(sep.join(['-v', row.cur_id,
                                       value, min_value, max_value,
                                       str(row.visibility), row.items[2]['text']]) + '\n')

                    if min_value.lower() == 'none':
                        min_value = '-' + self.MAXINT
                    if max_value.lower() == 'none':
                        max_value = self.MAXINT

                    f2.write(sep.join(['-v', row.cur_id,
                                       *[str(float(x))
                                         for x in [value, min_value, max_value]],
                                       str(row.visibility), row.items[2]['text']]) + '\n')

                    for func_id in self.func_list[row.cur_id + '_']:
                        row = self.cur_infos[func_id.split('_')[0] + '_'][func_id]
                        f1.write('-f' + sep + row.cur_id + sep +
                                 row.function.replace('\n', enter) + sep +
                                 row.cond.replace('\n', enter) + '\n')
                        f2.write('-f' + sep + row.cur_id + sep +
                                 str_polish(row.function, self) + sep +
                                 str_polish(row.cond, self) + '\n')

                impath = os.path.join(os.path.dirname(os.path.realpath(filename1)), 'Images')
                if os.path.exists(impath) and os.path.isdir(impath):
                    shutil.rmtree(impath)
                os.makedirs(impath)

                for row in self.cur_infos['t'].values():
                    s = ('-t' + sep + row.cur_id + sep +
                         str(row.visibility) + sep +
                         row.items[2]['text'] + '\n')
                    f1.write(s)
                    f2.write(s)

                    for row in self.cur_infos[row.cur_id + '_'].values():
                        shutil.copy(row.filename,
                                    os.path.join(impath,
                                                 row.cur_id + ' ' + str(row.visibility) +
                                                 '.' + row.filename.rsplit('.', 2)[-1]))

                for row in self.cur_infos['r'].values():
                    s = ('-r' + sep + row.cur_id + sep +
                         row.descr.replace('\n', enter) + sep
                         + row.items[2]['text'] + '\n')
                    f1.write(s)
                    f2.write(s)
                    for row in self.cur_infos[row.cur_id + '_'].values():
                        f1.write('-a' + sep + row.cur_id + sep +
                                 row.items[4]['text'] + sep +
                                 row.desc.replace('\n', enter) + sep +
                                 row.req.replace('\n', enter) + sep +
                                 ','.join(row.ans) + sep +
                                 ','.join(row.ans_id) + sep + str(len(row.action)) + '\n' +
                                 '\n'.join([a.replace('\n', enter) + sep +
                                            c.replace('\n', enter)
                                            for a, c in zip(row.action, row.cond)] + [''])
                                 )
                        f2.write('-a' + sep + row.cur_id + sep +
                                 row.items[4]['text'] + sep +
                                 row.desc.replace('\n', enter) + sep +
                                 str_polish(row.req, self) + sep +
                                 ','.join(row.ans) + sep +
                                 ','.join(row.ans_id) + sep + str(len(row.action)) + '\n' +
                                 '\n'.join([str_polish(a, self) + sep +
                                            str_polish(c, self)
                                            for a, c in zip(row.action, row.cond)] + [''])
                                 )

                f1.write('-l' + sep + self.loose_cond.replace('\n', enter) + '\n')
                f1.write('-w' + sep + self.win_cond.replace('\n', enter) + '\n')
                f1.write('-n' + sep + self.name.replace('\n', enter) + '\n')

                f2.write('-l' + sep + str_polish(self.loose_cond, self) + '\n')
                f2.write('-w' + sep + str_polish(self.win_cond, self) + '\n')
                f2.write('-n' + sep + self.name.replace('\n', enter) + '\n')
                messagebox.showinfo('Сохранено', 'Успешно сохранено')
        except ValueError:
            messagebox.showerror('Ошибка',
                                 'Ошибка в сценарии. Скорее всего вы удалили переменную, которая где-то используется')
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                shutil.rmtree(dirpath)

    def restore(self, filename):
        # self.initial_values()
        sep = self.sep
        enter = self.enter
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line[:-1].replace(enter, '\n').split(sep)
                if line[0] == '-v':
                    var_id, value, min_value, max_value, visibility, name = line[1:]
                    if var_id == 'ptime':
                        self.create_time(value, min_value, max_value)
                    else:
                        self.show_param(self.param_scroll, name, int(visibility), value, min_value, max_value,
                                        force_id=int(var_id[1:]))
                elif line[0] == '-t':
                    tab_id, visibility, name = line[1:]
                    self.show_tab(self.tab_scroll, name, int(visibility), force_id=int(tab_id[1:]))
                elif line[0] == '-r':
                    role_id, descr, name = line[1:]
                    if role_id == 'rhost':
                        self.create_host(name, descr + '\n')
                    elif role_id == 'rleader':
                        self.create_leader(name, descr + '\n')
                    else:
                        self.show_role(self.role_scroll, name, descr + '\n', force_id=int(role_id[1:]))
                elif line[0] == '-f':
                    func_id, func, cond = line[1:]
                    creator = self.info_creators[func_id.split('_')[0] + '_']
                    m = creator.next_id

                    self.show_function(self.functions_scroll_frame,
                                       func_id.split('_')[0], func + '\n',
                                       cond + '\n', edit=False, force_id=int(func_id.split('_')[1]))

                    creator.next_id = max(m, creator.next_id)
                elif line[0] == '-a':
                    action_id, max_n, descr, req, ans, ans_id, n = line[1:]
                    ans = ans.split(',') if ans else []
                    ans_id = ans_id.split(',') if ans_id else []
                    answers, conditions = [], []
                    for i in range(int(n)):
                        act, cond = f.readline()[:-1].replace(enter, '\n').split(sep)
                        answers.append(act)
                        conditions.append(cond)

                    class Tmp:
                        def __init__(self, a, c):
                            self.action = a
                            self.condition = c

                    self.cur_infos['re'] = dict([
                        (i, Tmp(a + '\n', c + '\n'))
                        for i, (a, c) in enumerate(zip(answers, conditions))
                    ])

                    class Tmp:
                        def __init__(self, new_ans, new_ans_id):
                            self.items = [None, None, dict({'text': new_ans})]
                            self.cur_id = new_ans_id

                    self.cur_infos['an'] = dict([
                        (i, Tmp(ans, ans_id))
                        for i, (ans, ans_id) in enumerate(zip(ans, ans_id))
                    ])

                    self.show_action(self.actions_scroll_frame, action_id.split('_')[0],
                                     descr + '\n',
                                     req + '\n',
                                     edit=False,
                                     force_id=int(action_id.split('_')[1]))

                    self.cur_infos['re'] = dict()
                    self.cur_infos['an'] = dict()

                    self.cur_infos[action_id.split('_')[0] + '_'][action_id].items[4]['text'] = max_n

                elif line[0] == '-l':
                    self.loose_cond = line[1]
                elif line[0] == '-w':
                    self.win_cond = line[1]
                elif line[0] == '-n':
                    self.name = line[1]
                else:
                    messagebox.showerror('Ошибка', 'Ошибка в сценарии')
                    raise Exception("Ошибка в сценарии")

        dirname = os.path.dirname(os.path.realpath(filename))
        for filename in os.listdir(dirname + '/Images'):
            if filename[0] == '.':
                continue
            print(dirname + '/Images/' + filename)
            image_id, visibility = filename.split('.')[0].split(' ')
            self.add_list(self.lists_scroll_frame, image_id.split('_')[0],
                          int(visibility), dirname + '/Images/' + filename,
                          force_id=int(image_id.split('_')[1]))


if __name__ == '__main__':
    game = Game()

    game.start()
