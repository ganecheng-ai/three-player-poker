"""AI 玩家类"""
import random
from typing import List, Optional, Dict, Tuple
from collections import Counter

from ..game.deck import Card, sort_cards
from ..game.rules import GameRule, PlayerRole
from ..game.cards import HandType, analyze_hand, can_play, HandResult


class AIPlayer:
    """AI 玩家类 - 智能斗地主 AI"""

    def __init__(self, player_id: int, name: str = "电脑"):
        self.player_id = player_id
        self.name = name
        self.remembered_cards: Dict[int, int] = {}  # 记牌器：rank -> count
        self.last_played_cards: List[Card] = []  # 最后打出的牌

        # 初始化记牌器（所有牌初始为 4 张，王为 1 张）
        for rank in range(3, 16):
            self.remembered_cards[rank] = 4
        self.remembered_cards[16] = 1  # 小王
        self.remembered_cards[17] = 1  # 大王

    def update_memorized_cards(self, cards: List[Card]):
        """更新记牌器（记录已打出的牌）"""
        for card in cards:
            if card.rank in self.remembered_cards:
                self.remembered_cards[card.rank] -= 1

    def get_remaining_cards(self) -> Dict[int, int]:
        """获取剩余牌的分布"""
        return {rank: count for rank, count in self.remembered_cards.items() if count > 0}

    def choose_call_score(self, rule: GameRule, current_max: int) -> int:
        """
        AI 叫分逻辑

        策略：
        - 评估手牌强度
        - 考虑是否有炸弹、王、2 等关键牌
        """
        hand = rule.get_player_hand(self.player_id)
        score = self._evaluate_hand_strength(hand)

        # 至少要高于当前叫分
        if score <= current_max:
            score = current_max

        # 如果牌太弱，不叫
        if score < 1:
            return 0

        return min(score, 3)

    def _evaluate_hand_strength(self, hand: List[Card]) -> int:
        """
        评估手牌强度

        Returns:
            建议叫分 (0-3)
        """
        if not hand:
            return 0

        rank_counts = Counter(c.rank for c in hand)
        ranks = sorted(rank_counts.keys(), reverse=True)

        score = 0

        # 大王加分
        if 17 in rank_counts:
            score += 2

        # 小王加分
        if 16 in rank_counts:
            score += 1

        # 2 加分
        score += rank_counts.get(15, 0) * 0.5

        # A 加分
        score += rank_counts.get(14, 0) * 0.3

        # 炸弹加分
        for rank, count in rank_counts.items():
            if count == 4:
                score += 2
            elif count >= 3 and rank > 10:
                score += 0.5

        # 顺子潜力
        consecutive = 0
        for i in range(len(ranks) - 1):
            if ranks[i] - ranks[i + 1] == 1 and ranks[i] < 15:
                consecutive += 1
        if consecutive >= 4:
            score += 0.5

        # 根据分数决定叫分
        if score >= 3:
            return 3
        elif score >= 2:
            return 2
        elif score >= 1:
            return 1
        return 0

    def choose_cards(self, rule: GameRule) -> Optional[List[Card]]:
        """
        AI 出牌逻辑

        策略：
        - 如果是自由出牌，出最小的有效牌型
        - 如果需要管牌，尝试用最小的牌管上
        - 如果管不上或牌太好，考虑是否过牌
        """
        hand = rule.get_player_hand(self.player_id)
        if not hand:
            return None

        last_hand = rule.last_hand
        last_player = rule.last_hand_player

        # 如果是自由出牌（上一手是自己或没有上一手）
        if last_hand is None or last_player == self.player_id:
            return self._play_free(hand)

        # 需要管牌
        return self._play_to_beat(hand, last_hand)

    def _play_free(self, hand: List[Card]) -> List[Card]:
        """自由出牌策略 - 智能选择出牌"""
        rank_groups = self._group_cards_by_rank(hand)
        ranks = sorted(rank_groups.keys())

        # 策略：优先出能减少手牌数量的牌型
        # 1. 尝试出飞机带对或飞机带单
        airplane_with_pair = self._try_airplane_with_pair(rank_groups)
        if airplane_with_pair:
            return airplane_with_pair

        airplane_with_single = self._try_airplane_with_single(rank_groups)
        if airplane_with_single:
            return airplane_with_single

        # 2. 尝试出连对
        double_straight = self._try_double_straight(rank_groups)
        if double_straight:
            return double_straight

        # 3. 尝试出顺子
        straight = self._try_straight(rank_groups)
        if straight:
            return straight

        # 4. 尝试出飞机（不带）
        airplane = self._try_airplane(rank_groups)
        if airplane:
            return airplane

        # 5. 先尝试出三带一或三带二
        for rank in ranks:
            if len(rank_groups.get(rank, [])) >= 3:
                # 找一个最小的单牌或对子来带
                other_ranks = [r for r in ranks if r != rank]
                if other_ranks:
                    # 三带一
                    other_rank = min(other_ranks)
                    if rank_groups[other_rank]:
                        return rank_groups[rank][:3] + [rank_groups[other_rank][0]]
                # 找一个最小的对子
                pair_ranks = [r for r in other_ranks if len(rank_groups.get(r, [])) >= 2]
                if pair_ranks:
                    pair_rank = min(pair_ranks)
                    return rank_groups[rank][:3] + rank_groups[pair_rank][:2]

        # 6. 尝试出对子（优先出小的对子）
        for rank in ranks:
            if len(rank_groups.get(rank, [])) >= 2:
                return rank_groups[rank][:2]

        # 7. 出单张（最小）
        for rank in ranks:
            if rank_groups[rank]:
                return [rank_groups[rank][0]]

        return hand  # 不应该到这里

    def _try_straight(self, rank_groups: Dict[int, List[Card]]) -> Optional[List[Card]]:
        """尝试出顺子"""
        available_ranks = sorted([r for r in rank_groups.keys() if r < 15 and rank_groups[r]])
        if len(available_ranks) < 5:
            return None

        # 找最长的顺子
        for length in range(min(12, len(available_ranks)), 4, -1):  # 从长到短尝试
            for i in range(len(available_ranks) - length + 1):
                start_rank = available_ranks[i]
                if start_rank + length - 1 >= 15:
                    continue
                # 检查是否连续
                valid = True
                cards = []
                for r in range(start_rank, start_rank + length):
                    if r not in rank_groups:
                        valid = False
                        break
                    cards.append(rank_groups[r][0])
                if valid:
                    return cards
        return None

    def _try_double_straight(self, rank_groups: Dict[int, List[Card]]) -> Optional[List[Card]]:
        """尝试出连对"""
        pair_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 2])
        if len(pair_ranks) < 3:
            return None

        # 找最长的连对
        for length in range(min(10, len(pair_ranks)), 2, -1):
            for i in range(len(pair_ranks) - length + 1):
                start_rank = pair_ranks[i]
                if start_rank + length - 1 >= 15:
                    continue
                valid = True
                cards = []
                for r in range(start_rank, start_rank + length):
                    if r not in rank_groups or len(rank_groups[r]) < 2:
                        valid = False
                        break
                    cards.extend(rank_groups[r][:2])
                if valid:
                    return cards
        return None

    def _try_airplane(self, rank_groups: Dict[int, List[Card]]) -> Optional[List[Card]]:
        """尝试出飞机（不带）"""
        triple_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 3])
        if len(triple_ranks) < 2:
            return None

        # 找最长的飞机
        for length in range(min(6, len(triple_ranks)), 1, -1):
            for i in range(len(triple_ranks) - length + 1):
                start_rank = triple_ranks[i]
                if start_rank + length - 1 >= 15:
                    continue
                valid = True
                cards = []
                for r in range(start_rank, start_rank + length):
                    if r not in rank_groups or len(rank_groups[r]) < 3:
                        valid = False
                        break
                    cards.extend(rank_groups[r][:3])
                if valid:
                    return cards
        return None

    def _try_airplane_with_single(self, rank_groups: Dict[int, List[Card]]) -> Optional[List[Card]]:
        """尝试出飞机带单"""
        triple_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 3])
        if len(triple_ranks) < 2:
            return None

        # 找连续的三张
        for length in range(min(5, len(triple_ranks)), 1, -1):
            for i in range(len(triple_ranks) - length + 1):
                start_rank = triple_ranks[i]
                if start_rank + length - 1 >= 15:
                    continue

                # 检查是否连续
                airplane_ranks = list(range(start_rank, start_rank + length))
                valid = all(r in rank_groups and len(rank_groups[r]) >= 3 for r in airplane_ranks)

                if not valid:
                    continue

                # 找带的单牌
                single_ranks = [r for r in rank_groups.keys() if r not in airplane_ranks and rank_groups[r]]
                if len(single_ranks) >= length:
                    airplane_cards = []
                    for r in airplane_ranks:
                        airplane_cards.extend(rank_groups[r][:3])
                    for r in single_ranks[:length]:
                        airplane_cards.append(rank_groups[r][0])
                    return airplane_cards
        return None

    def _try_airplane_with_pair(self, rank_groups: Dict[int, List[Card]]) -> Optional[List[Card]]:
        """尝试出飞机带对"""
        triple_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 3])
        pair_ranks = [r for r in rank_groups.keys() if len(rank_groups.get(r, [])) >= 2]

        if len(triple_ranks) < 2:
            return None

        # 找连续的三张
        for length in range(min(4, len(triple_ranks)), 1, -1):
            for i in range(len(triple_ranks) - length + 1):
                start_rank = triple_ranks[i]
                if start_rank + length - 1 >= 15:
                    continue

                airplane_ranks = list(range(start_rank, start_rank + length))
                valid = all(r in rank_groups and len(rank_groups[r]) >= 3 for r in airplane_ranks)

                if not valid:
                    continue

                # 找带的对子（不能和飞机重复）
                available_pair_ranks = [r for r in pair_ranks if r not in airplane_ranks]
                if len(available_pair_ranks) >= length:
                    airplane_cards = []
                    for r in airplane_ranks:
                        airplane_cards.extend(rank_groups[r][:3])
                    for r in available_pair_ranks[:length]:
                        airplane_cards.extend(rank_groups[r][:2])
                    return airplane_cards
        return None

    def _play_to_beat(self, hand: List[Card], last_hand: List[Card]) -> Optional[List[Card]]:
        """管牌策略 - 尝试用最小的牌管上"""
        last_result = analyze_hand(last_hand)
        if last_result.hand_type == HandType.INVALID:
            return self._play_free(hand)

        rank_groups = self._group_cards_by_rank(hand)

        # 处理炸弹管炸弹的情况
        if last_result.hand_type == HandType.BOMB:
            bomb = self._find_smallest_bomb(rank_groups, last_result.main_rank)
            if bomb:
                return bomb
            # 没有更大的炸弹，尝试用王炸
            if 16 in rank_groups and 17 in rank_groups:
                return [Card(16, None), Card(17, None)]
            return None  # 管不上

        # 处理王炸 - 无法管
        if last_result.hand_type == HandType.ROCKET:
            return None

        # 王炸策略 - 只在必要时使用
        has_rocket = 16 in rank_groups and 17 in rank_groups

        # 先尝试用普通牌型管
        normal_beat = self._find_normal_beat(hand, last_hand, rank_groups, last_result)
        if normal_beat:
            return normal_beat

        # 没有普通牌型可以管，考虑是否用炸弹
        if self._should_use_bomb(last_hand):
            bomb = self._find_smallest_bomb(rank_groups, 0)
            if bomb:
                return bomb
            # 没有炸弹，考虑用王炸
            if has_rocket:
                return [Card(16, None), Card(17, None)]

        return None  # 选择过牌

    def _find_normal_beat(self, hand: List[Card], last_hand: List[Card],
                          rank_groups: Dict[int, List[Card]],
                          last_result: HandResult) -> Optional[List[Card]]:
        """寻找能管上的普通牌型"""

        # 单张
        if last_result.hand_type == HandType.SINGLE:
            for rank in sorted(rank_groups.keys()):
                if rank > last_result.main_rank and rank_groups[rank]:
                    return [rank_groups[rank][0]]

        # 对子
        if last_result.hand_type == HandType.PAIR:
            for rank in sorted(rank_groups.keys()):
                if rank > last_result.main_rank and len(rank_groups[rank]) >= 2:
                    return rank_groups[rank][:2]

        # 三张
        if last_result.hand_type == HandType.TRIPLE:
            for rank in sorted(rank_groups.keys()):
                if rank > last_result.main_rank and len(rank_groups[rank]) >= 3:
                    return rank_groups[rank][:3]

        # 三带一
        if last_result.hand_type == HandType.TRIPLE_WITH_ONE:
            for rank in sorted(rank_groups.keys()):
                if rank > last_result.main_rank and len(rank_groups[rank]) >= 3:
                    # 找一个最小的带牌
                    other_ranks = [r for r in rank_groups if r != rank and rank_groups[r]]
                    if other_ranks:
                        other_rank = min(other_ranks)
                        return rank_groups[rank][:3] + [rank_groups[other_rank][0]]

        # 三带二
        if last_result.hand_type == HandType.TRIPLE_WITH_PAIR:
            for rank in sorted(rank_groups.keys()):
                if rank > last_result.main_rank and len(rank_groups[rank]) >= 3:
                    # 找一个最小的对子
                    pair_ranks = [r for r in rank_groups if r != rank and len(rank_groups[r]) >= 2]
                    if pair_ranks:
                        pair_rank = min(pair_ranks)
                        return rank_groups[rank][:3] + rank_groups[pair_rank][:2]

        # 顺子
        if last_result.hand_type == HandType.STRAIGHT:
            straight_beat = self._find_straight_beat(rank_groups, last_result.main_rank, len(last_hand))
            if straight_beat:
                return straight_beat

        # 连对
        if last_result.hand_type == HandType.DOUBLE_STRAIGHT:
            double_straight_beat = self._find_double_straight_beat(rank_groups, last_result.main_rank, len(last_hand) // 2)
            if double_straight_beat:
                return double_straight_beat

        # 飞机（不带）
        if last_result.hand_type == HandType.AIRPLANE:
            airplane_beat = self._find_airplane_beat(rank_groups, last_result.main_rank, len(last_hand) // 3)
            if airplane_beat:
                return airplane_beat

        # 飞机带单
        if last_result.hand_type == HandType.AIRPLANE_WITH_SINGLE:
            airplane_beat = self._find_airplane_with_single_beat(hand, rank_groups, last_result.main_rank, len(last_hand) // 4)
            if airplane_beat:
                return airplane_beat

        # 飞机带对
        if last_result.hand_type == HandType.AIRPLANE_WITH_PAIR:
            airplane_beat = self._find_airplane_with_pair_beat(hand, rank_groups, last_result.main_rank, len(last_hand) // 5)
            if airplane_beat:
                return airplane_beat

        return None

    def _find_smallest_bomb(self, rank_groups: Dict[int, List[Card]],
                            beat_rank: int = 0) -> Optional[List[Card]]:
        """寻找最小的炸弹"""
        for rank in sorted(rank_groups.keys()):
            if rank > beat_rank and len(rank_groups[rank]) >= 4:
                return rank_groups[rank][:4]
        return None

    def _should_use_bomb(self, last_hand: List[Card]) -> bool:
        """判断是否应该用炸弹"""
        result = analyze_hand(last_hand)

        # 王炸不需要用炸弹管（已经在 _play_to_beat 中处理）
        if result.hand_type == HandType.ROCKET:
            return False

        # 炸弹需要用更大的炸弹管
        if result.hand_type == HandType.BOMB:
            return True

        # 对手牌很大（2或更大），值得用炸弹
        if result.main_rank >= 15:  # 2 或王
            return True

        # 对手牌是较大的牌（K、A），可以考虑用炸弹
        if result.main_rank >= 13:
            return True

        return False

    def _find_straight_beat(self, rank_groups: Dict[int, List[Card]],
                              beat_rank: int, length: int) -> Optional[List[Card]]:
        """寻找能管上的顺子"""
        # 找到连续的牌，长度为 length，最大牌大于 beat_rank
        available_ranks = sorted([r for r in rank_groups.keys() if r < 15 and rank_groups[r]])  # 不含2和王
        for start_rank in range(beat_rank + 1, 15):  # 从 beat_rank+1 开始尝试
            # 检查是否有从 start_rank 开始的 length 张连续牌
            if start_rank + length - 1 >= 15:  # 超出范围
                continue
            valid = True
            cards = []
            for r in range(start_rank, start_rank + length):
                if r not in rank_groups or not rank_groups[r]:
                    valid = False
                    break
                cards.append(rank_groups[r][0])
            if valid:
                return cards
        return None

    def _find_double_straight_beat(self, rank_groups: Dict[int, List[Card]],
                                   beat_rank: int, pair_count: int) -> Optional[List[Card]]:
        """寻找能管上的连对"""
        available_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 2])
        for start_rank in range(beat_rank + 1, 15):  # 从 beat_rank+1 开始尝试
            if start_rank + pair_count - 1 >= 15:
                continue
            valid = True
            cards = []
            for r in range(start_rank, start_rank + pair_count):
                if r not in rank_groups or len(rank_groups[r]) < 2:
                    valid = False
                    break
                cards.extend(rank_groups[r][:2])
            if valid:
                return cards
        return None

    def _find_airplane_beat(self, rank_groups: Dict[int, List[Card]],
                            beat_rank: int, triple_count: int) -> Optional[List[Card]]:
        """寻找能管上的飞机（不带）"""
        available_ranks = sorted([r for r in rank_groups.keys() if r < 15 and len(rank_groups.get(r, [])) >= 3])
        for start_rank in range(beat_rank + 1, 15):
            if start_rank + triple_count - 1 >= 15:
                continue
            valid = True
            cards = []
            for r in range(start_rank, start_rank + triple_count):
                if r not in rank_groups or len(rank_groups[r]) < 3:
                    valid = False
                    break
                cards.extend(rank_groups[r][:3])
            if valid:
                return cards
        return None

    def _find_airplane_with_single_beat(self, hand: List[Card], rank_groups: Dict[int, List[Card]],
                                        beat_rank: int, triple_count: int) -> Optional[List[Card]]:
        """寻找能管上的飞机带单"""
        # 先找飞机主体
        airplane = self._find_airplane_beat(rank_groups, beat_rank, triple_count)
        if not airplane:
            return None

        # 找带的单牌
        airplane_ranks = set()
        for i in range(0, len(airplane), 3):
            airplane_ranks.add(airplane[i].rank)

        single_cards = []
        for rank, cards in rank_groups.items():
            if rank not in airplane_ranks and cards:
                single_cards.append(cards[0])
                if len(single_cards) == triple_count:
                    break

        if len(single_cards) < triple_count:
            return None

        return airplane + single_cards

    def _find_airplane_with_pair_beat(self, hand: List[Card], rank_groups: Dict[int, List[Card]],
                                      beat_rank: int, triple_count: int) -> Optional[List[Card]]:
        """寻找能管上的飞机带对"""
        # 先找飞机主体
        airplane = self._find_airplane_beat(rank_groups, beat_rank, triple_count)
        if not airplane:
            return None

        # 找带的对子
        airplane_ranks = set()
        for i in range(0, len(airplane), 3):
            airplane_ranks.add(airplane[i].rank)

        pair_cards = []
        for rank, cards in sorted(rank_groups.items()):
            if rank not in airplane_ranks and len(cards) >= 2:
                pair_cards.extend(cards[:2])
                if len(pair_cards) == triple_count * 2:
                    break

        if len(pair_cards) < triple_count * 2:
            return None

        return airplane + pair_cards

    def _group_cards_by_rank(self, hand: List[Card]) -> Dict[int, List[Card]]:
        """按牌面值分组"""
        groups = {}
        for card in hand:
            if card.rank not in groups:
                groups[card.rank] = []
            groups[card.rank].append(card)
        return groups

    def notify_game_over(self, winner: str, rule: GameRule):
        """通知游戏结束"""
        pass  # AI 不需要通知
