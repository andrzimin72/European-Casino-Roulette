#!/usr/bin/env python3

import tkinter as tk
from tkinter import messagebox
import random
import math
from collections import deque, defaultdict

# ======================
# CORE GAME ENGINE
# ======================

class RouletteEngine:
    RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    BLACK = set(range(1, 37)) - RED

    PAYOUTS = {
        'straight': 35, 'split': 17, 'street': 11, 'trio': 11,
        'corner': 8, 'line': 5,
        'red': 1, 'black': 1, 'even': 1, 'odd': 1, 'low': 1, 'high': 1,
        'dozen_1': 2, 'dozen_2': 2, 'dozen_3': 2,
        'column_1': 2, 'column_2': 2, 'column_3': 2
    }

    WHEEL_NUMBERS = [
        0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
        5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
    ]

    @staticmethod
    def spin() -> int:
        return random.randint(0, 36)

    @staticmethod
    def resolve(bet_type: str, number: int) -> bool:
        parts = bet_type.split('_')
        base = parts[0]
        if base == 'straight':
            return number == int(parts[1])
        if base == 'split':
            return number in (int(parts[1]), int(parts[2]))
        if base in ('street', 'trio'):
            return number in tuple(map(int, parts[1:]))
        if base == 'corner':
            return number in tuple(map(int, parts[1:]))
        if base == 'line':
            return number in tuple(map(int, parts[1:]))
        if base == 'red': return number in RouletteEngine.RED
        if base == 'black': return number in RouletteEngine.BLACK
        if base == 'even': return number != 0 and number % 2 == 0
        if base == 'odd': return number != 0 and number % 2 == 1
        if base == 'low': return 1 <= number <= 18
        if base == 'high': return 19 <= number <= 36
        if base == 'dozen_1': return 1 <= number <= 12
        if base == 'dozen_2': return 13 <= number <= 24
        if base == 'dozen_3': return 25 <= number <= 36
        if base == 'column_1': return number != 0 and number % 3 == 1
        if base == 'column_2': return number != 0 and number % 3 == 2
        if base == 'column_3': return number != 0 and number % 3 == 0
        return False

    @staticmethod
    def get_payout(bet_type: str) -> int:
        return RouletteEngine.PAYOUTS.get(bet_type.split('_')[0], 0)

# ======================
# CALL BETS
# ======================

CALL_BETS = {
    'voisins': [('trio_0_2_3', 2), ('split_4_7', 1), ('split_12_15', 1), ('split_18_21', 1),
                ('split_19_22', 1), ('corner_25_26_28_29', 1), ('split_32_35', 1)],
    'tiers': [('split_5_8', 1), ('split_10_11', 1), ('split_13_16', 1), ('split_23_24', 1),
              ('split_27_30', 1), ('split_33_36', 1)],
    'red_splits': [('split_9_12', 1), ('split_16_19', 1), ('split_18_21', 1), ('split_27_30', 1)],
    'black_splits': [('split_8_11', 1), ('split_10_11', 1), ('split_10_13', 1), ('split_17_20', 1),
                     ('split_26_29', 1), ('split_28_29', 1), ('split_28_31', 1)]
}

# ======================
# MAIN GUI CLASS
# ======================

