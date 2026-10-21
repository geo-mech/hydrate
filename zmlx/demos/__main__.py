if __name__ == "__main__":
    from zmlx.ui import gui


    def f():
        gui.show_demo()


    gui.execute(f, close_after_done=False)
