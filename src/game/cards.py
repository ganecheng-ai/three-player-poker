"""牌型定义和比较逻辑"""
from enum import IntEnum
from typing import List, Optional, Tuple, Dict
from collections import Counter
from .deck import Card


class HandType(IntEnum):
    """牌型枚举"""
    INVALID = 0       # 无效牌型
    SINGLE = 1        # 单张
    PAIR = 2          # 对子
    TRIPLE = 3        # 三张
    TRIPLE_WITH_ONE = 4    # 三带一
    TRIPLE_WITH_PAIR = 5   # 三带二
    STRAIGHT = 6      # 单顺子
    DOUBLE_STRAIGHT = 7    # 双顺子
    AIRPLANE = 8      # 飞机（不带）
    AIRPLANE_WITH_SINGLE = 9   # 飞机带单
    AIRPLANE_WITH_PAIR = 10  # 飞机带对
    BOMB = 11         # 炸弹
    ROCKET = 12       # 王炸


# 牌型名称（中文）
HAND_TYPE_NAMES_CN = {
    HandType.INVALID: '无效牌型',
    HandType.SINGLE: '单张',
    HandType.PAIR: '对子',
    HandType.TRIPLE: '三张',
    HandType.TRIPLE_WITH_ONE: '三带一',
    HandType.TRIPLE_WITH_PAIR: '三带二',
    HandType.STRAIGHT: '顺子',
    HandType.DOUBLE_STRAIGHT: '连对',
    HandType.AIRPLANE: '飞机',
    HandType.AIRPLANE_WITH_SINGLE: '飞机带单',
    HandType.AIRPLANE_WITH_PAIR: '飞机带对',
    HandType.BOMB: '炸弹',
    HandType.ROCKET: '王炸',
}


class HandResult:
    """牌型分析结果"""

    def __init__(self, hand_type: HandType, main_rank: int, extra_cards: Optional[List[Card]] = None):
        """
        Args:
            hand_type: 牌型
            main_rank: 主要牌面值（用于比较大小）
            extra_cards: 额外的牌（用于完整还原手牌）
        """
        self.hand_type = hand_type
        self.main_rank = main_rank
        self.extra_cards = extra_cards or []

    @property
    def name_cn(self) -> str:
        """中文牌型名称"""
        return HAND_TYPE_NAMES_CN.get(self.hand_type, '未知')

    def __repr__(self) -> str:
        return f"HandResult({self.name_cn}, main_rank={self.main_rank})"