class RouletteCanvasGUI:
    CHIP_VALUES = [1, 5, 10, 25, 100, 500]
    CHIP_COLORS = {
        1: '#f44336',    # Red
        5: '#4caf50',    # Green
        10: '#2196f3',   # Blue
        25: '#ff9800',   # Orange
        100: '#9c27b0',  # Purple
        500: '#ffeb3b'   # Yellow
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("European Roulette – Ultimate Edition")
        self.root.geometry("1400x1000")
        self.root.configure(bg='#0d1b2a')
        self.root.resizable(True, True)

        self.balance = 1000.0
        self.starting_balance = self.balance
        self.total_bet = 0.0
        self.current_bets = defaultdict(float)
        self.last_bets = {}
        self.selected_chip = 1
        self.spinning = False
        self.wheel_angle = 0
        self.ball_angle = 0
        self.ball_radius = 200

        self.anim_duration = 3000
        self.target_outcome = 0

        # Statistics
        self.total_spins = 0
        self.wins = 0
        self.losses = 0
        self.bet_frequency = defaultdict(int)

        self.history = deque(maxlen=15)
        self.bet_zones = {}
        self.outside_bet_positions = {}

        self.create_widgets()

    def create_widgets(self):
        # Top info bar
        top = tk.Frame(self.root, bg='#1b263b', relief='raised', bd=2)
        top.pack(fill='x', padx=10, pady=5)
        self.balance_label = tk.Label(top, text=f"Balance: ${self.balance:.2f}",
                                      font=('Helvetica', 14, 'bold'), fg='gold', bg='#1b263b')
        self.balance_label.pack(side='left', padx=10)
        self.total_bet_label = tk.Label(top, text=f"Total Bet: ${self.total_bet:.2f}",
                                        font=('Helvetica', 12), fg='white', bg='#1b263b')
        self.total_bet_label.pack(side='right', padx=10)

        # Chip selector
        chip_frame = tk.Frame(self.root, bg='#0d1b2a')
        chip_frame.pack(pady=8)
        tk.Label(chip_frame, text="Select Chip:", font=('Helvetica', 12), fg='white', bg='#0d1b2a').pack(side='left', padx=5)
        for val in self.CHIP_VALUES:
            btn = tk.Button(chip_frame, text=str(val), width=4, bg=self.CHIP_COLORS[val], fg='white',
                            font=('Helvetica', 10, 'bold'),
                            command=lambda v=val: self.select_chip(v))
            btn.pack(side='left', padx=3)
        self.chip_indicator = tk.Label(chip_frame, text=f"Selected: {self.selected_chip}",
                                       bg='gold', fg='black', font=('Helvetica', 10, 'bold'), width=14)
        self.chip_indicator.pack(side='left', padx=15)

        # Main play area
        main_frame = tk.Frame(self.root, bg='#0d1b2a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Wheel
        self.wheel_canvas = tk.Canvas(main_frame, bg='#0d1b2a', highlightthickness=0, relief='sunken', bd=3)
        self.wheel_canvas.pack(side='left', fill='both', expand=True, padx=5)
        self.wheel_canvas.bind("<Configure>", lambda e: self.draw_wheel())

        # Betting table
        self.table_canvas = tk.Canvas(main_frame, bg='#0a4d2e', highlightthickness=0, relief='sunken', bd=3)
        self.table_canvas.pack(side='left', fill='both', expand=True, padx=5)
        self.table_canvas.bind("<Configure>", lambda e: self.draw_table())
        self.table_canvas.bind("<Button-1>", self.on_table_click)

        # Right panel
        right_frame = tk.Frame(main_frame, bg='#0d1b2a')
        right_frame.pack(side='right', fill='y', padx=5)

        # Racetrack
        racetrack = tk.LabelFrame(right_frame, text="Call Bets", font=('Helvetica', 11, 'bold'),
                                  fg='gold', bg='#1b263b', labelanchor='n')
        racetrack.pack(fill='x', padx=5, pady=5)
        for name in ['voisins', 'tiers', 'red_splits', 'black_splits']:
            tk.Button(racetrack, text=name.replace('_', ' ').title(), width=15, bg='#415a77', fg='white',
                      command=lambda n=name: self.place_call_bet(n)).pack(pady=3)
        tk.Label(racetrack, text="Neighbours (0-36):", fg='white', bg='#1b263b').pack(pady=(12,2))
        self.neigh_entry = tk.Entry(racetrack, width=8, justify='center')
        self.neigh_entry.pack()
        tk.Button(racetrack, text="Bet", bg='#e0e1dd', command=self.place_neighbours).pack(pady=5)

        # History
        history_frame = tk.LabelFrame(right_frame, text="Last Spins", font=('Helvetica', 11, 'bold'),
                                      fg='gold', bg='#1b263b')
        history_frame.pack(fill='both', expand=True, padx=5, pady=10)
        self.history_canvas = tk.Canvas(history_frame, bg='#1b263b', height=120, highlightthickness=0)
        self.history_canvas.pack(fill='both', expand=True)

        # Controls
        ctrl = tk.Frame(self.root, bg='#0d1b2a')
        ctrl.pack(pady=10)
        tk.Button(ctrl, text="CLEAR BET", bg='#ff6b6b', fg='white', font=('Helvetica', 10, 'bold'),
                  command=self.clear_bet).pack(side='left', padx=6)
        tk.Button(ctrl, text="NEW BETS", bg='#4ecdc4', fg='white', font=('Helvetica', 10, 'bold'),
                  command=self.new_bets).pack(side='left', padx=6)
        tk.Button(ctrl, text="REBET", bg='#ffd166', fg='black', font=('Helvetica', 10, 'bold'),
                  command=self.rebet).pack(side='left', padx=6)
        self.spin_btn = tk.Button(ctrl, text="SPIN", bg='#06d6a0', fg='white', font=('Helvetica', 12, 'bold'),
                                  width=16, height=2, command=self.start_spin)
        self.spin_btn.pack(side='left', padx=15)

        # Log
        self.log = tk.Text(self.root, height=4, state='disabled', bg='#1b263b', fg='lightgray',
                           font=('Courier', 10), relief='sunken')
        self.log.pack(fill='x', padx=10, pady=5)

        # Statistics (initial)
        self.update_statistics()

        self.root.after(200, self.draw_wheel)
        self.root.after(200, self.draw_table)

    def log_msg(self, msg):
        self.log.config(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def select_chip(self, val):
        self.selected_chip = val
        self.chip_indicator.config(text=f"Selected: {val}", bg=self.CHIP_COLORS[val], fg='white')

    # ======================
    # WHEEL ANIMATION
    # ======================

    def ease_out_expo(self, t):
        return 1.0 if t >= 1.0 else 1.0 - pow(2, -10 * t)

    def animate_wheel_smooth(self, elapsed=0):
        if not self.spinning:
            return

        t = min(elapsed / self.anim_duration, 1.0)
        progress = self.ease_out_expo(t)

        base_rotations = 8
        target_wheel_deg = (RouletteEngine.WHEEL_NUMBERS.index(self.target_outcome) * (360 / 37))
        total_wheel_angle = base_rotations * 360 + target_wheel_deg
        self.wheel_angle = progress * total_wheel_angle

        self.ball_radius = 200 - 20 * progress
        total_ball_rot = base_rotations * 720 + (360 - target_wheel_deg)
        self.ball_angle = (progress * total_ball_rot) % 360

        self.draw_wheel()

        if t < 1.0:
            self.root.after(16, lambda: self.animate_wheel_smooth(elapsed + 16))
        else:
            self.spinning = False
            self.spin_btn.config(state='normal', bg='#06d6a0')
            self.resolve_bets(self.target_outcome)

    def start_spin(self):
        if self.total_bet == 0:
            messagebox.showwarning("No Bet", "Place a bet first!")
            return
        if self.spinning:
            return
        self.spinning = True
        self.spin_btn.config(state='disabled', bg='#6c757d')
        self.target_outcome = RouletteEngine.spin()
        self.log_msg(f"Spinning... targeting {self.target_outcome}")
        self.animate_wheel_smooth()

    def draw_wheel(self):
        canvas = self.wheel_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 50 or h < 50:
            w, h = 500, 500
        cx, cy = w // 2, h // 2
        outer_r = min(cx, cy) - 10
        if outer_r < 50:
            outer_r = 200

        canvas.create_oval(cx-outer_r, cy-outer_r, cx+outer_r, cy+outer_r, fill='#2b2b2b', outline='#555', width=2)
        canvas.create_oval(cx-outer_r+10, cy-outer_r+10, cx+outer_r-10, cy+outer_r-10, fill='#121212', outline='')

        segment_angle = 360 / 37
        for i, num in enumerate(RouletteEngine.WHEEL_NUMBERS):
            start = 360 - (i + 1) * segment_angle - (self.wheel_angle % 360)
            color = 'green' if num == 0 else ('#d32f2f' if num in RouletteEngine.RED else '#212121')
            canvas.create_arc(cx-outer_r, cy-outer_r, cx+outer_r, cy+outer_r,
                              start=start, extent=segment_angle,
                              fill=color, outline='#333', width=1)
            if num != 0:
                highlight_color = '#ff6b6b' if num in RouletteEngine.RED else '#4a4a4a'
                inner_r = outer_r - 15
                canvas.create_arc(cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r,
                                  start=start, extent=segment_angle,
                                  fill='', outline=highlight_color, width=2)
            mid_deg = start + segment_angle / 2
            rad = math.radians(mid_deg)
            tx = cx + (outer_r - 40) * math.cos(rad)
            ty = cy + (outer_r - 40) * math.sin(rad)
            text_color = 'white' if num != 0 else 'gold'
            canvas.create_text(tx, ty, text=str(num), fill=text_color, font=('Helvetica', 10, 'bold'))

        # Ball
        ball_deg = self.ball_angle % 360
        ball_rad = math.radians(ball_deg)
        br = max(180, self.ball_radius)
        bx = cx + br * math.cos(ball_rad)
        by = cy + br * math.sin(ball_rad)
        canvas.create_oval(bx-10, by-10, bx+10, by+10, fill='#333', outline='')
        canvas.create_oval(bx-8, by-8, bx+8, by+8, fill='#f8f9fa', outline='#555')
        canvas.create_oval(bx-5, by-6, bx-1, by-2, fill='white', outline='')

    # ======================
    # WIN ANIMATIONS
    # ======================

    def animate_win_flash(self, outcome, step=0):
        if step >= 6:
            self.draw_wheel()
            return

        segment_index = RouletteEngine.WHEEL_NUMBERS.index(outcome)
        original_angle = self.wheel_angle
        self.wheel_angle = original_angle + (5 if step % 2 == 0 else -5)
        self.draw_wheel()

        canvas = self.wheel_canvas
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 50: w, h = 500, 500
        cx, cy = w // 2, h // 2
        outer_r = min(cx, cy) - 10
        segment_angle = 360 / 37
        start_deg = 360 - (segment_index + 1) * segment_angle - (self.wheel_angle % 360)
        canvas.create_arc(cx-outer_r, cy-outer_r, cx+outer_r, cy+outer_r,
                          start=start_deg, extent=segment_angle,
                          fill='gold', outline='white', width=2)

        if step % 2 == 0:
            self.draw_sparkles(cx, cy, outer_r - 30)

        self.root.after(150, lambda: self.animate_win_flash(outcome, step + 1))

    def draw_sparkles(self, cx, cy, r):
        for _ in range(8):
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            dist = r + random.uniform(-20, 20)
            x = cx + dist * math.cos(rad)
            y = cy + dist * math.sin(rad)
            size = random.randint(3, 6)
            color = random.choice(['gold', 'white', '#ffeb3b'])
            self.wheel_canvas.create_oval(x-size, y-size, x+size, y+size,
                                          fill=color, outline='', tags="sparkle")
        self.root.after(400, lambda: self.wheel_canvas.delete("sparkle"))

    # ======================
    # TABLE & CHIPS
    # ======================

    def draw_table(self):
        canvas = self.table_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = 800, 500

        start_x, start_y = 60, 60
        cell_w, cell_h = 45, 45
        self.bet_zones.clear()
        self.outside_bet_positions.clear()

        for col in range(12):
            for row in range(3):
                num = col * 3 + row + 1
                if num > 36: break
                x1 = start_x + col * cell_w
                y1 = start_y + row * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                color = '#d32f2f' if num in RouletteEngine.RED else '#212121'
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='white', width=1)
                canvas.create_text((x1+x2)//2, (y1+y2)//2, text=str(num), fill='white', font=('Helvetica', 10, 'bold'))
                self.bet_zones[(x1, y1, x2, y2)] = f'straight_{num}'

        zx1, zy1 = start_x + 12 * cell_w + 10, start_y
        zx2, zy2 = zx1 + cell_w, zy1 + 3 * cell_h
        canvas.create_rectangle(zx1, zy1, zx2, zy2, fill='green', outline='white', width=1)
        canvas.create_text((zx1+zx2)//2, (zy1+zy2)//2, text='0', fill='white', font=('Helvetica', 12, 'bold'))
        self.bet_zones[(zx1, zy1, zx2, zy2)] = 'straight_0'

        out_y = start_y + 3 * cell_h + 25
        outside_bets = [
            ('1st 12', 'dozen_1', 0),
            ('2nd 12', 'dozen_2', 1),
            ('3rd 12', 'dozen_3', 2),
            ('1-18', 'low', 3),
            ('EVEN', 'even', 4),
            ('RED', 'red', 5),
            ('BLACK', 'black', 6),
            ('ODD', 'odd', 7),
            ('19-36', 'high', 8),
        ]
        for label, bet_type, col in outside_bets:
            x1 = start_x + int(col * (cell_w * 1.35))
            x2 = x1 + int(cell_w * 1.2)
            y1, y2 = out_y, out_y + 35
            canvas.create_rectangle(x1, y1, x2, y2, fill='#4a5568', outline='white')
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=label, fill='white', font=('Helvetica', 8))
            self.bet_zones[(x1, y1, x2, y2)] = bet_type
            self.outside_bet_positions[bet_type] = ((x1+x2)//2, (y1+y2)//2)

        col_y = start_y - 45
        for i in range(3):
            x1 = start_x + i * cell_w * 4
            x2 = x1 + cell_w * 4 - 2
            y1, y2 = col_y, col_y + 32
            canvas.create_rectangle(x1, y1, x2, y2, fill='#4a5568', outline='white')
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text='2:1', fill='white', font=('Helvetica', 9))
            bet_type = f'column_{i+1}'
            self.bet_zones[(x1, y1, x2, y2)] = bet_type
            self.outside_bet_positions[bet_type] = ((x1+x2)//2, (y1+y2)//2)

        self.draw_all_chips(canvas)

    def _break_into_chips(self, amount):
        chips = []
        remaining = int(round(amount))
        for val in sorted(self.CHIP_VALUES, reverse=True):
            while remaining >= val:
                chips.append(val)
                remaining -= val
        while remaining > 0:
            chips.append(1)
            remaining -= 1
        return chips

    def draw_all_chips(self, canvas):
        start_x, start_y = 60, 60
        cell_w, cell_h = 45, 45

        for bet_type, total in self.current_bets.items():
            if total <= 0: continue
            cx, cy = None, None

            if bet_type.startswith('straight_'):
                num = int(bet_type.split('_')[1])
                if num == 0:
                    cx = start_x + 12 * cell_w + 10 + cell_w // 2
                    cy = start_y + (3 * cell_h) // 2
                else:
                    col = (num - 1) // 3
                    row = (num - 1) % 3
                    cx = start_x + col * cell_w + cell_w // 2
                    cy = start_y + row * cell_h + cell_h // 2
            elif bet_type in self.outside_bet_positions:
                cx, cy = self.outside_bet_positions[bet_type]
            else:
                continue

            chip_list = self._break_into_chips(total)
            base_y = cy + 18
            for i, chip_val in enumerate(chip_list):
                y_offset = base_y - i * 9
                color = self.CHIP_COLORS.get(chip_val, '#777')
                canvas.create_oval(cx - 10, y_offset - 10, cx + 10, y_offset + 10,
                                   fill=color, outline='black', width=1)
                canvas.create_text(cx, y_offset, text=str(chip_val),
                                   fill='white', font=('Helvetica', 6, 'bold'))

    def on_table_click(self, event):
        if self.spinning: return
        x, y = event.x, event.y
        for (x1, y1, x2, y2), bet_type in self.bet_zones.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.add_bet(bet_type)
                return

    # ======================
    # BETTING LOGIC
    # ======================

    def add_bet(self, bet_type):
        if self.balance < self.selected_chip:
            messagebox.showwarning("Funds", "Insufficient balance.")
            return
        self.current_bets[bet_type] += self.selected_chip
        self.total_bet += self.selected_chip
        self.balance -= self.selected_chip
        # Track frequency for stats
        if bet_type.startswith('straight_'):
            num = int(bet_type.split('_')[1])
            self.bet_frequency[num] += 1
        self.update_ui()
        self.log_msg(f"Bet ${self.selected_chip} on {bet_type}")
        self.draw_table()

    def place_call_bet(self, name):
        if name not in CALL_BETS:
            return
        total = sum(chips * self.selected_chip for _, chips in CALL_BETS[name])
        if self.balance < total:
            messagebox.showwarning("Funds", "Not enough for this call bet.")
            return
        for sub_bet, cnt in CALL_BETS[name]:
            amt = cnt * self.selected_chip
            self.current_bets[sub_bet] += amt
            self.total_bet += amt
            self.balance -= amt
            # Track straight parts if any
            if sub_bet.startswith('straight_'):
                num = int(sub_bet.split('_')[1])
                self.bet_frequency[num] += cnt
        self.update_ui()
        self.log_msg(f"Placed call bet: {name}")
        self.draw_table()

    def place_neighbours(self):
        try:
            num = int(self.neigh_entry.get())
            if not (0 <= num <= 36):
                raise ValueError
        except ValueError:
            messagebox.showerror("Input", "Enter 0–36")
            return
        for offset in (-2, -1, 0, 1, 2):
            n = (num + offset) % 37
            self.add_bet(f'straight_{n}')

    def update_ui(self):
        self.balance_label.config(text=f"Balance: ${self.balance:.2f}")
        self.total_bet_label.config(text=f"Total Bet: ${self.total_bet:.2f}")

    def clear_bet(self):
        for amt in self.current_bets.values():
            self.balance += amt
        self.total_bet = 0
        self.current_bets.clear()
        self.update_ui()
        self.log_msg("Cleared bets.")
        self.draw_table()

    def new_bets(self):
        self.clear_bet()
        self.log_msg("New round started.")

    def rebet(self):
        if not self.last_bets:
            messagebox.showinfo("Info", "No previous bet.")
            return
        total = sum(self.last_bets.values())
        if self.balance < total:
            messagebox.showwarning("Funds", "Not enough to rebet.")
            return
        self.clear_bet()
        self.current_bets = self.last_bets.copy()
        self.total_bet = total
        self.balance -= total
        # Re-track frequency
        for bet_type, amt in self.last_bets.items():
            if bet_type.startswith('straight_'):
                num = int(bet_type.split('_')[1])
                self.bet_frequency[num] += int(amt // min(self.CHIP_VALUES))
        self.update_ui()
        self.log_msg("Rebet placed.")
        self.draw_table()

    # ======================
    # RESOLVE & STATISTICS
    # ======================

    def resolve_bets(self, outcome):
        self.history.appendleft(outcome)
        self.draw_history()
        self.total_spins += 1

        self.log_msg(f"Ball landed on: {outcome}")
        total_return = 0.0
        win_count = 0

        for bet_type, amount in self.current_bets.items():
            if RouletteEngine.resolve(bet_type, outcome):
                payout = RouletteEngine.get_payout(bet_type)
                win = amount * (payout + 1)
                total_return += win
                win_count += 1
                self.log_msg(f"✅ Win on {bet_type}: +${win:.2f}")

        if win_count > 0:
            self.wins += 1
            self.animate_win_flash(outcome)
        else:
            self.losses += 1

        self.balance += total_return
        self.last_bets = self.current_bets.copy()
        self.total_bet = 0
        self.current_bets.clear()
        self.update_ui()
        self.update_statistics()
        self.log_msg(f"Balance: ${self.balance:.2f}\n{'─' * 50}")
        self.draw_table()

    def update_statistics(self):
        win_rate = self.wins / max(self.total_spins, 1) * 100
        profit = self.balance - self.starting_balance
        stats_text = (
            f"Spins: {self.total_spins} | Wins: {self.wins} | Losses: {self.losses}\n"
            f"Win Rate: {win_rate:.1f}% | Profit: ${profit:.2f}\n"
        )
        if self.bet_frequency:
            most_bet_num = max(self.bet_frequency, key=self.bet_frequency.get)
            stats_text += f"Your #1 Bet: {most_bet_num} ({self.bet_frequency[most_bet_num]}x)"
        else:
            stats_text += "Your #1 Bet: —"

        if not hasattr(self, 'stats_label'):
            self.stats_label = tk.Label(self.root, text=stats_text, font=('Helvetica', 10),
                                        bg='#1b263b', fg='lightblue', justify='left',
                                        relief='ridge', padx=10, pady=5)
            self.stats_label.pack(pady=5, padx=10, fill='x')
        else:
            self.stats_label.config(text=stats_text)

    def draw_history(self):
        canvas = self.history_canvas
        canvas.delete("all")
        w = canvas.winfo_width() or 200
        h = 120
        radius = 15
        spacing = 25
        start_y = h // 2

        for i, num in enumerate(self.history):
            x = 15 + i * spacing
            if x + radius > w - 10:
                break
            color = 'green' if num == 0 else ('red' if num in RouletteEngine.RED else 'black')
            text_color = 'white' if num != 0 else 'gold'
            canvas.create_oval(x - radius, start_y - radius, x + radius, start_y + radius,
                               fill=color, outline='white', width=1)
            canvas.create_text(x, start_y, text=str(num), fill=text_color, font=('Helvetica', 9, 'bold'))

# ======================
# RUN
# ======================

if __name__ == '__main__':
    root = tk.Tk()
    app = RouletteCanvasGUI(root)
    root.mainloop()
