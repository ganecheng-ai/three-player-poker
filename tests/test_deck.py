"""扑克牌和牌堆测试"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.deck import Card, Deck, Suit, sort_cards, cards_to_string
from src.game.cards import HandType, analyze_hand, can_play, compare_hands


class TestCard(unittest.TestCase):
    """卡牌测试"""

    def test_card_creation(self):
        """测试卡牌创建"""
        card = Card(3, Suit.DIAMONDS)
        self.assertEqual(card.rank, 3)
        self.assertEqual(card.suit, Suit.DIAMONDS)

    def test_joker_card(self):
        """测试王牌"""
        low_joker = Card(16, None)
        high_joker = Card(17, None)

        self.assertTrue(low_joker.is_joker)
        self.assertTrue(low_joker.is_low_joker)
        self.assertFalse(low_joker.is_high_joker)

        self.assertTrue(high_joker.is_joker)
        self.assertTrue(high_joker.is_high_joker)
        self.assertFalse(high_joker.is_low_joker)

    def test_card_display_name(self):
        """测试卡牌显示名称"""
        card = Card(3, Suit.DIAMONDS)
        self.assertIn('方块', card.display_name_cn)
        self.assertIn('3', card.display_name_cn)


class TestDeck(unittest.TestCase):
    """牌堆测试"""

    def test_deck_creation(self):
        """测试牌堆创建"""
        deck = Deck()
        self.assertEqual(len(deck), 54)

    def test_deck_shuffle(self):
        """测试洗牌"""
        deck1 = Deck()
        cards1 = deck1.cards.copy()

        deck2 = Deck()
        deck2.shuffle()

        # 洗牌后应该不同（极小概率相同）
        self.assertNotEqual(cards1, deck2.cards)

    def test_deck_deal(self):
        """测试发牌"""
        deck = Deck()
        cards = deck.deal(5)
        self.assertEqual(len(cards), 5)
        self.assertEqual(len(deck), 49)

    def test_deck_deal_three_players(self):
        """测试三人发牌"""
        deck = Deck()
        hand1, hand2, hand3, bottom = deck.deal_three_players()

        self.assertEqual(len(hand1), 17)
        self.assertEqual(len(hand2), 17)
        self.assertEqual(len(hand3), 17)
        self.assertEqual(len(bottom), 3)

    def test_deck_reset(self):
        """测试重置牌堆"""
        deck = Deck()
        deck.deal(10)
        deck.reset()
        self.assertEqual(len(deck), 54)


class TestHandAnalysis(unittest.TestCase):
    """牌型分析测试"""

    def test_single(self):
        """测试单张"""
        card = Card(10, Suit.DIAMONDS)
        result = analyze_hand([card])
        self.assertEqual(result.hand_type, HandType.SINGLE)
        self.assertEqual(result.main_rank, 10)

    def test_pair(self):
        """测试对子"""
        cards = [Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.PAIR)

    def test_triple(self):
        """测试三张"""
        cards = [Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS), Card(10, Suit.HEARTS)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE)

    def test_triple_with_one(self):
        """测试三带一"""
        cards = [
            Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS), Card(10, Suit.HEARTS),
            Card(5, Suit.SPADES)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE_WITH_ONE)

    def test_triple_with_pair(self):
        """测试三带二"""
        cards = [
            Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS), Card(10, Suit.HEARTS),
            Card(5, Suit.SPADES), Card(5, Suit.DIAMONDS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.TRIPLE_WITH_PAIR)

    def test_straight(self):
        """测试顺子"""
        cards = [
            Card(3, Suit.DIAMONDS), Card(4, Suit.CLUBS), Card(5, Suit.HEARTS),
            Card(6, Suit.SPADES), Card(7, Suit.DIAMONDS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.STRAIGHT)

    def test_double_straight(self):
        """测试连对"""
        cards = [
            Card(3, Suit.DIAMONDS), Card(3, Suit.CLUBS),
            Card(4, Suit.HEARTS), Card(4, Suit.SPADES),
            Card(5, Suit.DIAMONDS), Card(5, Suit.CLUBS)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.DOUBLE_STRAIGHT)

    def test_bomb(self):
        """测试炸弹"""
        cards = [
            Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS), Card(10, Suit.SPADES)
        ]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.BOMB)

    def test_rocket(self):
        """测试王炸"""
        cards = [Card(16, None), Card(17, None)]
        result = analyze_hand(cards)
        self.assertEqual(result.hand_type, HandType.ROCKET)


class TestCanPlay(unittest.TestCase):
    """出牌规则测试"""

    def test_free_play(self):
        """测试自由出牌"""
        card = Card(3, Suit.DIAMONDS)
        self.assertTrue(can_play([card], None))

    def test_beat_single(self):
        """测试管单张"""
        last = [Card(10, Suit.DIAMONDS)]
        beat = [Card(14, Suit.CLUBS)]  # A > 10
        self.assertTrue(can_play(beat, last))

        smaller = [Card(5, Suit.CLUBS)]  # 5 < 10
        self.assertFalse(can_play(smaller, last))

    def test_bomb_beats_normal(self):
        """测试炸弹管普通牌"""
        last = [Card(14, Suit.DIAMONDS), Card(14, Suit.CLUBS)]  # 对 A
        bomb = [
            Card(5, Suit.DIAMONDS), Card(5, Suit.CLUBS),
            Card(5, Suit.HEARTS), Card(5, Suit.SPADES)
        ]
        self.assertTrue(can_play(bomb, last))

    def test_rocket_beats_all(self):
        """测试王炸最大"""
        bomb = [
            Card(10, Suit.DIAMONDS), Card(10, Suit.CLUBS),
            Card(10, Suit.HEARTS), Card(10, Suit.SPADES)
        ]
        rocket = [Card(16, None), Card(17, None)]
        self.assertTrue(can_play(rocket, bomb))


if __name__ == '__main__':
    unittest.main()