def analyze_hand(cards: List[Card]) -> HandResult:
    """
    分析手牌的牌型

    Args:
        cards: 手牌列表

    Returns:
        牌型分析结果
    """
    if not cards:
        return HandResult(HandType.INVALID, 0)

    n = len(cards)
    ranks = sorted([c.rank for c in cards], reverse=True)
    rank_counts = Counter(ranks)

    # 王炸（大小王）
    if n == 2 and ranks == [17, 16]:
        return HandResult(HandType.ROCKET, 17)

    # 单张
    if n == 1:
        return HandResult(HandType.SINGLE, ranks[0])

    # 对子
    if n == 2 and len(rank_counts) == 1 and list(rank_counts.values())[0] == 2:
        return HandResult(HandType.PAIR, ranks[0])

    # 三张
    if n == 3 and len(rank_counts) == 1 and list(rank_counts.values())[0] == 3:
        return HandResult(HandType.TRIPLE, ranks[0])

    # 三带一
    if n == 4 and len(rank_counts) == 2:
        counts = list(rank_counts.items())
        triple_rank = None
        single_rank = None
        for rank, count in counts:
            if count == 3:
                triple_rank = rank
            elif count == 1:
                single_rank = rank
        if triple_rank and single_rank:
            # Find the actual card with the single rank from input
            single_card = next(c for c in cards if c.rank == single_rank)
            return HandResult(HandType.TRIPLE_WITH_ONE, triple_rank, [single_card])

    # 三带二（对子）
    if n == 5 and len(rank_counts) == 2:
        counts = list(rank_counts.items())
        triple_rank = None
        pair_rank = None
        for rank, count in counts:
            if count == 3:
                triple_rank = rank
            elif count == 2:
                pair_rank = rank
        if triple_rank and pair_rank:
            # Find the actual cards from input
            triple_cards = [c for c in cards if c.rank == triple_rank][:3]
            pair_cards = [c for c in cards if c.rank == pair_rank][:2]
            return HandResult(HandType.TRIPLE_WITH_PAIR, triple_rank, triple_cards + pair_cards)

    # 炸弹
    if n == 4 and len(rank_counts) == 1:
        return HandResult(HandType.BOMB, ranks[0])

    # 单顺子 (5 张或以上连续单牌，不含 2 和王)
    if n >= 5 and len(rank_counts) == n:
        if all(r < 15 for r in ranks):  # 不含 2 和王
            if max(ranks) - min(ranks) == n - 1:
                return HandResult(HandType.STRAIGHT, max(ranks))

    # 双顺子 (3 个或以上连续对子，不含 2 和王)
    if n >= 6 and n % 2 == 0 and all(c == 2 for c in rank_counts.values()):
        pair_ranks = sorted(rank_counts.keys(), reverse=True)
        if all(r < 15 for r in pair_ranks):  # 不含 2 和王
            if max(pair_ranks) - min(pair_ranks) == len(pair_ranks) - 1:
                return HandResult(HandType.DOUBLE_STRAIGHT, max(pair_ranks))

    # 飞机（连续三张，不含 2 和王）
    if n >= 6 and n % 3 == 0 and all(c == 3 for c in rank_counts.values()):
        triple_ranks = sorted(rank_counts.keys(), reverse=True)
        if all(r < 15 for r in triple_ranks):  # 不含 2 和王
            if max(triple_ranks) - min(triple_ranks) == len(triple_ranks) - 1:
                return HandResult(HandType.AIRPLANE, max(triple_ranks))

    # 飞机带单（连续三张 + 相同数量的单张）
    if n >= 8 and n % 4 == 0:
        num_triples = n // 4
        triple_ranks = [r for r, c in rank_counts.items() if c == 3]
        single_ranks = [r for r, c in rank_counts.items() if c == 1]
        if len(triple_ranks) == num_triples and len(single_ranks) == num_triples:
            triple_ranks.sort(reverse=True)
            if all(r < 15 for r in triple_ranks):
                if max(triple_ranks) - min(triple_ranks) == num_triples - 1:
                    return HandResult(HandType.AIRPLANE_WITH_SINGLE, max(triple_ranks))

    # 飞机带对（连续三张 + 相同数量的对子）
    if n >= 10 and n % 5 == 0:
        num_triples = n // 5
        triple_ranks = [r for r, c in rank_counts.items() if c == 3]
        pair_ranks = [r for r, c in rank_counts.items() if c == 2]
        if len(triple_ranks) == num_triples and len(pair_ranks) == num_triples:
            triple_ranks.sort(reverse=True)
            if all(r < 15 for r in triple_ranks):
                if max(triple_ranks) - min(triple_ranks) == num_triples - 1:
                    return HandResult(HandType.AIRPLANE_WITH_PAIR, max(triple_ranks))

    # 飞机带单/对的变体（三张数量可以更多，带的牌数量匹配即可）
    # 飞机带单变体
    if n >= 8:
        for num_triples in range(2, n // 3 + 1):
            if num_triples * 4 > n:
                continue
            triple_ranks_list = [r for r, c in rank_counts.items() if c == 3]
            if len(triple_ranks_list) >= num_triples:
                # 尝试找连续的三张
                triple_ranks_list.sort(reverse=True)
                for i in range(len(triple_ranks_list) - num_triples + 1):
                    seq = triple_ranks_list[i:i + num_triples]
                    if max(seq) - min(seq) == num_triples - 1 and all(r < 15 for r in seq):
                        # 检查剩余牌是否为单张
                        remaining = n - num_triples * 3
                        if remaining == num_triples:
                            other_ranks = [r for r in rank_counts if r not in seq]
                            other_count = sum(rank_counts[r] for r in other_ranks)
                            if other_count == remaining:
                                return HandResult(HandType.AIRPLANE_WITH_SINGLE, max(seq))
                        elif remaining == num_triples * 2:
                            # 飞机带对
                            other_ranks = [r for r in rank_counts if r not in seq]
                            other_count = sum(rank_counts[r] for r in other_ranks)
                            if other_count == remaining and all(rank_counts[r] == 2 for r in other_ranks):
                                return HandResult(HandType.AIRPLANE_WITH_PAIR, max(seq))

    return HandResult(HandType.INVALID, 0)


def can_play(hand: List[Card], last_hand: Optional[List[Card]]) -> bool:
    """
    判断手牌是否可以出

    Args:
        hand: 当前手牌
        last_hand: 上一手牌（None 表示可以自由出牌）

    Returns:
        是否可以出牌
    """
    if not hand:
        return False

    hand_result = analyze_hand(hand)
    if hand_result.hand_type == HandType.INVALID:
        return False

    if last_hand is None:
        return True

    last_result = analyze_hand(last_hand)
    if last_result.hand_type == HandType.INVALID:
        return True

    # 王炸可以管任何牌
    if hand_result.hand_type == HandType.ROCKET:
        return True

    # 炸弹可以管除了王炸和更大的炸弹外的所有牌
    if hand_result.hand_type == HandType.BOMB:
        if last_result.hand_type == HandType.ROCKET:
            return False
        if last_result.hand_type == HandType.BOMB:
            return hand_result.main_rank > last_result.main_rank
        return True

    # 相同牌型且牌面更大
    if hand_result.hand_type == last_result.hand_type:
        if hand_result.hand_type in [HandType.SINGLE, HandType.PAIR, HandType.TRIPLE,
                                      HandType.STRAIGHT, HandType.DOUBLE_STRAIGHT,
                                      HandType.AIRPLANE]:
            return hand_result.main_rank > last_result.main_rank

        if hand_result.hand_type in [HandType.TRIPLE_WITH_ONE, HandType.TRIPLE_WITH_PAIR,
                                      HandType.AIRPLANE_WITH_SINGLE, HandType.AIRPLANE_WITH_PAIR]:
            return hand_result.main_rank > last_result.main_rank

    return False


def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
    """
    比较两手牌

    Returns:
        1: hand1 大
        -1: hand2 大
        0: 无法比较或相同
    """
    r1 = analyze_hand(hand1)
    r2 = analyze_hand(hand2)

    if r1.hand_type == HandType.INVALID:
        return -1 if r2.hand_type != HandType.INVALID else 0
    if r2.hand_type == HandType.INVALID:
        return 1

    # 王炸最大
    if r1.hand_type == HandType.ROCKET:
        return 1 if r2.hand_type != HandType.ROCKET else 0
    if r2.hand_type == HandType.ROCKET:
        return -1

    # 炸弹比较
    if r1.hand_type == HandType.BOMB:
        if r2.hand_type == HandType.BOMB:
            return 1 if r1.main_rank > r2.main_rank else (-1 if r1.main_rank < r2.main_rank else 0)
        return 1  # 炸弹管非炸弹
    if r2.hand_type == HandType.BOMB:
        return -1

    # 相同牌型比较主牌
    if r1.hand_type == r2.hand_type:
        return 1 if r1.main_rank > r2.main_rank else (-1 if r1.main_rank < r2.main_rank else 0)

    return 0  # 不同牌型无法比较
