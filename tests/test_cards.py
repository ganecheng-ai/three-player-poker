"""牌型定义和比较测试"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.deck import Card, Deck, Suit
from src.game.cards import (
    HandType, analyze_hand, can_play, compare_hands,
    HandResult, HAND_TYPE_NAMES_CN
)


class TestHandAnalysis(unittest.TestCase):
    """牌型分析测试"""

    def test_invalid_hand(self):
        """测试无效牌型"""
        # 空手牌
        result = analyze_hand([])
        self.assertEqual(result.hand_type, HandType.INVALID)
        self.assertEqual(result.main_rank, 0)

        # 两张不同点数的牌
        cards = [Card(3, Suit.DIAMONDS), Card(5, Suit.CLUBS)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.INVALID)

    def test_single(self):
        """测试单张"""
        card = Card(10, Suit.DIAMONDS)
        result = analyze_hand([card])
        self.assertEqual(result.hand_type, HandType.SINGLE)
        self.assertEqual(result.main_rank, 10)
        self.assertEqual(result.name_cn, "单张")

    def test_pair(self):
        """测试对子"""
        cards = [Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.PAIR)
        self.assertEqual(result.main_rank, 10)

    def test_triple(self):
        """测试三张"""
        cards = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE)
        self.assertEqual(result.main_rank, 10)

    def test_triple_with_one(self):
        """测试三带一"""
        cards = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(5, Suit.SPADES)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE_WITH_ONE)
        self.assertEqual(result.main_rank, 10)
        self.assertEqual(len(result.extra_cards), 1)

    def test_triple_with_pair(self):
        """测试三带二"""
        cards = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(5, Suit.SPADES),
            Card(5, Suit.DIAMONDS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE_WITH_PAIR)
        self.assertEqual(result.main_rank, 10)

    def test_straight(self):
        """测试顺子"""
        cards = [
            Card(3, Suit.DIAMONDS),
            Card(4, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES),
            Card(7, Suit.DIAMONDS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.STRAIGHT)
        self.assertEqual(result.main_rank, 7)

        # 更长的顺子
        cards = [
            Card(3, Suit.DIAMONDS),
            Card(4, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES),
            Card(7, Suit.DIAMONDS),
            Card(8, Suit.CLUBS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.STRAIGHT)
        self.assertEqual(result.main_rank, 8)

    def test_straight_with_2_or_joker_invalid(self):
        """测试顺子包含 2 或王则为无效"""
        # 包含 2
        cards = [
            Card(3, Suit.DIAMONDS),
            Card(4, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES),
            Card(15, Suit.DIAMONDS)  # 2
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.INVALID)

        # 包含小王
        cards = [
            Card(3, Suit.DIAMONDS),
            Card(4, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES),
            Card(16, None)  # 小王
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.INVALID)

    def test_double_straight(self):
        """测试连对"""
        cards = [
            Card(3, Suit.DIAMONDS), Card(3, Suit.CLUBS),
            Card(4, Suit.HEARTS), Card(4, Suit.SPADES),
            Card(5, Suit.DIAMONDS), Card(5, Suit.CLUBS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.DOUBLE_STRAIGHT)
        self.assertEqual(result.main_rank, 5)

    def test_bomb(self):
        """测试炸弹"""
        cards = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(10, Suit.SPADES)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.BOMB)
        self.assertEqual(result.main_rank, 10)

    def test_rocket(self):
        """测试王炸"""
        cards = [Card(16, None), Card(17, None)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.ROCKET)
        self.assertEqual(result.main_rank, 17)


class TestCanPlay(unittest.TestCase):
    """出牌规则测试"""

    def test_free_play(self):
        """测试自由出牌"""
        card = Card(3, Suit.DIAMONDS)
        self.assertTrue(can_play([card], None))

        # 任意有效牌型都可以自由出
        cards = [Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS)]
        self.assertTrue(can_play(cards, None))

    def test_invalid_hand_cannot_play(self):
        """测试无效牌型不能出"""
        cards = [Card(3, Suit.DIAMONDS), Card(5, Suit.CLUBS)]
        self.assertFalse(can_play(cards, None))

    def test_beat_single(self):
        """测试管单张"""
        last = [Card(10, Suit.DIAMONDS)]

        # 更大的单张可以管
        beat = [Card(14, Suit.CLUBS)]  # A > 10
        self.assertTrue(can_play(beat, last))

        # 更小的单张不能管
        smaller = [Card(5, Suit.CLUBS)]
        self.assertFalse(can_play(smaller, last))

        # 相同点数不能管
        same = [Card(10, Suit.CLUBS)]
        self.assertFalse(can_play(same, last))

    def test_beat_pair(self):
        """测试管对子"""
        last = [Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS)]

        # 更大的对子可以管
        beat = [Card(14, Suit.HEARTS), Card(14, Suit.SPADES)]
        self.assertTrue(can_play(beat, last))

        # 更小的对子不能管
        smaller = [Card(5, Suit.DIAMONDS), Card(5, Suit.CLUBS)]
        self.assertFalse(can_play(smaller, last))

    def test_beat_triple(self):
        """测试管三张"""
        last = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS)
        ]

        beat = [
            Card(14, Suit.HEARTS),
            Card(14, Suit.SPADES),
            Card(14, Suit.DIAMONDS)
        ]
        self.assertTrue(can_play(beat, last))

        smaller = [
            Card(5, Suit.DIAMONDS),
            Card(5, Suit.CLUBS),
            Card(5, Suit.HEARTS)
        ]
        self.assertFalse(can_play(smaller, last))

    def test_bomb_beats_normal(self):
        """测试炸弹管普通牌"""
        # 对 A
        last = [Card(14, Suit.DIAMONDS), Card(14, Suit.CLUBS)]

        # 小炸弹
        bomb = [
            Card(5, Suit.DIAMONDS),
            Card(5, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(5, Suit.SPADES)
        ]
        self.assertTrue(can_play(bomb, last))

    def test_bomb_comparison(self):
        """测试炸弹比较"""
        small_bomb = [
            Card(5, Suit.DIAMONDS),
            Card(5, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(5, Suit.SPADES)
        ]

        big_bomb = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(10, Suit.SPADES)
        ]

        # 大炸弹可以管小炸弹
        self.assertTrue(can_play(big_bomb, small_bomb))

        # 小炸弹不能管大炸弹
        self.assertFalse(can_play(small_bomb, big_bomb))

    def test_rocket_beats_all(self):
        """测试王炸最大"""
        # 王炸可以管任何牌
        rocket = [Card(16, None), Card(17, None)]

        # 管单张
        self.assertTrue(can_play(rocket, [Card(15, Suit.DIAMONDS)]))

        # 管炸弹
        bomb = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(10, Suit.SPADES)
        ]
        self.assertTrue(can_play(rocket, bomb))


class TestCompareHands(unittest.TestCase):
    """牌型比较测试"""

    def test_same_type_comparison(self):
        """测试相同牌型比较"""
        hand1 = [Card(10, Suit.DIAMONDS)]
        hand2 = [Card(14, Suit.CLUBS)]  # A > 10

        result = compare_hands(hand1, hand2)
        self.assertEqual(result, -1)  # hand2 大

        result = compare_hands(hand2, hand1)
        self.assertEqual(result, 1)  # hand1 大

    def test_rocket_is_biggest(self):
        """测试王炸最大"""
        rocket = [Card(16, None), Card(17, None)]
        bomb = [
            Card(10, Suit.DIAMONDS),
            Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS),
            Card(10, Suit.SPADES)
        ]

        result = compare_hands(rocket, bomb)
        self.assertEqual(result, 1)  # 王炸大

    def test_bomb_beats_non_bomb(self):
        """测试炸弹管非炸弹"""
        bomb = [
            Card(5, Suit.DIAMONDS),
            Card(5, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(5, Suit.SPADES)
        ]
        straight = [
            Card(3, Suit.DIAMONDS),
            Card(4, Suit.CLUBS),
            Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES),
            Card(7, Suit.DIAMONDS)
        ]

        result = compare_hands(bomb, straight)
        self.assertEqual(result, 1)  # 炸弹大

    def test_different_types_cannot_compare(self):
        """测试不同牌型无法比较"""
        single = [Card(15, Suit.DIAMONDS)]  # 2
        pair = [Card(3, Suit.DIAMONDS), Card(3, Suit.CLUBS)]

        result = compare_hands(single, pair)
        self.assertEqual(result, 0)  # 无法比较


class TestHandTypeNames(unittest.TestCase):
    """牌型名称测试"""

    def test_all_hand_types_have_chinese_names(self):
        """测试所有牌型都有中文名称"""
        for hand_type in HandType:
            self.assertIn(hand_type, HAND_TYPE_NAMES_CN)
            self.assertIsNotNone(HAND_TYPE_NAMES_CN[hand_type])


if __name__ == '__main__':
    unittest.main()
