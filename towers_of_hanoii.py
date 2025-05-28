import tkinter as tk
from tkinter import messagebox
import time
import threading
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class GameSetup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Towers of Hanoi - Setup")
        self.root.geometry("300x150")
        
        tk.Label(self.root, text="Towers of Hanoi Setup", font=('Arial', 16)).pack(pady=10)
        tk.Label(self.root, text="Number of Disks (2-8):").pack()
        self.disks_var = tk.StringVar(value="3")
        self.disks_entry = tk.Entry(self.root, textvariable=self.disks_var)
        self.disks_entry.pack()
        tk.Button(self.root, text="Start Game", command=self.start_game).pack(pady=20)
        self.result = None
        self.root.mainloop()
    
    def start_game(self):
        try:
            num_disks = int(self.disks_var.get())
            if not (2 <= num_disks <= 8):
                messagebox.showerror("Error", "Number of disks must be between 2 and 8")
                return
            self.result = num_disks
            self.root.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

class TowersOfHanoi:
    def __init__(self, root, num_disks):
        self.root = root
        self.root.title("Towers of Hanoi")
        self.root.geometry("900x650")
        self.num_disks = num_disks
        self.num_towers = 3
        self.moves = 0
        self.selected_tower = None
        self.towers = [[] for _ in range(self.num_towers)]
        self.minimum_moves = 2 ** self.num_disks - 1
        self.timer_running = False
        self.start_time = None
        self.elapsed_time = 0
        self.timer_label = None
        self.timer_thread = None
        self.stop_timer_flag = False
        self.solving = False
        self.move_history = []
        self.initialize_game()
        self.create_gui()
    
    def initialize_game(self):
        for i in range(self.num_disks, 0, -1):
            self.towers[0].append(i)
    
    def create_gui(self):
        # Top frame for controls
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        self.reset_button = tk.Button(self.top_frame, text="Reset Game", command=self.reset_game)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        self.new_game_button = tk.Button(self.top_frame, text="New Game", command=self.new_game)
        self.new_game_button.pack(side=tk.LEFT, padx=5)
        self.solve_button = tk.Button(self.top_frame, text="Solve", command=self.solve)
        self.solve_button.pack(side=tk.LEFT, padx=5)
        self.move_label = tk.Label(self.top_frame, text=f"Moves: 0 / Min: {self.minimum_moves}", font=('Arial', 12))
        self.move_label.pack(side=tk.LEFT, padx=20)
        self.timer_label = tk.Label(self.top_frame, text="Time: 00:00", font=('Arial', 12))
        self.timer_label.pack(side=tk.LEFT, padx=20)
        # Instructions
        self.instructions = tk.Label(self.root, text="Click a tower to select a disk, then click another tower to move it. Goal: Move all disks to the rightmost tower.", font=('Arial', 12), wraplength=700)
        self.instructions.pack(pady=5)
        # Main frame for canvas and move history
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # Canvas for towers
        self.canvas = tk.Canvas(self.main_frame, width=700, height=400, bg='white')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        # Move history panel
        self.history_frame = tk.Frame(self.main_frame)
        self.history_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        tk.Label(self.history_frame, text="Move History", font=('Arial', 12, 'bold')).pack()
        self.history_listbox = tk.Listbox(self.history_frame, width=15, font=('Arial', 11))
        self.history_listbox.pack(fill=tk.Y, expand=True)
        self.draw_game()
        self.start_timer()
    
    def draw_game(self):
        self.canvas.delete("all")
        tower_positions = [150, 350, 550]
        # Draw base
        self.canvas.create_line(50, 350, 650, 350, width=5)
        # Draw towers
        for i, pos in enumerate(tower_positions):
            color = 'orange' if self.selected_tower == i else 'black'
            self.canvas.create_line(pos, 350, pos, 150, width=7 if self.selected_tower == i else 5, fill=color)
        # Draw disks
        colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'cyan']
        for i, tower in enumerate(self.towers):
            for j, disk in enumerate(tower):
                x = tower_positions[i]
                y = 350 - (j * 30)
                width = disk * 30
                self.canvas.create_rectangle(
                    x - width//2, y - 20,
                    x + width//2, y,
                    fill=colors[(disk-1)%len(colors)], outline='black', width=2
                )
                self.canvas.create_text(x, y-10, text=str(disk), fill='white', font=('Arial', 12, 'bold'))
        # Tower labels
        labels = ['A', 'B', 'C']
        for i, pos in enumerate(tower_positions):
            self.canvas.create_text(pos, 370, text=labels[i], font=('Arial', 14, 'bold'))
        # Update move history
        self.history_listbox.delete(0, tk.END)
        for move in self.move_history:
            self.history_listbox.insert(tk.END, move)
    
    def on_click(self, event):
        if self.solving:
            return
        x = event.x
        tower_positions = [150, 350, 550]
        tower_idx = None
        for i, pos in enumerate(tower_positions):
            if pos - 50 <= x <= pos + 50:
                tower_idx = i
                break
        if tower_idx is None:
            return
        if self.selected_tower is None:
            if self.towers[tower_idx]:
                self.selected_tower = tower_idx
        else:
            if self.is_valid_move(self.selected_tower, tower_idx):
                self.animate_disk_move(self.selected_tower, tower_idx)
            self.selected_tower = None
        self.draw_game()
    
    def is_valid_move(self, from_tower, to_tower):
        if not self.towers[from_tower]:
            return False
        if not self.towers[to_tower]:
            return True
        return self.towers[from_tower][-1] < self.towers[to_tower][-1]
    
    def move_disk(self, from_tower, to_tower):
        disk = self.towers[from_tower].pop()
        self.towers[to_tower].append(disk)
        # Add move to history
        labels = ['A', 'B', 'C']
        self.move_history.append(f"{labels[from_tower]} → {labels[to_tower]}")
    
    def animate_disk_move(self, from_tower, to_tower, callback=None):
        # Animate disk moving up, across, and down
        disk = self.towers[from_tower][-1]
        tower_positions = [150, 350, 550]
        x0 = tower_positions[from_tower]
        x1 = tower_positions[to_tower]
        y0 = 350 - (len(self.towers[from_tower])-1) * 30
        y1 = 350 - (len(self.towers[to_tower])) * 30
        colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'cyan']
        rect = self.canvas.create_rectangle(x0-disk*15, y0-20, x0+disk*15, y0, fill=colors[(disk-1)%len(colors)], outline='black', width=2)
        text = self.canvas.create_text(x0, y0-10, text=str(disk), fill='white', font=('Arial', 12, 'bold'))
        def move_up():
            for _ in range(10):
                self.canvas.move(rect, 0, -3)
                self.canvas.move(text, 0, -3)
                self.canvas.update()
                time.sleep(0.01)
            move_across()
        def move_across():
            dx = (x1 - x0) / 20
            for _ in range(20):
                self.canvas.move(rect, dx, 0)
                self.canvas.move(text, dx, 0)
                self.canvas.update()
                time.sleep(0.01)
            move_down()
        def move_down():
            for _ in range(10):
                self.canvas.move(rect, 0, (y1-y0)/10)
                self.canvas.move(text, 0, (y1-y0)/10)
                self.canvas.update()
                time.sleep(0.01)
            self.canvas.delete(rect)
            self.canvas.delete(text)
            self.move_disk(from_tower, to_tower)
            self.moves += 1
            self.move_label.config(text=f"Moves: {self.moves} / Min: {self.minimum_moves}")
            self.draw_game()
            self.play_move_sound()
            if self.check_win():
                self.stop_timer()
                self.play_win_sound()
                messagebox.showinfo("Congratulations!", f"You won in {self.moves} moves!\nTime: {self.format_time(self.elapsed_time)}")
                self.reset_game()
            if callback:
                callback()
        self.root.after(1, move_up)
    
    def check_win(self):
        return len(self.towers[2]) == self.num_disks
    
    def reset_game(self):
        self.towers = [[] for _ in range(self.num_towers)]
        self.moves = 0
        self.move_label.config(text=f"Moves: 0 / Min: {self.minimum_moves}")
        self.selected_tower = None
        self.move_history = []
        self.initialize_game()
        self.draw_game()
        self.stop_timer()
        self.start_timer()
        self.solving = False
        self.solve_button.config(state=tk.NORMAL)
    
    def new_game(self):
        self.stop_timer()
        self.root.destroy()
        main()
    
    def start_timer(self):
        self.start_time = time.time()
        self.elapsed_time = 0
        self.timer_running = True
        self.stop_timer_flag = False
        self.update_timer()
    
    def stop_timer(self):
        self.timer_running = False
        self.stop_timer_flag = True
    
    def update_timer(self):
        if self.stop_timer_flag:
            return
        if self.timer_running:
            self.elapsed_time = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Time: {self.format_time(self.elapsed_time)}")
            self.root.after(1000, self.update_timer)
    
    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def play_move_sound(self):
        if SOUND_AVAILABLE:
            winsound.MessageBeep(winsound.MB_OK)
    
    def play_win_sound(self):
        if SOUND_AVAILABLE:
            winsound.Beep(880, 200)
            winsound.Beep(1320, 200)
    
    def solve(self):
        if hasattr(self, 'solving') and self.solving:
            return
        self.solving = True
        self.solve_button.config(state=tk.DISABLED)
        self.selected_tower = None
        self.solve_moves = []
        self._generate_moves(self.num_disks, 0, 2, 1)
        self._animate_moves()

    def _generate_moves(self, n, source, target, auxiliary):
        if n == 0:
            return
        self._generate_moves(n-1, source, auxiliary, target)
        self.solve_moves.append((source, target))
        self._generate_moves(n-1, auxiliary, target, source)

    def _animate_moves(self):
        if not self.solve_moves:
            self.solving = False
            self.solve_button.config(state=tk.NORMAL)
            if self.check_win():
                self.stop_timer()
                self.play_win_sound()
                messagebox.showinfo("Solved!", f"Solved in {self.moves} moves!\nTime: {self.format_time(self.elapsed_time)}")
            return
        from_tower, to_tower = self.solve_moves.pop(0)
        def after_move():
            self.root.after(100, self._animate_moves)
        self.animate_disk_move(from_tower, to_tower, callback=after_move)

def main():
    setup = GameSetup()
    if setup.result:
        num_disks = setup.result
        root = tk.Tk()
        game = TowersOfHanoi(root, num_disks)
        root.mainloop()

if __name__ == "__main__":
    main() 
