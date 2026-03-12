"""扑克牌和牌堆模块"""
import random
from enum import IntEnum
from typing import List, Tuple, Optional


class Suit(IntEnum):
    """花色枚举"""
    DIAMONDS = 0  # 方块
    CLUBS = 1     # 梅花
    HEARTS = 2    # 红桃
    SPADES = 3    # 黑桃
    JOKER_LOW = 4   # 小王
    JOKER_HIGH = 5  # 大王


class Card:
    """扑克牌类"""

    # 牌面值 (3-2, J, Q, K, A, 小王，大王)
    RANK_NAMES = {
        3: '3',
        4: '4',
        5: '5',
        6: '6',
        7: '7',
        8: '8',
        9: '9',
        10: '10',
        11: 'J',
        12: 'Q',
        13: 'K',
        14: 'A',
        15: '2',
        16: 'JOKER_LOW',   # 小王
        17: 'JOKER_HIGH', # 大王
    }

    # 中文牌面值
    RANK_NAMES_CN = {
        3: '3',
        4: '4',
        5: '5',
        6: '6',
        7: '7',
        8: '8',
        9: '9',
        10: '10',
        11: 'J',
        12: 'Q',
        13: 'K',
        14: 'A',
        15: '2',
        16: '小王',
        17: '大王',
    }

    # 花色中文名称
    SUIT_NAMES_CN = {
        Suit.DIAMONDS: '方块',
        Suit.CLUBS: '梅花',
        Suit.HEARTS: '红桃',
        Suit.SPADES: '黑桃',
    }

    def __init__(self, rank: int, suit: Optional[Suit] = None):
        """
        初始化一张牌

        Args:
            rank: 牌面值 (3-17, 其中 16=小王，17=大王)
            suit: 花色 (大王小王为 None)
        """
        self.rank = rank
        self.suit = suit
        self.face_up = True  # 是否明牌

    @property
    def is_joker(self) -> bool:
        """是否为王"""
        return self.rank >= 16

    @property
    def is_high_joker(self) -> bool:
        """是否为大王"""
        return self.rank == 17

    @property
    def is_low_joker(self) -> bool:
        """是否为小王"""
        return self.rank == 16

    @property
    def display_name(self) -> str:
        """获取牌的显示名称（英文）"""
        if self.is_joker:
            return self.RANK_NAMES[self.rank]
        return f"{self.SUIT_NAMES_CN.get(self.suit, '')}{self.RANK_NAMES[self.rank]}"

    @property
    def display_name_cn(self) -> str:
        """获取牌的显示名称（中文）"""
        if self.is_joker:
            return self.RANK_NAMES_CN[self.rank]
        return f"{self.SUIT_NAMES_CN.get(self.suit, '')}{self.RANK_NAMES_CN[self.rank]}"

    @property
    def short_name(self) -> str:
        """获取牌的短名称（用于显示）"""
        return self.RANK_NAMES_CN[self.rank]

    def __repr__(self) -> str:
        return f"Card({self.rank}, {self.suit})"

    def __str__(self) -> str:
        return self.display_name_cn

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def copy(self) -> 'Card':
        """复制一张牌"""
        return Card(self.rank, self.suit)


class Deck:
    """牌堆类"""

    def __init__(self):
        """初始化一副完整的扑克牌（54 张）"""
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> 'Deck':
        """重置牌堆为完整的 54 张牌"""
        self.cards = []
        # 添加 4 种花色的牌 (3-2)
        for suit in [Suit.DIAMONDS, Suit.CLUBS, Suit.HEARTS, Suit.SPADES]:
            for rank in range(3, 16):  # 3 到 2 (15)
                self.cards.append(Card(rank, suit))
        # 添加大小王
        self.cards.append(Card(16, None))  # 小王
        self.cards.append(Card(17, None))  # 大王
        return self

    def shuffle(self) -> 'Deck':
        """洗牌"""
        random.shuffle(self.cards)
        return self

    def deal(self, num: int = 1) -> List[Card]:
        """
        发牌

        Args:
            num: 发牌数量

        Returns:
            发出的牌列表
        """
        if num > len(self.cards):
            raise ValueError(f"牌堆剩余 {len(self.cards)} 张，无法发出 {num} 张")
        dealt = self.cards[:num]
        self.cards = self.cards[num:]
        return dealt

    def deal_three_players(self) -> Tuple[List[Card], List[Card], List[Card], List[Card]]:
        """
        三人斗地主发牌

        Returns:
            (玩家 1 手牌，玩家 2 手牌，玩家 3 手牌，底牌)
        """
        self.shuffle()
        # 每人 17 张，底牌 3 张
        hand1 = sorted(self.deal(17), key=lambda c: c.rank)
        hand2 = sorted(self.deal(17), key=lambda c: c.rank)
        hand3 = sorted(self.deal(17), key=lambda c: c.rank)
        bottom_cards = self.deal(3)
        return hand1, hand2, hand3, bottom_cards

    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return f"Deck({len(self.cards)} cards)"


def sort_cards(cards: List[Card]) -> List[Card]:
    """按牌面大小排序手牌"""
    return sorted(cards, key=lambda c: c.rank, reverse=True)


def cards_to_string(cards: List[Card], use_chinese: bool = True) -> str:
    """将牌列表转换为字符串"""
    if use_chinese:
        return ' '.join([c.short_name for c in cards])
    return ' '.join([c.RANK_NAMES.get(c.rank, '?') for c in cards])
