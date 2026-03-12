"""斗地主游戏主入口"""
import sys
import pygame

from src.game.deck import Card, Deck, sort_cards
from src.game.rules import GameRule, GamePhase, PlayerRole
from src.game.cards import analyze_hand, can_play
from src.player.human import HumanPlayer
from src.player.ai import AIPlayer
from src.ui.screen import GameScreen, COLOR_TEXT


class DouDizhuGame:
    """斗地主游戏主类"""

    def __init__(self):
        self.screen = GameScreen(1280, 720)
        self.rule = GameRule()

        # 玩家
        self.human_player = HumanPlayer(0, "玩家")
        self.ai_player1 = AIPlayer(1, "电脑 1")
        self.ai_player2 = AIPlayer(2, "电脑 2")
        self.players = {
            0: self.human_player,
            1: self.ai_player1,
            2: self.ai_player2,
        }

        # 游戏状态
        self.game_started = False
        self.message = "欢迎来到斗地主!"
        self.message_timer = 0

        # AI 思考延迟
        self.ai_think_timer = 0
        self.waiting_for_ai = False

    def start_new_game(self):
        """开始新游戏"""
        player_ids = [0, 1, 2]
        self.rule.start_game(player_ids)
        self.game_started = True
        self.screen.selected_cards = []
        self.message = "请叫地主!"
        self.message_timer = 60  # 显示 1 秒

        # 重置 AI 记牌器
        self.ai_player1.remembered_cards = {r: 4 for r in range(3, 16)}
        self.ai_player1.remembered_cards[16] = 1
        self.ai_player1.remembered_cards[17] = 1
        self.ai_player2.remembered_cards = {r: 4 for r in range(3, 16)}
        self.ai_player2.remembered_cards[16] = 1
        self.ai_player2.remembered_cards[17] = 1

    def run(self):
        """运行游戏主循环"""
        self.screen.initialize()
        self.start_new_game()

        running = True
        while running:
            # 处理事件
            for event in self.screen.poll_events():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        self.handle_click(event.pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        self.start_new_game()
                    if event.key == pygame.K_SPACE:
                        # 空格键出牌
                        if self.rule.get_current_player() == 0 and \
                           self.rule.phase == GamePhase.PLAYING:
                            self.play_selected_cards()

            # AI 逻辑
            self.update_ai()

            # 渲染
            self.render()
            self.screen.update()

        self.screen.quit()

    def handle_click(self, pos):
        """处理鼠标点击"""
        # 检查按钮点击
        button_name = self.screen.handle_click(pos)
        if button_name:
            if button_name == "Start" and not self.game_started:
                self.start_new_game()
            elif button_name == "Pass" and self.can_player_act():
                self.rule.pass_turn(0)
                self.message = "你选择了过牌"
            elif button_name == "Call1" and self.rule.phase == GamePhase.CALL_LANDLORD:
                self.handle_call_score(1)
            elif button_name == "Call2" and self.rule.phase == GamePhase.CALL_LANDLORD:
                self.handle_call_score(2)
            elif button_name == "Call3" and self.rule.phase == GamePhase.CALL_LANDLORD:
                self.handle_call_score(3)
            elif button_name == "NoCall" and self.rule.phase == GamePhase.CALL_LANDLORD:
                self.handle_call_score(0)
            return

        # 检查卡牌点击（选择/取消选择）
        if self.rule.phase == GamePhase.PLAYING and \
           self.rule.get_current_player() == 0:
            hand = self.rule.get_player_hand(0)
            if hand:
                # 玩家手牌位置（底部中央）
                total_width = len(hand) * (self.screen.card_width - 25)
                start_x = (self.screen.width - total_width) // 2
                start_y = self.screen.height - self.screen.card_height - 20

                card_idx = self.screen.handle_card_click(hand, pos, start_x, start_y, 25)
                if card_idx is not None:
                    if card_idx in self.screen.selected_cards:
                        self.screen.selected_cards.remove(card_idx)
                    else:
                        self.screen.selected_cards.append(card_idx)

    def handle_call_score(self, score: int):
        """处理叫分"""
        self.rule.call_landlord(0, score)
        score_names = {0: "不叫", 1: "1 分", 2: "2 分", 3: "3 分"}
        self.message = f"你叫了 {score_names[score]}"

        # 检查是否需要继续叫牌
        next_caller = self.rule.get_next_caller()
        if next_caller is not None and next_caller != 0:
            self.waiting_for_ai = True
            self.ai_think_timer = 30  # 0.5 秒后 AI 叫牌

    def can_player_act(self) -> bool:
        """判断当前是否是玩家行动"""
        return (self.rule.phase == GamePhase.PLAYING and
                self.rule.get_current_player() == 0 and
                not self.waiting_for_ai)

    def play_selected_cards(self):
        """打出选中的牌"""
        hand = self.rule.get_player_hand(0)
        if not hand or not self.screen.selected_cards:
            self.message = "请选择要出的牌!"
            return

        # 获取选中的牌
        selected_cards = [hand[i] for i in self.screen.selected_cards]

        # 尝试出牌
        if self.rule.play_cards(0, selected_cards):
            self.screen.selected_cards = []
            self.message = "你出牌了!"

            # 检查游戏是否结束
            if self.rule.is_game_over():
                self.handle_game_over()
            else:
                # AI 回合
                next_player = self.rule.get_current_player()
                if next_player != 0:
                    self.waiting_for_ai = True
                    self.ai_think_timer = 30
        else:
            self.message = "无效的出牌!"

    def update_ai(self):
        """更新 AI 逻辑"""
        if not self.waiting_for_ai:
            return

        self.ai_think_timer -= 1
        if self.ai_think_timer <= 0:
            self.waiting_for_ai = False
            current_player = self.rule.get_current_player()

            if current_player is None:
                return

            if self.rule.phase == GamePhase.CALL_LANDLORD:
                # AI 叫地主
                ai = self.players.get(current_player)
                if isinstance(ai, AIPlayer):
                    max_score = max(self.rule.call_scores.values()) if self.rule.call_scores else 0
                    score = ai.choose_call_score(self.rule, max_score)
                    self.rule.call_landlord(current_player, score)
                    score_names = {0: "不叫", 1: "1 分", 2: "2 分", 3: "3 分"}
                    self.message = f"{ai.name} 叫了 {score_names[score]}"

            elif self.rule.phase == GamePhase.PLAYING:
                ai = self.players.get(current_player)
                if isinstance(ai, AIPlayer):
                    cards = ai.choose_cards(self.rule)
                    if cards:
                        if self.rule.play_cards(current_player, cards):
                            # 更新记牌器
                            ai.update_memorized_cards(cards)
                            self.message = f"{ai.name} 出牌了"

                            # 检查游戏是否结束
                            if self.rule.is_game_over():
                                self.handle_game_over()
                    else:
                        self.rule.pass_turn(current_player)
                        self.message = f"{ai.name} 不要"

    def handle_game_over(self):
        """处理游戏结束"""
        winner = self.rule.get_winner_team()
        landlord = self.rule.get_landlord()

        if winner == 'landlord':
            if landlord == 0:
                self.message = "游戏结束 - 你是地主，你赢了!"
            else:
                self.message = "游戏结束 - 电脑是地主，电脑赢了!"
        else:
            if landlord == 0:
                self.message = "游戏结束 - 你是地主，农民赢了!"
            else:
                self.message = "游戏结束 - 你是农民，你赢了!"

        self.game_started = False

    def render(self):
        """渲染游戏画面"""
        self.screen.clear()

        # 绘制标题
        self.screen.draw_message("斗地主", self.screen.width // 2 - 60, 20, "large")

        if not self.game_started:
            # 开始按钮
            self.screen.create_button("Start", "开始新游戏",
                                      self.screen.width // 2 - 60,
                                      self.screen.height // 2)
            self.screen.draw_button("Start")
            self.screen.draw_message(self.message, self.screen.width // 2 - 100,
                                     self.screen.height // 2 - 50)
            return

        # 绘制游戏界面
        self.render_game()

    def render_game(self):
        """渲染游戏进行中画面"""
        # 绘制底牌（顶部中央）
        if self.rule.phase == GamePhase.PLAYING:
            self.screen.draw_bottom_cards(self.rule.bottom_cards,
                                          self.screen.width // 2 - 150, 10)

        # 绘制其他玩家（电脑）
        # 电脑 1（左侧）
        hand1 = self.rule.get_player_hand(1)
        role1 = self.rule.get_player_role(1)
        self.screen.draw_player_info(1, "电脑 1", role1, len(hand1), 50, 100)
        # 绘制电脑 1 的牌背
        for i in range(min(len(hand1), 17)):
            self.screen.draw_card(Card(3, Card.SPADES), 50 + i * 15, 150, face_up=False)

        # 电脑 2（右侧）
        hand2 = self.rule.get_player_hand(2)
        role2 = self.rule.get_player_role(2)
        self.screen.draw_player_info(2, "电脑 2", role2, len(hand2),
                                     self.screen.width - 150, 100)
        # 绘制电脑 2 的牌背
        for i in range(min(len(hand2), 17)):
            self.screen.draw_card(Card(3, Card.SPADES),
                                  self.screen.width - 100 - i * 15, 150, face_up=False)

        # 绘制玩家手牌（底部）
        hand = self.rule.get_player_hand(0)
        role = self.rule.get_player_role(0)
        self.screen.draw_player_info(0, "玩家", role, len(hand), 50,
                                     self.screen.height - 80)

        if hand:
            total_width = len(hand) * (self.screen.card_width - 25)
            start_x = (self.screen.width - total_width) // 2
            start_y = self.screen.height - self.screen.card_height - 20
            self.screen.draw_hand(hand, start_x, start_y, overlap=25)

        # 绘制当前玩家提示
        current = self.rule.get_current_player()
        if current == 0:
            self.screen.draw_message("你的回合", self.screen.width // 2 - 50,
                                     self.screen.height // 2 - 50)
        elif current == 1:
            self.screen.draw_message("电脑 1 的回合", self.screen.width // 2 - 60,
                                     self.screen.height // 2 - 50)
        else:
            self.screen.draw_message("电脑 2 的回合", self.screen.width // 2 - 60,
                                     self.screen.height // 2 - 50)

        # 绘制叫地主按钮
        if self.rule.phase == GamePhase.CALL_LANDLORD and \
           self.rule.get_current_player() == 0 and 0 not in self.rule.call_scores:
            self._draw_call_buttons()

        # 绘制出牌按钮
        if self.rule.phase == GamePhase.PLAYING and current == 0:
            self._draw_play_buttons()

        # 绘制消息
        self.screen.draw_message(self.message, 10, self.screen.height - 40, "small")

        # 绘制提示
        self.screen.draw_message("按 R 重新开始 | 按 ESC 退出",
                                 self.screen.width - 250, self.screen.height - 40, "small")

    def _draw_call_buttons(self):
        """绘制叫地主按钮"""
        button_y = self.screen.height // 2
        button_x = self.screen.width // 2 - 200

        self.screen.create_button("NoCall", "不叫", button_x, button_y)
        self.screen.create_button("Call1", "1 分", button_x + 130, button_y)
        self.screen.create_button("Call2", "2 分", button_x + 260, button_y)
        self.screen.create_button("Call3", "3 分", button_x + 390, button_y)

        for btn in ["NoCall", "Call1", "Call2", "Call3"]:
            self.screen.draw_button(btn)

    def _draw_play_buttons(self):
        """绘制出牌按钮"""
        button_y = self.screen.height // 2
        button_x = self.screen.width // 2 - 100

        # 检查是否能出牌（有选中的牌或上一手是自己）
        last_player = self.rule.last_hand_player
        can_play_cards = (last_player == 0 or last_player is None)

        self.screen.create_button("Play", "出牌 (空格)", button_x - 60, button_y)
        self.screen.create_button("Pass", "过牌", button_x + 60, button_y)

        play_enabled = len(self.screen.selected_cards) > 0 or can_play_cards
        self.screen.draw_button("Play", play_enabled)

        # 只有当不是自由出牌时才能过牌
        pass_enabled = (last_player is not None and last_player != 0)
        self.screen.draw_button("Pass", pass_enabled)


def main():
    """主函数"""
    game = DouDizhuGame()
    game.run()


if __name__ == "__main__":
    main()
