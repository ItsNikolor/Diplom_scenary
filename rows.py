from tkinter import Frame, Label, Entry, messagebox, Toplevel

from PIL import ImageTk


class EmptyRow:
    def bind(self, *args):
        return

    def configure(self, **kwargs):
        return

    def destroy(self):
        return

    def turn_off(self):
        return

    def turn_on(self):
        return


class RowWithLabels:
    def __init__(self, game, my_font, *args):
        self.values = args
        self.myFont = my_font
        self.game = game

    def show(self, frame):
        all_frame = Frame(frame)
        all_frame.pack(fil='x')

        self.items = [all_frame]

        for text in self.values:
            frame = Frame(all_frame, height=20)
            frame.pack(fill='both', side='left', expand=True)
            frame.pack_propagate(0)

            label = Label(frame, text=text, font=self.myFont, anchor='w')
            label.pack(anchor='w')

            self.items.append(frame)
            self.items.append(label)

        self.turn_off()

    def add_id(self, width=70):
        frame = Frame(self.items[0], width=width)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(0)

        label = Label(frame, text=self.cur_id, font=self.myFont)
        label.pack(anchor='w')

        label.bind('<Double-Button-1>', lambda e: self.change_visibility())
        frame.bind('<Double-Button-1>', lambda e: self.change_visibility())

        self.items.append(frame)
        self.items.append(label)

        self.turn_off()

    def turn_on(self):
        [x.configure(bg='light goldenrod')
         for x in self.items]

    def turn_off(self):
        [x.configure(bg='snow')
         for x in self.items]

    def bind(self, *args, **kwargs):
        for i in self.items:
            i.bind(*args, **kwargs)

    def configure(self, **kwargs):
        for i in self.items:
            for name, value in kwargs.items():
                try:
                    i.configure(**{name: value})
                except:
                    print('error in ', self)

    def change_visibility(self, visibility=None):
        if visibility is None:
            if hasattr(self, 'visibility'):
                self.visibility = (self.visibility + 1) % 2
            else:
                return
        else:
            self.visibility = visibility

        for i in self.items[2::2]:
            i.configure(fg='green' if self.visibility else 'red')

    def destroy(self):
        self.items[0].destroy()

    def pack_forget(self):
        self.items[0].pack_forget()

    def pack_again(self):
        self.items[0].pack(fill='x')

    def __str__(self):
        return str(self.values)


class RowWithEntrys(RowWithLabels):
    def show(self, frame):
        super().show(frame)

        def func(i):
            self.items[i].bind('<Double-Button-1>', lambda e: self.to_entry(i))
            self.items[i - 1].bind('<Double-Button-1>', lambda e: self.to_entry(i))

        for ind in range(2, len(self.items), 2):
            func(ind)
            self.items[ind].func = lambda s: True

    def to_entry(self, i):
        self.has_entry = i
        text = self.items[i]['text']
        self.previous_text = text
        self.previous_func = self.items[i].func
        self.items[i].destroy()

        entry = Entry(self.items[i - 1], font=self.myFont, bg=self.items[-1]['bg'])
        entry.insert(0, text)
        if hasattr(self, 'visibility'):
            entry.configure(fg='green' if self.visibility else 'red')
        entry.pack(anchor='w', fill='x')
        self.items[i] = entry

        entry.bind('<Return>', lambda e: self.to_label(i))

    def to_label(self, i):
        del self.has_entry
        text = self.items[i].get()
        self.items[i].destroy()

        if not self.previous_func(text):
            text = self.previous_text
            messagebox.showerror("Ошибка", "Неподходящее значение")

        l = Label(self.items[i - 1], text=text, font=self.myFont, bg=self.items[-1]['bg'], anchor='w')
        if hasattr(self, 'visibility'):
            l.configure(fg='green' if self.visibility else 'red')
        l.pack(anchor='w')
        l.func = self.previous_func
        self.items[i] = l

        l.bind('<Double-Button-1>', lambda e: self.to_entry(i))

        self.bind('<Button-1>', lambda e: self.game.click_on_item(self.name, self.cur_id))
        if hasattr(self, 'add_func'):
            self.bind('<Button-1>', lambda e: self.add_func(self.items[2]['text'], self.cur_id), add=True)


class RowWithImage(RowWithLabels):
    def __init__(self, _, my_font, img, default_img, filename, *args):
        self.img = img
        self.default_img = default_img
        self.values = args
        self.filename = filename
        self.myFont = my_font

    def show(self, frame):
        all_frame = Frame(frame)
        all_frame.pack(fil='x')

        self.items = [all_frame]

        frame = Frame(self.items[0])
        frame.pack(side='top', fill='x', expand=True)

        label = Label(frame, font=self.myFont, anchor='w')
        label.pack(anchor='w')

        self.items.append(frame)
        self.items.append(label)

        frame = Frame(all_frame, width=320, height=180)
        frame.pack(fill='both', side='left', expand=True)
        frame.pack_propagate(0)

        label = Label(frame, image=self.img)
        label.pack(anchor='w')

        label.bind('<Double-Button-1>', self.show_fullscreen)

        self.items.append(frame)
        self.items.append(label)

        for text in self.values:
            frame = Frame(all_frame, height=20)
            frame.pack(fill='x', side='left', expand=True)
            frame.pack_propagate(0)

            label = Label(frame, text=text, font=self.myFont, anchor='w')
            label.pack(anchor='w')

            self.items.append(frame)
            self.items.append(label)

        [x.configure(bg='snow')
         for x in self.items]

    def show_fullscreen(self, _):
        window = Toplevel()
        window.geometry('500x500')

        img = self.default_img
        w, h = img.size
        k = min(1, 500 / w, 500 / h)

        img = ImageTk.PhotoImage(img.resize((int(w * k), int(h * k))))

        self.image_label = Label(window, image=img)
        self.image_label.pack()
        self.image_label.image = img

        window.bind('<Configure>', self.resize)

    def resize(self, e):
        img = self.default_img
        w, h = img.size

        k = min(e.width / w, e.height / h)

        img = ImageTk.PhotoImage(img.resize((int(w * k), int(h * k))))
        self.image_label.configure(image=img)
        self.image_label.image = img

    def add_id(self, _=None):
        self.items[2]['text'] = self.cur_id
        self.items[2].bind('<Double-Button-1>', lambda e: self.change_visibility())
        self.items[1].bind('<Double-Button-1>', lambda e: self.change_visibility())
