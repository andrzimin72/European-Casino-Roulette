# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from collections import defaultdict, deque
import random
import math

# Local modules
from roulette_engine import RouletteEngine, CALL_BETS
from widgets.table import BettingTable
from widgets.wheel import RouletteWheel

# Set background
Window.clearcolor = (0.05, 0.1, 0.16, 1)  # #0d1b2a

CHIP_VALUES = [1, 5, 10, 25, 100, 500]
CHIP_COLORS_HEX = {
    1: '#f44336',    # Red
    5: '#4caf50',    # Green
    10: '#2196f3',   # Blue
    25: '#ff9800',   # Orange
    100: '#9c27b0',  # Purple
    500: '#ffeb3b'   # Yellow
}

# Convert HEX to RGBA (0–1)
def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))
    return (*rgb, alpha)

CHIP_COLORS_RGBA = {k: hex_to_rgba(v) for k, v in CHIP_COLORS_HEX.items()}

class ColoredBoxLayout(BoxLayout):
    def __init__(self, color=(0.1, 0.15, 0.23, 1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class RouletteApp(App):
    def build(self):
        self.title = "European Roulette – Kivy Edition"
        # Game state
        self.balance = 1000.0
        self.starting_balance = self.balance
        self.total_bet = 0.0
        self.current_bets = defaultdict(float)
        self.last_bets = {}
        self.selected_chip = 1
        self.spinning = False
        self.CHIP_COLORS_RGBA = CHIP_COLORS_RGBA

        # Stats
        self.total_spins = 0
        self.wins = 0
        self.losses = 0
        self.bet_frequency = defaultdict(int)
        self.history = deque(maxlen=15)

        # Root layout
        root = ColoredBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Top bar
        top_bar = ColoredBoxLayout(size_hint_y=None, height=dp(40), color=(0.106, 0.149, 0.231, 1))
        self.balance_label = Label(text=f"Balance: ${self.balance:.2f}", color=(1, 0.8, 0, 1), font_size=dp(14))
        self.total_bet_label = Label(text=f"Total Bet: ${self.total_bet:.2f}", color=(1, 1, 1, 1), font_size=dp(12))
        top_bar.add_widget(self.balance_label)
        top_bar.add_widget(Label())  # spacer
        top_bar.add_widget(self.total_bet_label)
        root.add_widget(top_bar)

        # Chip selector
        chip_frame = ColoredBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        chip_frame.add_widget(Label(text="Select Chip:", color=(1, 1, 1, 1), size_hint_x=None, width=dp(80)))
        for val in CHIP_VALUES:
            btn = Button(text=str(val), size_hint_x=None, width=dp(50),
                         background_color=CHIP_COLORS_RGBA[val])
            btn.bind(on_press=lambda inst, v=val: self.select_chip(v))
            chip_frame.add_widget(btn)
        self.chip_indicator = Label(text=f"Selected: {self.selected_chip}", size_hint_x=None, width=dp(120),
                                    color=(0, 0, 0, 1), font_size=dp(12))
        with self.chip_indicator.canvas.before:
            Color(1, 1, 0)  # gold bg
            self.chip_bg = Rectangle(size=self.chip_indicator.size, pos=self.chip_indicator.pos)
        self.chip_indicator.bind(size=self._update_chip_bg, pos=self._update_chip_bg)
        chip_frame.add_widget(self.chip_indicator)
        root.add_widget(chip_frame)

        # Main area: Wheel + Table + Side panel
        main_area = BoxLayout(spacing=dp(8))

        # Wheel
        self.wheel_widget = RouletteWheel(self, size_hint_x=0.6)
        main_area.add_widget(self.wheel_widget)

        # Betting table
        self.table_widget = BettingTable(self, size_hint_x=0.6, size_hint_y=0.8)
        table_container = ColoredBoxLayout(color=(0.04, 0.3, 0.18, 1), padding=dp(5))
        table_container.add_widget(self.table_widget)
        main_area.add_widget(table_container)

        # Side panel
        side_panel = ColoredBoxLayout(orientation='vertical', size_hint_x=0.25, spacing=dp(8), padding=dp(5),
                                      color=(0.106, 0.149, 0.231, 1))

        # Call bets
        call_bets = ColoredBoxLayout(orientation='vertical', size_hint_y=None, height=dp(180), padding=dp(5))
        call_bets.add_widget(Label(text="Call Bets", color=(1, 0.843, 0, 1), size_hint_y=None, height=dp(25), font_size=dp(12)))
        for name in CALL_BETS:
            btn = Button(text=name.replace('_', ' ').title(), size_hint_y=None, height=dp(35),
                         background_color=(0.263, 0.353, 0.467, 1), color=(1, 1, 1, 1))
            btn.bind(on_press=lambda inst, n=name: self.place_call_bet(n))
            call_bets.add_widget(btn)
        side_panel.add_widget(call_bets)

        # Neighbour input
        neigh_panel = ColoredBoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(5))
        neigh_panel.add_widget(Label(text="Neighbours (0-36):", color=(1, 1, 1, 1), font_size=dp(12)))
        self.neigh_entry = TextInput(multiline=False, input_filter='int', size_hint_y=None, height=dp(30), halign='center')
        neigh_btn = Button(text="Bet Neighbours", size_hint_y=None, height=dp(35), background_color=(0.878, 0.882, 0.867, 1))
        neigh_btn.bind(on_press=self.place_neighbours)
        neigh_panel.add_widget(self.neigh_entry)
        neigh_panel.add_widget(neigh_btn)
        side_panel.add_widget(neigh_panel)

        # History
        history_label = Label(text="Last Spins", color=(1, 0.843, 0, 1), size_hint_y=None, height=dp(25), font_size=dp(12))
        self.history_view = Label(text="", valign='middle', halign='left', color=(1, 1, 1, 1), font_size=dp(14))
        self.history_view.bind(size=self.history_view.setter('text_size'))
        history_scroll = ScrollView(size_hint_y=0.4)
        history_scroll.add_widget(self.history_view)
        side_panel.add_widget(history_label)
        side_panel.add_widget(history_scroll)

        main_area.add_widget(side_panel)
        root.add_widget(main_area)

        # Control buttons
        ctrl = ColoredBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.clear_btn = Button(text="CLEAR BET", background_color=(1, 0.42, 0.42, 1), color=(1, 1, 1, 1))
        self.new_btn = Button(text="NEW BETS", background_color=(0.306, 0.804, 0.769, 1), color=(1, 1, 1, 1))
        self.rebet_btn = Button(text="REBET", background_color=(1, 0.82, 0.22, 1), color=(0, 0, 0, 1))
        self.spin_btn = Button(text="SPIN", size_hint_x=0.3, background_color=(0.024, 0.839, 0.627, 1), color=(1, 1, 1, 1), font_size=dp(16))
        self.clear_btn.bind(on_press=self.clear_bet)
        self.new_btn.bind(on_press=self.new_bets)
        self.rebet_btn.bind(on_press=self.rebet)
        self.spin_btn.bind(on_press=self.start_spin)
        ctrl.add_widget(self.clear_btn)
        ctrl.add_widget(self.new_btn)
        ctrl.add_widget(self.rebet_btn)
        ctrl.add_widget(self.spin_btn)
        root.add_widget(ctrl)

        # Log
        self.log_view = Label(text="Welcome to European Roulette!", valign='top', halign='left',
                              color=(0.8, 0.8, 0.8, 1), font_size=dp(12))
        self.log_view.bind(size=self.log_view.setter('text_size'))
        log_scroll = ScrollView(size_hint_y=0.15)
        log_scroll.add_widget(self.log_view)
        root.add_widget(log_scroll)

        # Stats label (updated after spins)
        self.stats_label = Label(text="", size_hint_y=None, height=dp(40), color=(0.678, 0.867, 1, 1), font_size=dp(12))
        root.add_widget(self.stats_label)

        Clock.schedule_once(lambda dt: self.update_statistics(), 0.5)
        return root

    def _update_chip_bg(self, instance, value):
        self.chip_bg.pos = instance.pos
        self.chip_bg.size = instance.size

    def log_msg(self, msg):
        self.log_view.text += '\n' + msg
        self.log_view.text = self.log_view.text[-1000:]  # limit length

    def select_chip(self, val):
        self.selected_chip = val
        self.chip_indicator.text = f"Selected: {val}"
        # Update indicator bg
        with self.chip_indicator.canvas.before:
            Color(*CHIP_COLORS_RGBA[val])
            self.chip_bg = Rectangle(size=self.chip_indicator.size, pos=self.chip_indicator.pos)

    def _break_into_chips(self, amount):
        chips = []
        remaining = int(round(amount))
        for val in sorted(CHIP_VALUES, reverse=True):
            while remaining >= val:
                chips.append(val)
                remaining -= val
        while remaining > 0:
            chips.append(1)
            remaining -= 1
        return chips

    def add_bet(self, bet_type):
        if self.balance < self.selected_chip:
            self.log_msg("⚠️ Insufficient balance.")
            return
        if self.spinning:
            return
        self.current_bets[bet_type] += self.selected_chip
        self.total_bet += self.selected_chip
        self.balance -= self.selected_chip
        if bet_type.startswith('straight_'):
            num = int(bet_type.split('_')[1])
            self.bet_frequency[num] += 1
        self.update_ui()
        self.log_msg(f"Placed ${self.selected_chip} on {bet_type}")
        self.table_widget.redraw()

    def place_call_bet(self, name):
        if name not in CALL_BETS:
            return
        total = sum(chips * self.selected_chip for _, chips in CALL_BETS[name])
        if self.balance < total:
            self.log_msg("⚠️ Not enough for this call bet.")
            return
        for sub_bet, cnt in CALL_BETS[name]:
            amt = cnt * self.selected_chip
            self.current_bets[sub_bet] += amt
            self.total_bet += amt
            self.balance -= amt
            if sub_bet.startswith('straight_'):
                num = int(sub_bet.split('_')[1])
                self.bet_frequency[num] += cnt
        self.update_ui()
        self.log_msg(f"Placed call bet: {name}")
        self.table_widget.redraw()

    def place_neighbours(self, *args):
        try:
            num = int(self.neigh_entry.text.strip())
            if not (0 <= num <= 36):
                raise ValueError
        except (ValueError, AttributeError):
            self.log_msg("⚠️ Enter number 0–36.")
            return
        for offset in (-2, -1, 0, 1, 2):
            n = (num + offset) % 37
            self.add_bet(f'straight_{n}')
        self.neigh_entry.text = ""

    def update_ui(self):
        self.balance_label.text = f"Balance: ${self.balance:.2f}"
        self.total_bet_label.text = f"Total Bet: ${self.total_bet:.2f}"

    def clear_bet(self, *args):
        for amt in self.current_bets.values():
            self.balance += amt
        self.total_bet = 0
        self.current_bets.clear()
        self.update_ui()
        self.log_msg("Cleared all bets.")
        self.table_widget.redraw()

    def new_bets(self, *args):
        self.clear_bet()
        self.log_msg("New round started.")

    def rebet(self, *args):
        if not self.last_bets:
            self.log_msg("ℹ️ No previous bet to rebet.")
            return
        total = sum(self.last_bets.values())
        if self.balance < total:
            self.log_msg("⚠️ Not enough to rebet.")
            return
        self.clear_bet()
        self.current_bets = self.last_bets.copy()
        self.total_bet = total
        self.balance -= total
        for bet_type, amt in self.last_bets.items():
            if bet_type.startswith('straight_'):
                num = int(bet_type.split('_')[1])
                self.bet_frequency[num] += int(amt // min(CHIP_VALUES))
        self.update_ui()
        self.log_msg("Rebet placed.")
        self.table_widget.redraw()

    def start_spin(self, *args):
        if self.total_bet == 0:
            self.log_msg("⚠️ Place a bet first!")
            return
        if self.spinning:
            return
        self.spinning = True
        self.spin_btn.background_color = (0.423, 0.467, 0.498, 1)  # disabled gray
        self.target_outcome = RouletteEngine.spin()
        self.log_msg(f"Spinning... targeting {self.target_outcome}")

        # Animation parameters
        self.anim_duration = 3.0
        self.start_time = Clock.get_time()
        Clock.schedule_interval(self._animate_spin, 1/60.0)

    def _animate_spin(self, dt):
        elapsed = Clock.get_time() - self.start_time
        t = min(elapsed / self.anim_duration, 1.0)
        if t >= 1.0:
            Clock.unschedule(self._animate_spin)
            self.spinning = False
            self.spin_btn.background_color = (0.024, 0.839, 0.627, 1)
            self.resolve_bets(self.target_outcome)
            return

        # Ease-out function
        progress = 1.0 if t >= 1.0 else 1.0 - pow(2, -10 * t)
        base_rotations = 8
        segment_deg = 360 / 37
        target_idx = RouletteEngine.WHEEL_NUMBERS.index(self.target_outcome)
        target_wheel_deg = target_idx * segment_deg
        total_wheel_angle = base_rotations * 360 + target_wheel_deg
        wheel_angle = progress * total_wheel_angle
        ball_radius = 200 - 20 * progress
        total_ball_rot = base_rotations * 720 + (360 - target_wheel_deg)
        ball_angle = (progress * total_ball_rot) % 360

        self.wheel_widget.update_angles(wheel_angle, ball_angle, ball_radius)

    def resolve_bets(self, outcome):
        self.history.appendleft(outcome)
        self._update_history_view()
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
            self.wheel_widget.animate_win_flash(outcome)
        else:
            self.losses += 1
        self.balance += total_return
        self.last_bets = self.current_bets.copy()
        self.total_bet = 0
        self.current_bets.clear()
        self.update_ui()
        self.update_statistics()
        self.table_widget.redraw()
        self.log_msg(f"Balance: ${self.balance:.2f} | {'─' * 30}")

    def _update_history_view(self):
        hist_str = "  ".join(str(n) for n in list(self.history)[:10])
        self.history_view.text = hist_str

    def update_statistics(self):
        win_rate = self.wins / max(self.total_spins, 1) * 100
        profit = self.balance - self.starting_balance
        stats = f"Spins: {self.total_spins} | Wins: {self.wins} | Losses: {self.losses} | Win Rate: {win_rate:.1f}% | Profit: ${profit:+.2f}"
        if self.bet_frequency:
            top_num = max(self.bet_frequency, key=self.bet_frequency.get)
            stats += f"\nTop Bet: {top_num} ({self.bet_frequency[top_num]}x)"
        self.stats_label.text = stats

# Run
if __name__ == '__main__':
    RouletteApp().run()