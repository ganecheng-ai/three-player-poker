"""人类玩家类"""
from typing import List, Optional, Callable
from ..game.deck import Card
from ..game.rules import GameRule


class HumanPlayer:
    """人类玩家类"""

    def __init__(self, player_id: int, name: str = "玩家"):
        self.player_id = player_id
        self.name = name
        self.input_handler: Optional[Callable] = None

    def set_input_handler(self, handler: Callable):
        """设置输入处理器（用于 UI 交互）"""
        self.input_handler = handler

    def choose_call_score(self, rule: GameRule, current_max: int) -> int:
        """
        选择叫分

        Args:
            rule: 游戏规则
            current_max: 当前最高叫分

        Returns:
            叫分 (0/1/2/3)
        """
        if self.input_handler:
            return self.input_handler('call_score', {
                'player_id': self.player_id,
                'current_max': current_max,
                'hand': rule.get_player_hand(self.player_id)
            })
        # 默认不叫（用于控制台 fallback）
        return 0

    def choose_cards(self, rule: GameRule) -> Optional[List[Card]]:
        """
        选择出牌

        Args:
            rule: 游戏规则

        Returns:
            要出的牌列表，None 表示过牌
        """
        if self.input_handler:
            return self.input_handler('play_cards', {
                'player_id': self.player_id,
                'hand': rule.get_player_hand(self.player_id),
                'last_hand': rule.last_hand,
                'last_hand_player': rule.last_hand_player
            })
        # 默认过牌
        return None

    def notify_game_over(self, winner: str, rule: GameRule):
        """通知游戏结束"""
        if self.input_handler:
            self.input_handler('game_over', {
                'winner': winner,
                'player_id': self.player_id,
                'landlord': rule.get_landlord()
            })
