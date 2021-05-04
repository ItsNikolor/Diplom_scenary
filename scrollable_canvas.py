from tkinter import Canvas, Frame, Scrollbar, RIGHT, BOTH, NW, Y


def add_scrollable_canvas(frame):
    canvas = Canvas(frame, bg='purple4')
    canvas.pack(side=RIGHT, fill=BOTH, expand=True)

    mailbox_frame = Frame(canvas, bg='purple4')

    canvas_frame = canvas.create_window((0, 0),
                                        window=mailbox_frame, anchor=NW)

    mail_scroll = Scrollbar(canvas, orient="vertical",
                            command=canvas.yview)
    mail_scroll.pack(side=RIGHT, fill=Y)

    canvas.config(yscrollcommand=mail_scroll.set)

    def FrameWidth(event):
        canvas_width = event.width
        canvas.itemconfig(canvas_frame, width=canvas_width)

    def OnFrameConfigure(_):
        canvas.configure(scrollregion=canvas.bbox("all"))

    mailbox_frame.bind("<Configure>", OnFrameConfigure)
    canvas.bind('<Configure>', FrameWidth)

    def _bound_to_mousewheel(_):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbound_to_mousewheel(_):
        canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(event):
        if canvas.winfo_height() < mailbox_frame.winfo_height():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    mailbox_frame.bind('<Enter>', _bound_to_mousewheel)
    mailbox_frame.bind('<Leave>', _unbound_to_mousewheel)

    return canvas, mailbox_frame
