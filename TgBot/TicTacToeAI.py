from PromptBuilder import PromptBuilder

class TicTacToeAI:
    def __init__(self, gemini_client):
        self.client = gemini_client
        print(f"TicTacToeAI initialized with client: {gemini_client is not None}")

    async def get_ai_move(self, game):
        #Отримує хід AI від Gemini
        if self.client is None:
            print("ERROR: Client is None in get_ai_move")
            return None

        try:
            available_moves = game.get_available_moves()
            print(f"Available moves: {available_moves}")
            if not available_moves:
                return None

            board_state = self.get_board_representation(game)
            prompt = PromptBuilder.tictactoe_prompt(board_state, available_moves)
            print(f"Sending prompt to Gemini:\n{prompt}")

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            print(f"Gemini response: {response.text}")
            move = self.parse_ai_response(response.text, available_moves)
            print(f"Parsed move: {move}")
            return move

        except Exception as err:
            print(f"ERROR in get_ai_move: {type(err).__name__}: {err}")
            import traceback
            traceback.print_exc()
            return None

    def get_board_representation(self, game):
        #Представляє дошку для Gemini
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
        #Парсить відповідь Gemini для отримання ходу
        print(f"Parsing response: {response_text}")
        print(f"Available moves to check: {available_moves}")
        for move in available_moves:
            if str(move) in response_text:
                print(f"Found move: {move}")
                return move
        print(f"No move found in response, returning first available: {available_moves[0] if available_moves else None}")
        return available_moves[0] if available_moves else None
    
