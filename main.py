import pygame
import tomllib
import sys
import inspect


default_config_file='config.toml'

# Colors
BACKGROUND_COLOR = "#2b2f40"
TEXT_COLOR = (255, 255, 255)
CURSOR_COLOR = (100, 100, 100)
CURRENT_LINE_COLOR = "#35394b"

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FONT_SIZE = 30
FPS = 30

class VimEmulator:
    def __init__(self, config_file=default_config_file):
        # Load the configuration
        self.config = self.load_config(config_file)
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        # font = pygame.font.Font(pygame.font.get_default_font(), FONT_SIZE)
        self.font = pygame.font.Font(pygame.font.match_font("firacode"), FONT_SIZE)
        self.clock = pygame.time.Clock()
        self.mode = 'NORMAL'  # Initial state (operating automaton state)
        self.buffer = [""]  # Text buffer
        self.cursor_x = 0  # Cursor position (x)
        self.cursor_y = 0  # Cursor position (y)
        self.scroll_offset = 0  # Scroll offset for rendering
        self.command_line = ""  # For command mode
        self.show_cursor = True
        self.cursor_timer = 0    # 光标闪烁计时器
        self.oplist = [] # 待操作列表
        self.prefix = 0

        self.search_query = ""  # For search mode
        self.search_results = []  # List of search results (line, column)
        self.copied_line = ""  # For copying lines TODO:
        self.wait = False
        self.highlight_current_line = True

    def load_config(self,config_file=default_config_file):
        """Load key mappings from the TOML configuration file."""
        try:
            with open(config_file, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    def source(self):
        self.config = self.load_config()
    
# ui begin
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        # 滚动偏移量
        visible_lines = WINDOW_HEIGHT // FONT_SIZE - 3
        self.scroll_offset = max(0, min(self.cursor_y - visible_lines // 2, len(self.buffer) - visible_lines))

        # 显示模式 行列号
        if self.mode != 'NORMAL' and self.mode != 'COMMAND':
            mode_text = self.font.render(f"-- {self.mode} --", True, TEXT_COLOR)
            self.screen.blit(mode_text, (10, WINDOW_HEIGHT-34))

        text = f"{self.cursor_y},{self.cursor_x}"
        xy_text = self.font.render(text, True, TEXT_COLOR)
        self.screen.blit(xy_text, (WINDOW_WIDTH - len(text)* 10 -50, WINDOW_HEIGHT-34))


        # 高亮当前行
        if self.highlight_current_line:
            pygame.draw.rect(
                self.screen,
                CURRENT_LINE_COLOR,
                (10,10+  (self.cursor_y - self.scroll_offset) * FONT_SIZE,WINDOW_WIDTH - 20, FONT_SIZE)
            )


        # 显示光标
        if self.show_cursor:
            cursor_x = 10 + self.font.size(self.buffer[self.cursor_y][:self.cursor_x])[0]
            cursor_y = 10 + (self.cursor_y - self.scroll_offset) * FONT_SIZE
            match self.mode:
                case 'INSERT':
                    # 插入模式：细线光标（闪烁）
                    pygame.draw.rect(
                        self.screen,
                        CURSOR_COLOR,
                        (cursor_x, cursor_y, 2, FONT_SIZE)
                    )
                    pygame.draw.rect(self.screen, CURSOR_COLOR, (cursor_x, cursor_y, 2, FONT_SIZE))
                case 'NORMAL':
                    if self.cursor_x != 0 and self.cursor_x>= len(self.buffer[self.cursor_y]):
                        cursor_x -= self.font.size(' ')[0]

                    # 普通模式：块状光标（填充矩形）
                    pygame.draw.rect(
                        self.screen,
                        CURSOR_COLOR,
                        (cursor_x, cursor_y, self.font.size(" ")[0], FONT_SIZE)
                    )

        # 显示命令行
        if self.mode in {'COMMAND', 'SEARCH'}:
            command_surface = self.font.render(f":{self.command_line}", True, TEXT_COLOR)
            self.screen.blit(command_surface, (10, WINDOW_HEIGHT - FONT_SIZE - 10))

        # 显示缓冲区内容
        for i, line in enumerate(self.buffer[self.scroll_offset:self.scroll_offset + visible_lines]):
            line_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(line_surface, (10, 10+i * FONT_SIZE))

    def update_cursor(self):
        if self.mode == 'INSERT':
            # 插入模式下的光标闪烁逻辑
            self.cursor_timer += 1
            if self.cursor_timer >= FPS // 2:
                self.show_cursor = not self.show_cursor
                self.cursor_timer = 0
        elif self.mode == 'NORMAL':
            # 普通模式光标始终显示
            self.show_cursor = True
# ui end


# debug functions begin
    def clean_oplist(self):
        self.wait = False
        self.oplist = []
    def print_oplist(self):
        print(self.oplist)
    def print_prefix(self):
        print(self.prefix)
# debug functions end 

# core begin
    def call_function_dynamically(self,func, args):
        """
            根据函数参数个数动态调用函数
            :param func: 目标函数
            :param args: 提供的参数列表
        """
        # 获取函数的签名
        sig = inspect.signature(func)
        # 获取必需的参数个数
        required_args_count = sum(
            1 for param in sig.parameters.values()
            if param.default == inspect.Parameter.empty and param.kind in [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]
        )
        if len(args)<=required_args_count:
            self.wait = True
            return args
        self.wait = False
        truncated_args = []
        for x in args[1:1+required_args_count]:
            if not isinstance(x,str):
                truncated_args.append(x.unicode)
            else:
                truncated_args.append(x)
        func(*truncated_args)
        return args[required_args_count+1:]

    def interpreter(self,event):
        mode_config = self.config["keybindings"].get(self.mode, {})
        if isinstance(event,str):
            action = mode_config.get(event)
            if not action:
                action = event
        else:
            action = mode_config.get(event.unicode, None) or mode_config.get(pygame.key.name(event.key), None)
            if not action:
                action = event.unicode
        return action

    def number_prefix(self,num):
        self.prefix = int(num)+self.prefix*10**len(num)

    def runner(self):

        if self.oplist == []:
            return
        action = self.interpreter(self.oplist[0])
        if not self.mode in ['COMMAND','INSERT'] and isinstance(action,str) and action.isdigit():
            self.number_prefix(action)
            self.oplist=self.oplist[1:]
            self.runner()
        else:
            self.prefix = max(self.prefix,1)
            cl = True
            if isinstance(action,list):
                self.oplist=self.oplist[1:]
                self.oplist = self.prefix*action + self.oplist
                # print(self.oplist)
            elif hasattr(self,action):
                for i in range(self.prefix-1):
                    self.call_function_dynamically(getattr(self,action),self.oplist)
                self.oplist = self.call_function_dynamically(getattr(self,action),self.oplist)
            elif self.mode == 'INSERT':
                self.oplist=self.oplist[1:]
                self.insert_char(action*self.prefix)
            elif self.mode == 'COMMAND':
                self.oplist=self.oplist[1:]
                self.command_line+=action*self.prefix
            else:
                cl = False
                self.oplist=self.oplist[1:]
                print(f"Unknown action: {action}")

            if cl:
                self.prefix = 0

            if not self.wait:
                self.runner()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            self.oplist.append(event)
            self.runner()
# core end

# mode command begin
    def quit(self):
        print("Quitting...")
        pygame.quit()
        sys.exit()

    def switch_to_insert(self):
        self.mode = "INSERT"
        print("Switched to INSERT mode")

    def switch_to_normal(self):
        self.mode = "NORMAL"
        if self.cursor_x == len(self.buffer[self.cursor_y]) and self.cursor_x != 0:
            self.cursor_x-=1
        print("Switched to NORMAL mode")

    def switch_to_command(self):
        self.command_line = ""
        self.mode = "COMMAND"
        print("Switched to COMMAND mode")
# mode command end

# edit command begin
    def insert_char(self, char):
        self.buffer[self.cursor_y] = (self.buffer[self.cursor_y][:self.cursor_x] + char + self.buffer[self.cursor_y][self.cursor_x:])
        self.cursor_x += len(char)
    def delete_char(self):
        if self.cursor_x > 0:
            self.buffer[self.cursor_y] = (self.buffer[self.cursor_y][:self.cursor_x - 1] + self.buffer[self.cursor_y][self.cursor_x:])
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            prev_line = self.buffer[self.cursor_y - 1]
            self.cursor_x = len(prev_line)
            self.buffer[self.cursor_y - 1] += self.buffer[self.cursor_y]
            del self.buffer[self.cursor_y]
            self.cursor_y -= 1
    def split_line(self):
        self.buffer.insert(self.cursor_y + 1, self.buffer[self.cursor_y][self.cursor_x:])
        self.buffer[self.cursor_y] = self.buffer[self.cursor_y][:self.cursor_x]
        self.cursor_y += 1
        self.cursor_x = 0
    def new_line_upward(self):
        self.cursor_y-=1
        self.new_line()
    def new_line(self):
        self.buffer.insert(self.cursor_y + 1, "")
        self.cursor_y += 1
        self.cursor_x = 0
        self.mode = "INSERT"
    def delete_line(self):
        self.buffer[self.cursor_y]=""
        self.cursor_x = 0
    def append_char(self):
        self.cursor_x = min(self.cursor_x+1,len(self.buffer[self.cursor_y]))
        self.switch_to_insert()
    def line_end(self):
        self.cursor_x = max(0,len(self.buffer[self.cursor_y])-1)
    def line_begin(self):
        self.cursor_x = 0
    def join_next_line(self):
        if len(self.buffer) == self.cursor_y+1:
            return
        if self.buffer[self.cursor_y+1] == "":
            self.buffer=self.buffer[:self.cursor_y+1]+self.buffer[self.cursor_y+2:]
            self.cursor_x = max(0,len(self.buffer[self.cursor_y])-1)
            return
        self.cursor_x = len(self.buffer[self.cursor_y])
        self.buffer[self.cursor_y]+=' '+self.buffer[self.cursor_y+1];
        self.buffer=self.buffer[:self.cursor_y+1]+self.buffer[self.cursor_y+2:]
    def replace_char(self, ch):
        if self.cursor_x==0 and self.buffer[self.cursor_y] == "":
            return
        self.buffer[self.cursor_y]=self.buffer[self.cursor_y][:self.cursor_x]+ch+self.buffer[self.cursor_y][self.cursor_x+1:]
        
# edit command end


# file control begin
    def save_to_file(self, filename):
        """保存缓冲区到文件"""
        try:
            with open(filename, 'w') as f:
                f.write('\n'.join(self.buffer))
            print(f"{filename} 保存成功")
        except Exception as e:
            print(f"保存失败：{e}")

    def load_from_file(self, filename):
        """加载文件到缓冲区"""
        try:
            with open(filename, 'r') as f:
                self.buffer = f.read().splitlines()
            print(f"{filename} 加载成功")
        except FileNotFoundError:
            print(f"{filename} not found")
        except Exception as e:
            print(f"加载失败：{e}")
# file control end

# COMMAND mode begin
    def execute_command(self):
        self.oplist=self.command_line.split(" ")
        self.command_line = ""
        self.switch_to_normal()
        if self.oplist and self.oplist[0] == 'q':
            self.quit()
        else:
            self.runner()

    def delete_command(self):
        if len(self.command_line):
            self.command_line=self.command_line[:-1]
# COMMAND mode end

# movement begin
    def move_cursor_left(self):
        if self.buffer[self.cursor_y] == "":
            self.cursor_x = 0
        else:
            self.cursor_x = min(len(self.buffer[self.cursor_y])-1, self.cursor_x)
        self.cursor_x = max(0,self.cursor_x - 1)
        print(f"Cursor moved left to position ({self.cursor_x}, {self.cursor_y})")

    def move_cursor_up(self):
        self.cursor_y = max(0, self.cursor_y - 1)
        print(f"Cursor moved up to position ({self.cursor_x}, {self.cursor_y})")
    def move_cursor_right(self):
        if self.mode == 'NORMAL':
            self.cursor_x = min(max(len(self.buffer[self.cursor_y])-1,0),self.cursor_x+1)
        else:
            self.cursor_x = min(len(self.buffer[self.cursor_y]), self.cursor_x + 1)
        print(f"Cursor moved right to position ({self.cursor_x}, {self.cursor_y})")
    def move_cursor_down(self):
        self.cursor_y = min(len(self.buffer) - 1, self.cursor_y + 1)
        print(f"Cursor moved down to position ({self.cursor_x}, {self.cursor_y})")
    def char_type(self,ch):
        if ch == ' ':
            return 0
        elif ch.isalpha() or ch == '_':
            return 1
        else:
            return 2

    def next_word(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==0 or self.char_type(self.buffer[self.cursor_y][i]) != self.char_type(self.buffer[self.cursor_y][i-1])));
    def next_WORD(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==0 or not self.char_type(self.buffer[self.cursor_y][i-1])))

    def next_word_end(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==len(self.buffer[self.cursor_y])-1 or self.char_type(self.buffer[self.cursor_y][i]) != self.char_type(self.buffer[self.cursor_y][i+1])))
    def next_WORD_end(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==len(self.buffer[self.cursor_y])-1 or not self.char_type(self.buffer[self.cursor_y][i+1])))

    def last_word(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==0 or self.char_type(self.buffer[self.cursor_y][i]) != self.char_type(self.buffer[self.cursor_y][i-1])),"backward")
    def last_WORD(self):
        self.check_and_move(lambda i: self.char_type(self.buffer[self.cursor_y][i]) and (i==0 or not self.char_type(self.buffer[self.cursor_y][i-1])),"backward")

    def check_and_move(self,check,d="forward",c=True,m=True):
        # d direction; c cross_line m move_on_fail
        if d == 'forward':
            flag = 0
            for i in range(self.cursor_x+1,len(self.buffer[self.cursor_y])):
                if check(i):
                    flag = 1
                    self.cursor_x = i
                    break
            if not flag:
                if c:
                    if len(self.buffer) == 1+self.cursor_y:
                        self.cursor_x = max(0,len(self.buffer[self.cursor_y])-1)
                    else:
                        self.cursor_x = 0
                        self.cursor_y +=1
                        if self.buffer[self.cursor_y]!= "" and not check(self.cursor_x):
                            self.check_and_move(check,d,c,m)
                elif m:
                    self.cursor_x = max(0,len(self.buffer[self.cursor_y])-1)
                else: 
                    return False
        else:
            flag = 0
            for i in range(self.cursor_x-1,-1,-1):
                if check(i):
                    flag = 1
                    self.cursor_x = i
                    break
            if not flag:
                if c:
                    if self.cursor_y == 0:
                        self.cursor_x = 0
                    else:
                        self.cursor_y -= 1
                        self.cursor_x = max(0,len(self.buffer[self.cursor_y])-1)
                        if self.buffer[self.cursor_y]!="" and not check(self.cursor_x):
                            self.check_and_move(check,d,c,m)
                elif m:
                    self.cursor_x = 0
                else:
                    return False
        return True

    def inline_search(self,ch):
        self.check_and_move(lambda i: self.buffer[self.cursor_y][i]==ch, c=False, m=False)
    def inline_search_until(self,ch):
        if self.check_and_move(lambda i: self.buffer[self.cursor_y][i]==ch, c=False, m=False):
            self.move_cursor_left()
    def inline_search_backward(self,ch):
        self.check_and_move(lambda i: self.buffer[self.cursor_y][i]==ch, d="backward",c=False, m=False)
    def inline_search_backward_until(self,ch):
        if self.check_and_move(lambda i: self.buffer[self.cursor_y][i]==ch, d="backward",c=False, m=False):
            self.move_cursor_right()
    def move(self,num):
        if num == 'top':
            self.cursor_y = 0
            return
        if num == 'bottom':
            self.cursor_y = max(0,len(self.buffer)-1)
            return
        if num.isdigit():
            self.cursor_y = min(len(self.buffer)-1,max(0,int(num)))
            self.cursor_x = 0
# movement end


vim = VimEmulator()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            vim.handle_input(event)
    vim.update_cursor()
    vim.draw()
    pygame.display.flip()
    vim.clock.tick(FPS)

pygame.quit()
