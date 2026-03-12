"""游戏状态管理"""
from typing import Dict, List, Optional, Any
from enum import IntEnum
import json

from .deck import Card, Deck, sort_cards
from .cards import HandType, analyze_hand, can_play
from .rules import GameRule, GamePhase, PlayerRole


class GameState:
    """游戏状态类 - 用于序列化和恢复游戏"""

    def __init__(self):
        self.players: Dict[int, List[Dict]] = {}  # player_id -> cards (serialized)
        self.roles: Dict[int, int] = {}
        self.landlord_id: Optional[int] = None
        self.bottom_cards: List[Dict] = []
        self.phase: int = 0
        self.current_player_id: Optional[int] = None
        self.last_hand: Optional[List[Dict]] = None
        self.last_hand_player: Optional[int] = None
        self.pass_count: int = 0
        self.call_scores: Dict[int, int] = {}
        self.winner: Optional[str] = None

    @classmethod
    def from_rule(cls, rule: GameRule) -> 'GameState':
        """从 GameRule 创建 GameState"""
        state = cls()
        state.players = {
            pid: [{'rank': c.rank, 'suit': c.suit.value if c.suit else None}
                  for c in hand]
            for pid, hand in rule.players.items()
        }
        state.roles = {pid: int(role.value) for pid, role in rule.roles.items()}
        state.landlord_id = rule.landlord_id
        state.bottom_cards = [{'rank': c.rank, 'suit': c.suit.value if c.suit else None}
                              for c in rule.bottom_cards]
        state.phase = int(rule.phase.value)
        state.current_player_id = rule.current_player_id
        state.last_hand = (
            [{'rank': c.rank, 'suit': c.suit.value if c.suit else None} for c in rule.last_hand]
            if rule.last_hand else None
        )
        state.last_hand_player = rule.last_hand_player
        state.pass_count = rule.pass_count
        state.call_scores = rule.call_scores.copy()
        state.winner = rule.get_winner_team()
        return state

    def to_rule(self) -> GameRule:
        """从 GameState 恢复 GameRule"""
        rule = GameRule()
        rule.players = {
            pid: [Card(c['rank'], Suit(c['suit']) if c['suit'] else None)
                  for c in cards]
            for pid, cards in self.players.items()
        }
        rule.roles = {pid: PlayerRole(role) for pid, role in self.roles.items()}
        rule.landlord_id = self.landlord_id
        rule.bottom_cards = [Card(c['rank'], Suit(c['suit']) if c['suit'] else None)
                             for c in self.bottom_cards]
        rule.phase = GamePhase(self.phase)
        rule.current_player_id = self.current_player_id
        rule.last_hand = (
            [Card(c['rank'], Suit(c['suit']) if c['suit'] else None)
             for c in self.last_hand]
            if self.last_hand else None
        )
        rule.last_hand_player = self.last_hand_player
        rule.pass_count = self.pass_count
        rule.call_scores = self.call_scores.copy()
        return rule

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'players': self.players,
            'roles': self.roles,
            'landlord_id': self.landlord_id,
            'bottom_cards': self.bottom_cards,
            'phase': self.phase,
            'current_player_id': self.current_player_id,
            'last_hand': self.last_hand,
            'last_hand_player': self.last_hand_player,
            'pass_count': self.pass_count,
            'call_scores': self.call_scores,
            'winner': self.winner,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """从字典创建"""
        state = cls()
        state.players = data.get('players', {})
        state.roles = data.get('roles', {})
        state.landlord_id = data.get('landlord_id')
        state.bottom_cards = data.get('bottom_cards', [])
        state.phase = data.get('phase', 0)
        state.current_player_id = data.get('current_player_id')
        state.last_hand = data.get('last_hand')
        state.last_hand_player = data.get('last_hand_player')
        state.pass_count = data.get('pass_count', 0)
        state.call_scores = data.get('call_scores', {})
        state.winner = data.get('winner')
        return state

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'GameState':
        """从 JSON 字符串创建"""
        return cls.from_dict(json.loads(json_str))


# 导入 Suit 用于反序列化
from .deck import Suit
