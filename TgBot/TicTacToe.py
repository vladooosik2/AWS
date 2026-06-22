class TicTacToe:
    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.human = 'X'
        self.ai = 'O'
        self.game_over = False
        self.winner = None

    def get_board_display(self):
        #Показує дошку у формі для Telegram
        board_str = ""
        for i in range(3):
            row = []
            for j in range(3):
                cell_idx = i * 3 + j
                cell = self.board[cell_idx]
                if cell == ' ':
                    row.append(f"{cell_idx + 1}")
                else:
                    row.append(cell)
            board_str += " | ".join(row) + "\n"
            if i < 2:
                board_str += "---------\n"
        return board_str

    def is_valid_move(self, position):
        #Перевіряє, чи допустимий хід (1-9)
        try:
            pos = int(position) - 1
            if 0 <= pos <= 8 and self.board[pos] == ' ':
                return pos
        except (ValueError, IndexError):
            pass
        return None

    def make_move(self, position, player):
        #Робить хід
        if self.board[position] == ' ':
            self.board[position] = player
            return True
        return False

    def check_winner(self):
        #Перевіряє, чи є переможець
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in winning_combinations:
            if (self.board[combo[0]] != ' ' and
                self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]]):
                return self.board[combo[0]]
        return None

    def is_board_full(self):
        #Перевіряє, чи дошка заповнена
        return ' ' not in self.board

    def update_game_state(self):
        #Оновлює стан гри
        winner = self.check_winner()
        if winner:
            self.game_over = True
            self.winner = winner
        elif self.is_board_full():
            self.game_over = True
            self.winner = 'draw'

    def get_available_moves(self):
        #Повертає список доступних ходів
        return [i + 1 for i in range(9) if self.board[i] == ' ']

    def get_game_status(self):
        #Повертає поточний стан гри
        if not self.game_over:
            return "гра триває"
        if self.winner == 'draw':
            return "нічия"
        return f"переможець: {self.winner}"
