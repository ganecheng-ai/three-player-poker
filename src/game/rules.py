"""斗地主游戏规则"""
from enum import IntEnum
from typing import List, Optional, Tuple, Dict
from .deck import Card, Deck, sort_cards, cards_to_string
from .cards import HandResult, HandType, analyze_hand, can_play


class GamePhase(IntEnum):
    """游戏阶段"""
    NOT_STARTED = 0
    CALL_LANDLORD = 1   # 叫地主阶段
    PLAYING = 2         # 出牌阶段
    GAME_OVER = 3       # 游戏结束


class PlayerRole(IntEnum):
    """玩家角色"""
    FARMER = 0    # 农民
    LANDLORD = 1  # 地主


class GameRule:
    """斗地主游戏规则类"""

    def __init__(self):
        self.deck = Deck()
        self.players: Dict[int, List[Card]] = {}  # player_id -> hand
        self.roles: Dict[int, PlayerRole] = {}    # player_id -> role
        self.landlord_id: Optional[int] = None    # 地主 ID
        self.bottom_cards: List[Card] = []        # 底牌
        self.phase = GamePhase.NOT_STARTED

        # 出牌相关
        self.current_player_id: Optional[int] = None  # 当前出牌玩家
        self.last_hand: Optional[List[Card]] = None   # 上一手牌
        self.last_hand_player: Optional[int] = None   # 上一手牌的玩家
        self.pass_count = 0  # 连续过牌数

        # 叫地主相关
        self.call_scores: Dict[int, int] = {}  # player_id -> score (0=不叫，1/2/3=叫分)
        self.call_order: List[int] = []        # 叫地主顺序

    def start_game(self, player_ids: List[int]) -> bool:
        """
        开始游戏

        Args:
            player_ids: 玩家 ID 列表（必须 3 人）

        Returns:
            是否成功开始
        """
        if len(player_ids) != 3:
            return False

        self.players = {pid: [] for pid in player_ids}
        self.roles = {pid: PlayerRole.FARMER for pid in player_ids}
        self.landlord_id = None
        self.call_scores = {}
        self.last_hand = None
        self.last_hand_player = None
        self.pass_count = 0

        # 发牌
        hand1, hand2, hand3, bottom_cards = self.deck.deal_three_players()
        self.players[player_ids[0]] = sort_cards(hand1)
        self.players[player_ids[1]] = sort_cards(hand2)
        self.players[player_ids[2]] = sort_cards(hand3)
        self.bottom_cards = bottom_cards

        self.phase = GamePhase.CALL_LANDLORD
        self.call_order = player_ids.copy()

        return True

    def call_landlord(self, player_id: int, score: int) -> bool:
        """
        叫地主

        Args:
            player_id: 玩家 ID
            score: 叫分 (0=不叫，1/2/3=叫分)

        Returns:
            是否有效叫分
        """
        if self.phase != GamePhase.CALL_LANDLORD:
            return False
        if player_id not in self.players:
            return False
        if score not in [0, 1, 2, 3]:
            return False
        if player_id in self.call_scores:
            return False  # 已经叫过了

        self.call_scores[player_id] = score

        # 检查是否所有人都叫过了或有人叫 3 分
        if score == 3:
            # 直接成为地主
            self._set_landlord(player_id)
            return True

        if len(self.call_scores) == 3:
            # 所有人都叫过了，选最高分
            max_score = max(self.call_scores.values())
            if max_score == 0:
                # 没人叫，重新发牌或流局（这里简单处理：第一个玩家当地主）
                self._set_landlord(self.call_order[0])
            else:
                # 选第一个叫最高分的
                for pid in self.call_order:
                    if self.call_scores.get(pid) == max_score:
                        self._set_landlord(pid)
                        break
            return True

        return True

    def _set_landlord(self, player_id: int):
        """设置地主"""
        self.landlord_id = player_id
        self.roles[player_id] = PlayerRole.LANDLORD

        # 地主获得底牌
        self.players[player_id].extend(self.bottom_cards)
        self.players[player_id] = sort_cards(self.players[player_id])

        self.phase = GamePhase.PLAYING
        self.current_player_id = player_id  # 地主先出

    def play_cards(self, player_id: int, cards: List[Card]) -> bool:
        """
        出牌

        Args:
            player_id: 玩家 ID
            cards: 要出的牌

        Returns:
            是否可以出牌
        """
        if self.phase != GamePhase.PLAYING:
            return False
        if player_id != self.current_player_id:
            return False
        if not cards:
            return False

        # 检查手牌中是否有这些牌
        hand = self.players.get(player_id, [])
        hand_ranks = sorted([c.rank for c in hand], reverse=True)
        cards_ranks = sorted([c.rank for c in cards], reverse=True)

        # 简单检查：出的牌必须都在手牌中
        temp_hand = hand.copy()
        for card in cards:
            found = False
            for h_card in temp_hand:
                if h_card.rank == card.rank and h_card.suit == card.suit:
                    temp_hand.remove(h_card)
                    found = True
                    break
            if not found:
                return False

        # 检查牌型是否有效
        result = analyze_hand(cards)
        if result.hand_type == HandType.INVALID:
            return False

        # 检查是否能管上
        if self.last_hand is not None and self.last_hand_player != player_id:
            if not can_play(cards, self.last_hand):
                return False

        # 出牌成功
        for card in cards:
            for h_card in hand:
                if h_card.rank == card.rank and h_card.suit == card.suit:
                    hand.remove(h_card)
                    break

        self.last_hand = cards
        self.last_hand_player = player_id
        self.pass_count = 0

        # 检查是否获胜
        if not hand:
            self._end_game(player_id)
            return True

        # 换下一个玩家
        self._next_player()
        return True

    def pass_turn(self, player_id: int) -> bool:
        """
        过牌/不出

        Args:
            player_id: 玩家 ID

        Returns:
            是否可以过牌
        """
        if self.phase != GamePhase.PLAYING:
            return False
        if player_id != self.current_player_id:
            return False

        # 如果是新的一轮（上家是自己或没有上家），不能过
        if self.last_hand is None or self.last_hand_player == player_id:
            return False

        self.pass_count += 1

        # 如果所有人都过了，开始新的一轮
        if self.pass_count >= 2:
            self.last_hand = None
            self.last_hand_player = None
            self.pass_count = 0

        self._next_player()
        return True

    def _next_player(self):
        """切换到下一个玩家"""
        if not self.players:
            return

        player_ids = list(self.players.keys())
        current_index = player_ids.index(self.current_player_id)
        next_index = (current_index + 1) % len(player_ids)
        self.current_player_id = player_ids[next_index]

    def _end_game(self, winner_id: int):
        """结束游戏"""
        self.phase = GamePhase.GAME_OVER
        # 可以根据 winner_id 和 roles 判断哪方获胜

    def is_game_over(self) -> bool:
        """游戏是否结束"""
        return self.phase == GamePhase.GAME_OVER

    def get_winner_team(self) -> Optional[str]:
        """
        获取获胜队伍

        Returns:
            'landlord' 或 'farmer' 或 None
        """
        if not self.is_game_over():
            return None

        # 找到手牌为 0 的玩家
        for pid, hand in self.players.items():
            if not hand:
                if self.roles.get(pid) == PlayerRole.LANDLORD:
                    return 'landlord'
                else:
                    return 'farmer'
        return None

    def get_current_player(self) -> Optional[int]:
        """获取当前玩家 ID"""
        return self.current_player_id

    def get_player_hand(self, player_id: int) -> List[Card]:
        """获取玩家手牌"""
        return self.players.get(player_id, []).copy()

    def get_landlord(self) -> Optional[int]:
        """获取地主 ID"""
        return self.landlord_id

    def get_player_role(self, player_id: int) -> Optional[PlayerRole]:
        """获取玩家角色"""
        return self.roles.get(player_id)

    def get_next_caller(self) -> Optional[int]:
        """获取下一个叫地主的玩家"""
        if self.phase != GamePhase.CALL_LANDLORD:
            return None

        for pid in self.call_order:
            if pid not in self.call_scores:
                return pid
        return None

    def get_valid_moves(self, hand: List[Card]) -> List[List[Card]]:
        """
        获取手牌中所有有效的出牌组合

        Args:
            hand: 手牌

        Returns:
            所有有效的出牌组合列表
        """
        if not hand:
            return []

        valid_moves = []

        # 如果是自由出牌（上一手是自己或没有上一手）
        if self.last_hand is None or self.last_hand_player == self.current_player_id:
            # 所有有效牌型都可以出
            return self._find_all_valid_hands(hand)

        # 需要管上上一手
        for combo in self._find_all_valid_hands(hand):
            if can_play(combo, self.last_hand):
                valid_moves.append(combo)

        return valid_moves

    def _find_all_valid_hands(self, cards: List[Card]) -> List[List[Card]]:
        """找出所有有效牌型组合"""
        # 简化版：只找基本牌型
        valid = []
        rank_groups: Dict[int, List[Card]] = {}

        for card in cards:
            if card.rank not in rank_groups:
                rank_groups[card.rank] = []
            rank_groups[card.rank].append(card)

        # 单张
        for card in cards:
            valid.append([card])

        # 对子
        for rank, group in rank_groups.items():
            if len(group) >= 2:
                valid.append(group[:2])

        # 三张
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                valid.append(group[:3])

        # 炸弹
        for rank, group in rank_groups.items():
            if len(group) >= 4:
                valid.append(group[:4])

        # 三带一
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                other_ranks = [r for r in rank_groups if r != rank]
                for other_rank in other_ranks:
                    combo = group[:3] + [rank_groups[other_rank][0]]
                    if analyze_hand(combo).hand_type == HandType.TRIPLE_WITH_ONE:
                        valid.append(combo)

        # 三带二
        for rank, group in rank_groups.items():
            if len(group) >= 3:
                other_ranks = [r for r in rank_groups if r != rank and len(rank_groups[r]) >= 2]
                for other_rank in other_ranks:
                    combo = group[:3] + rank_groups[other_rank][:2]
                    if analyze_hand(combo).hand_type == HandType.TRIPLE_WITH_PAIR:
                        valid.append(combo)

        # 王炸
        if 16 in rank_groups and 17 in rank_groups:
            valid.append([Card(16, None), Card(17, None)])

        return valid
