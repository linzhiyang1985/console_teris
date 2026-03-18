import os
import time
import random
from collections import namedtuple

# 定义游戏常量
WIDTH = 10
HEIGHT = 20

# 定义方块形状
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

# 定义颜色（使用ANSI转义序列）
COLORS = [
    '\033[97m',  # 白色 - I
    '\033[93m',  # 黄色 - O
    '\033[95m',  # 紫色 - T
    '\033[91m',  # 红色 - L
    '\033[94m',  # 蓝色 - J
    '\033[92m',  # 绿色 - S
    '\033[96m'   # 青色 - Z
]
RESET_COLOR = '\033[0m'

# 定义位置
Point = namedtuple('Point', ['x', 'y'])

class Tetris:
    def __init__(self):
        self.board = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.score = 0
        self.level = 1
        self.game_over = False
        self.current_piece = None
        self.current_pos = None
        self.next_piece = None
        self.next_piece_color = None
        self.current_piece_color = None
        self.hold_piece = None
        self.hold_piece_color = None
        self.hold_used = False  # 标记是否已经使用过hold
        self.paused = False  # 标记游戏是否暂停
        self.drop_speed = 1.0  # 每秒下落一格
        self.last_drop_time = time.time()
        self.new_piece()
    
    def _get_random_piece(self):
        # 随机选择一个方块形状
        shape_idx = random.randint(0, len(SHAPES) - 1)
        # shape_idx = random.choice([0, 1])  # debug
        return SHAPES[shape_idx], COLORS[shape_idx]

    def new_piece(self):
        # 如果没有下一个方块，生成一个
        if self.next_piece is None:
            self.next_piece, self.next_piece_color = self._get_random_piece()
        
        # 设置当前方块为下一个方块
        self.current_piece = self.next_piece
        self.current_piece_color = self.next_piece_color
        
        # 生成新的下一个方块
        self.next_piece, self.next_piece_color = self._get_random_piece()
        
        # 设置当前方块的初始位置
        self.current_pos = Point(WIDTH // 2 - len(self.current_piece[0]) // 2, 0)

        # 随机旋转当前方块
        random_rotation = random.randint(0, 3)
        for _ in range(random_rotation):
            self.rotate_piece()
        
        # 检查游戏是否结束
        if not self.is_valid_position(self.current_piece, self.current_pos):
            self.game_over = True
    
    def is_valid_position(self, piece, pos):
        for y, row in enumerate(piece):
            for x, cell in enumerate(row):
                if cell:
                    new_x = pos.x + x
                    new_y = pos.y + y
                    if (new_x < 0 or new_x >= WIDTH or 
                        new_y >= HEIGHT or 
                        (new_y >= 0 and self.board[new_y][new_x] is not None)):
                        return False
        return True
    
    def rotate_piece(self):
        # 旋转方块
        rotated = list(zip(*reversed(self.current_piece)))
        rotated = [list(row) for row in rotated]
        
        if self.is_valid_position(rotated, self.current_pos):
            self.current_piece = rotated
    
    def move_left(self):
        new_pos = Point(self.current_pos.x - 1, self.current_pos.y)
        if self.is_valid_position(self.current_piece, new_pos):
            self.current_pos = new_pos
    
    def move_right(self):
        new_pos = Point(self.current_pos.x + 1, self.current_pos.y)
        if self.is_valid_position(self.current_piece, new_pos):
            self.current_pos = new_pos
    
    def move_down(self):
        new_pos = Point(self.current_pos.x, self.current_pos.y + 1)
        if self.is_valid_position(self.current_piece, new_pos):
            self.current_pos = new_pos
            return True
        else:
            self.lock_piece()
            return False
    
    def get_drop_position(self):
        # 计算方块的投影位置
        drop_pos = self.current_pos
        while True:
            new_pos = Point(drop_pos.x, drop_pos.y + 1)
            if not self.is_valid_position(self.current_piece, new_pos):
                break
            drop_pos = new_pos
        return drop_pos
    
    def hard_drop(self):
        old_pos = self.current_pos
        while self.move_down():
            pass
        new_pos = self.current_pos
        self.score += abs(old_pos.y - new_pos.y) * 2
    
    def hold(self):
        # 实现hold功能
        if self.hold_used:
            return
        
        if self.hold_piece is None:
            # 首次hold，暂存当前方块，调入next方块
            self.hold_piece = self.current_piece
            self.hold_piece_color = self.current_piece_color
            # 生成新的当前方块（使用next方块）
            self.current_piece = self.next_piece
            self.current_piece_color = self.next_piece_color
            # 生成新的next方块
            self.next_piece, self.next_piece_color = self._get_random_piece()
        else:
            # 已经有暂存方块，交换当前方块和暂存方块
            self.current_piece, self.hold_piece = self.hold_piece, self.current_piece
            self.current_piece_color, self.hold_piece_color = self.hold_piece_color, self.current_piece_color
        
        # 重置当前方块位置
        self.current_pos = Point(WIDTH // 2 - len(self.current_piece[0]) // 2, 0)
        
        # 标记已经使用过hold
        self.hold_used = True
        
        # 检查游戏是否结束
        if not self.is_valid_position(self.current_piece, self.current_pos):
            self.game_over = True
    
    def lock_piece(self):
        # 将当前方块锁定到游戏板上
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell:
                    board_y = self.current_pos.y + y
                    if board_y >= 0:
                        self.board[board_y][self.current_pos.x + x] = self.current_piece_color
        
        # 检查是否有可消除的行
        self.clear_lines()
        
        # 生成新方块
        self.hold_used = False  # 重置hold使用标记
        self.new_piece()
    
    def clear_lines(self):
        lines_cleared = 0
        new_board = []
        
        for row in self.board:
            if all(cell for cell in row):
                lines_cleared += 1
            else:
                new_board.append(row)
        
        # 在顶部添加新的空行
        while len(new_board) < HEIGHT:
            new_board.insert(0, [None for _ in range(WIDTH)])
        
        self.board = new_board
        
        # 更新分数和级别
        if lines_cleared > 0:
            self.score += lines_cleared * 100 * self.level
            # 每消除10行升级一次
            self.level = self.score // 1000 + 1
            # 提高下落速度
            self.drop_speed = max(0.1, 1.0 - (self.level - 1) * 0.1)
    
    def draw(self):
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 绘制游戏标题
        print("TETRIS")
        print(f"Score: {self.score}  Level: {self.level}")
        print()
        
        # 绘制hold方块
        print("Hold:")
        if self.hold_piece:
            for row in self.hold_piece:
                print('  ', end='')
                for cell in row:
                    if cell:
                        print(self.hold_piece_color + '#' + RESET_COLOR, end='')
                    else:
                        print(' ', end='')
                print()
        else:
            print('  --')
        print()
        
        # 计算投影位置
        drop_pos = self.get_drop_position()
        
        # 绘制游戏板
        print('+' + '-' * WIDTH + '+')
        for y in range(HEIGHT):
            print('|', end='')
            for x in range(WIDTH):
                # 检查当前位置是否有方块
                piece_in_cell = False
                for py, p_row in enumerate(self.current_piece):
                    for px, p_cell in enumerate(p_row):
                        if p_cell and self.current_pos.y + py == y and self.current_pos.x + px == x:
                            piece_in_cell = True
                            break
                    if piece_in_cell:
                        break
                
                # 检查是否是投影位置
                shadow_in_cell = False
                if not piece_in_cell and not self.board[y][x]:
                    for py, p_row in enumerate(self.current_piece):
                        for px, p_cell in enumerate(p_row):
                            if p_cell and drop_pos.y + py == y and drop_pos.x + px == x:
                                shadow_in_cell = True
                                break
                        if shadow_in_cell:
                            break
                
                if piece_in_cell:
                    print(self.current_piece_color + '#' + RESET_COLOR, end='')
                elif shadow_in_cell:
                    print(self.current_piece_color + 'o' + RESET_COLOR, end='')
                elif self.board[y][x] is not None:
                    print(self.board[y][x] + '■' + RESET_COLOR, end='')
                else:
                    print(' ', end='')
            print('|')
        print('+' + '-' * WIDTH + '+')
        
        # 绘制下一个方块
        print("Next piece:")
        for row in self.next_piece:
            print('  ', end='')
            for cell in row:
                if cell:
                    print(self.next_piece_color + '#' + RESET_COLOR, end='')
                else:
                    print(' ', end='')
            print()
        
        # 绘制操作说明
        print()
        print("Controls:")
        print("A: Move left")
        print("D: Move right")
        print("S: Move down")
        print("W: Rotate")
        print("Space: Hard drop")
        print("C/h: Hold piece")
        print("P/ESC: Pause; ENTER: Resume")
        print("Q: Quit")
    
    def get_key(self):
        # Get user input
        key = None
        accepted_keys_and_map = {
            b'w': 'w', b's': 's', b'a': 'a', b'd': 'd',
            b'W': 'w', b'S': 's', b'A': 'a', b'D': 'd',
            b'H': 'w', b'P': 's', b'K': 'a', b'M': 'd', # arrow keys
            b'q': 'q', b'c': 'c', b'p': 'p', b'h': 'c', # quit, hold, pause
            b'Q': 'q', b'C': 'c', b'P': 'p',
            b' ': ' ', # hard drop
            b'\r': 'ENTER', # resume
            b'\x1b': 'ESC'  # pause
        }
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\xe0', b'\x00'):
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    key = accepted_keys_and_map[key]
                else:
                    key = None
                return key
        except ImportError:
            # Unix系统
            import sys, tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch.lower()
        return None
    
    def run(self):
        while not self.game_over:
            # 绘制游戏
            self.draw()
            
            # 处理输入
            key = self.get_key()
            if key == 'a':
                self.move_left()
            elif key == 'd':
                self.move_right()
            elif key == 's':
                self.move_down()
                self.move_down()
                self.score += 4
                self.last_drop_time = time.time()
            elif key == 'w':
                self.rotate_piece()
            elif key == ' ':
                self.hard_drop()
            elif key == 'c':
                self.hold()
            elif key in ('p', 'ENTER', 'ESC'):
                if key == 'p':
                    self.paused = not self.paused
                elif key == 'ENTER' and self.paused:
                    self.paused = False
                elif key == 'ESC' and not self.paused:
                    self.paused = True
                # 暂停时显示暂停信息
                if self.paused:
                    self.draw()
                    print("PAUSED - Press P/ENTER to resume")
                    # 等待用户按P键恢复
                    while self.paused:
                        key = self.get_key()
                        if key == 'p' or key == 'ENTER':
                            self.paused = False
                        time.sleep(0.1)
            elif key == 'q':
                break
            
            # 自动下落（仅在未暂停时）
            if not self.paused:
                current_time = time.time()
                if current_time - self.last_drop_time > self.drop_speed:
                    self.move_down()
                    self.last_drop_time = current_time
            
            # 小延迟，避免游戏过快
            time.sleep(0.05)
        
        # 游戏结束
        self.draw()
        print("Game Over!")
        print(f"Final Score: {self.score}")

if __name__ == "__main__":
    game = Tetris()
    game.run()
