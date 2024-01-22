class Colorib:
    # ANSI color codes for text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"  # Reset all text formatting

    # ANSI color codes for background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Text style modifiers
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    CONCEAL = "\033[8m"

    # Colorama-like functions
    init = lambda: None  # Placeholder for Colorama's init function

    @classmethod
    def colorize(cls, text, color):
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def style(cls, text, style):
        return f"{style}{text}{cls.RESET}"

    @classmethod
    def colorize_with_background(cls, text, color, bg_color):
        return f"{color}{bg_color}{text}{cls.RESET}"

    @classmethod
    def style_with_background(cls, text, style, bg_color):
        return f"{style}{bg_color}{text}{cls.RESET}"

    @classmethod
    def auto_reset(cls, text):
        return f"{text}{cls.RESET}"

    @classmethod
    def strip_ansi(cls, text):
        import re
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    @classmethod
    def print_color(cls, text, color):
        print(f"{color}{text}{cls.RESET}")

    @classmethod
    def disable(cls):
        cls.RESET = ''
        cls.BLACK = ''
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.MAGENTA = ''
        cls.CYAN = ''
        cls.WHITE = ''
        cls.BG_BLACK = ''
        cls.BG_RED = ''
        cls.BG_GREEN = ''
        cls.BG_YELLOW = ''
        cls.BG_BLUE = ''
        cls.BG_MAGENTA = ''
        cls.BG_CYAN = ''
        cls.BG_WHITE = ''
        cls.BOLD = ''
        cls.ITALIC = ''
        cls.UNDERLINE = ''
        cls.BLINK = ''
        cls.REVERSE = ''
        cls.CONCEAL = ''

    @classmethod
    def enable(cls):
        cls.RESET = "\033[0m"
        cls.BLACK = "\033[30m"
        cls.RED = "\033[31m"
        cls.GREEN = "\033[32m"
        cls.YELLOW = "\033[33m"
        cls.BLUE = "\033[34m"
        cls.MAGENTA = "\033[35m"
        cls.CYAN = "\033[36m"
        cls.WHITE = "\033[37m"
        cls.BG_BLACK = "\033[40m"
        cls.BG_RED = "\033[41m"
        cls.BG_GREEN = "\033[42m"
        cls.BG_YELLOW = "\033[43m"
        cls.BG_BLUE = "\033[44m"
        cls.BG_MAGENTA = "\033[45m"
        cls.BG_CYAN = "\033[46m"
        cls.BG_WHITE = "\033[47m"
        cls.BOLD = "\033[1m"
        cls.ITALIC = "\033[3m"
        cls.UNDERLINE = "\033[4m"
        cls.BLINK = "\033[5m"
        cls.REVERSE = "\033[7m"
        cls.CONCEAL = "\033[8m"

    @classmethod
    def prompt(cls, text, color=WHITE):
        return input(f"{color}{text}{cls.RESET}")

    @classmethod
    def colorize_multiple(cls, text_parts, colors):
        if len(text_parts) != len(colors):
            raise ValueError("The number of text parts must match the number of colors")
        colorized_parts = [f"{color}{text}{cls.RESET}" for text, color in zip(text_parts, colors)]
        return "".join(colorized_parts)

    @classmethod
    def print_table(cls, data, headers=None, cell_width=12):
        if headers:
            cls.print_table_row(headers, header=True)
        for row in data:
            cls.print_table_row(row, cell_width=cell_width)

    @classmethod
    def print_table_row(cls, row, header=False, cell_width=12):
        format_str = f"{cls.BG_WHITE if header else ''}{{:<{cell_width}}}{cls.RESET}"
        formatted_row = [format_str.format(str(item)) for item in row]
        print("".join(formatted_row))
