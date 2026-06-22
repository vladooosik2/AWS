from PromptBuilder import PromptBuilder

class TicTacToeAI:
    def __init__(self, gemini_client):
        self.client = gemini_client

    async def get_ai_move(self, game):
        """Отримує хід AI від Gemini"""
        if self.client is None:
            return None

        try:
            available_moves = game.get_available_moves()
            if not available_moves:
                return None

            board_state = self.get_board_representation(game)
            prompt = PromptBuilder.tictactoe_prompt(board_state, available_moves)

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )

            move = self.parse_ai_response(response.text, available_moves)
            return move

        except Exception as err:
            print(f"Error getting AI move: {type(err)}: {err}")
            return None

    def get_board_representation(self, game):
        """Представляє дошку для Gemini"""
        board_str = ""
        for i in range(3):
            row = []
            for j in range(3):
                cell_idx = i * 3 + j
                cell = game.board[cell_idx]
                row.append(cell if cell != ' ' else str(cell_idx + 1))
            board_str += f"  {' | '.join(row)}\n"
            if i < 2:
                board_str += "  ---------\n"
        return board_str

    def parse_ai_response(self, response_text, available_moves):
        """Парсить відповідь Gemini для отримання ходу"""
        for move in available_moves:
            if str(move) in response_text:
                return move
        return available_moves[0] if available_moves else None
