"""游戏规则测试"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.deck import Card, Deck, Suit
from src.game.rules import GameRule, GamePhase, PlayerRole


class TestGameRule(unittest.TestCase):
    """游戏规则测试"""

    def setUp(self):
        """测试前准备"""
        self.rule = GameRule()

    def test_start_game(self):
        """测试开始游戏"""
        player_ids = [0, 1, 2]
        result = self.rule.start_game(player_ids)

        self.assertTrue(result)
        self.assertEqual(self.rule.phase, GamePhase.CALL_LANDLORD)

        # 检查手牌数量
        for pid in player_ids:
            self.assertEqual(len(self.rule.get_player_hand(pid)), 17)

        # 检查底牌数量
        self.assertEqual(len(self.rule.bottom_cards), 3)

    def test_call_landlord_3(self):
        """测试叫 3 分直接成为地主"""
        self.rule.start_game([0, 1, 2])

        # 玩家 0 叫 3 分
        self.rule.call_landlord(0, 3)

        self.assertEqual(self.rule.landlord_id, 0)
        self.assertEqual(self.rule.roles[0], PlayerRole.LANDLORD)
        self.assertEqual(self.rule.roles[1], PlayerRole.FARMER)
        self.assertEqual(self.rule.roles[2], PlayerRole.FARMER)

        # 地主应该有 20 张牌（17+3 底牌）
        self.assertEqual(len(self.rule.get_player_hand(0)), 20)

        # 应该进入出牌阶段
        self.assertEqual(self.rule.phase, GamePhase.PLAYING)

        # 地主应该先出牌
        self.assertEqual(self.rule.get_current_player(), 0)

    def test_call_landlord_highest_score(self):
        """测试最高分成为地主"""
        self.rule.start_game([0, 1, 2])

        # 玩家 0 不叫，玩家 1 叫 2 分，玩家 2 叫 1 分
        self.rule.call_landlord(0, 0)
        self.rule.call_landlord(1, 2)
        self.rule.call_landlord(2, 1)

        # 玩家 1 应该成为地主
        self.assertEqual(self.rule.landlord_id, 1)
        self.assertEqual(self.rule.roles[1], PlayerRole.LANDLORD)

    def test_play_cards(self):
        """测试出牌"""
        self.rule.start_game([0, 1, 2])
        self.rule.call_landlord(0, 3)

        # 地主出单张
        hand = self.rule.get_player_hand(0)
        card_to_play = [hand[0]]
        result = self.rule.play_cards(0, card_to_play)

        self.assertTrue(result)
        self.assertEqual(len(self.rule.get_player_hand(0)), 19)

        # 应该切换到下一个玩家
        self.assertEqual(self.rule.get_current_player(), 1)

    def test_play_invalid_cards(self):
        """测试无效出牌"""
        self.rule.start_game([0, 1, 2])
        self.rule.call_landlord(0, 3)

        # 尝试出两张不同点数的牌（无效牌型）
        hand = self.rule.get_player_hand(0)

        # 找两张不同点数且不是王炸的牌
        # 注意：手牌按 rank 降序排序，所以大王 (17) 在小王 (16) 前面
        card1 = None
        card2 = None
        for i in range(len(hand) - 1):
            if hand[i].rank != hand[i + 1].rank:
                # 排除王炸组合（17=大王，16=小王，排序后 17 在前）
                is_rocket = (hand[i].rank == 17 and hand[i + 1].rank == 16)
                if not is_rocket:
                    card1 = hand[i]
                    card2 = hand[i + 1]
                    break

        # 如果手牌中没有合适的两张牌，则跳过测试
        if card1 is None or card2 is None:
            self.skipTest("手牌中没有两张不同点数且不是王炸的牌")

        invalid_cards = [card1, card2]
        result = self.rule.play_cards(0, invalid_cards)
        self.assertFalse(result, "出两张不同点数且不是王炸的牌应该是无效的")

    def test_pass_turn(self):
        """测试过牌"""
        self.rule.start_game([0, 1, 2])
        self.rule.call_landlord(0, 3)

        # 地主先出一张牌
        hand = self.rule.get_player_hand(0)
        self.rule.play_cards(0, [hand[0]])

        # 现在轮到玩家 1，假设是电脑玩家，直接过牌
        self.assertEqual(self.rule.get_current_player(), 1)
        self.rule.pass_turn(1)

        # 应该轮到玩家 2
        self.assertEqual(self.rule.get_current_player(), 2)

    def test_game_over(self):
        """测试游戏结束"""
        self.rule.start_game([0, 1, 2])
        self.rule.call_landlord(0, 3)

        # 模拟地主出完所有牌
        while not self.rule.is_game_over():
            current = self.rule.get_current_player()
            hand = self.rule.get_player_hand(current)

            if hand:
                # 出最小的牌
                if current == 0 or self.rule.last_hand is None or self.rule.last_hand_player == current:
                    # 自由出牌
                    self.rule.play_cards(current, [hand[0]])
                else:
                    # 需要管牌，简单起见直接过
                    self.rule.pass_turn(current)
            else:
                break

        self.assertTrue(self.rule.is_game_over())
        winner = self.rule.get_winner_team()
        self.assertIn(winner, ['landlord', 'farmer'])


if __name__ == '__main__':
    unittest.main()
