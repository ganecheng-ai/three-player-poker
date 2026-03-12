"""屏幕管理和渲染"""
import pygame
from typing import Optional, Tuple, List, Dict, Any
from ..game.deck import Card
from ..game.rules import GameRule, PlayerRole


# 颜色定义
COLOR_BACKGROUND = (15, 82, 45)  # 深绿色背景（牌桌）
COLOR_CARD_BACK = (41, 128, 185)  # 卡牌背面蓝色
COLOR_CARD_WHITE = (255, 255, 255)  # 卡牌白色区域
COLOR_CARD_RED = (231, 76, 60)  # 红色花色
COLOR_CARD_BLACK = (44, 62, 80)  # 黑色花色
COLOR_TEXT = (255, 255, 255)  # 白色文字
COLOR_GOLD = (241, 196, 15)  # 金色
COLOR_BUTTON_PRIMARY = (52, 152, 219)  # 蓝色按钮
COLOR_BUTTON_HOVER = (41, 128, 185)  # 悬停蓝色
COLOR_BUTTON_DISABLED = (127, 140, 141)  # 禁用灰色


class GameScreen:
    """游戏屏幕管理类"""

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.Clock] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.chinese_font: Optional[pygame.font.Font] = None

        # 卡牌尺寸
        self.card_width = 80
        self.card_height = 110

        # 按钮
        self.buttons: Dict[str, pygame.Rect] = {}
        self.button_callbacks: Dict[str, Any] = {}

        # 选中状态
        self.selected_cards: List[int] = []  # 选中的牌索引

    def initialize(self):
        """初始化 Pygame"""
        pygame.init()
        pygame.display.set_caption("斗地主")

        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.clock.Clock()

        # 初始化字体
        pygame.font.init()
        try:
            # 尝试加载中文字体
            self.chinese_font = pygame.font.Font(None, 36)
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)

    def quit(self):
        """退出 Pygame"""
        pygame.quit()

    def clear(self):
        """清屏"""
        if self.screen:
            self.screen.fill(COLOR_BACKGROUND)

    def draw_card(self, card: Card, x: int, y: int,
                  face_up: bool = True, selected: bool = False) -> pygame.Rect:
        """
        绘制一张牌

        Args:
            card: 卡牌对象
            x, y: 位置
            face_up: 是否明牌
            selected: 是否选中

        Returns:
            牌的矩形区域
        """
        if not self.screen:
            return pygame.Rect(x, y, self.card_width, self.card_height)

        # 选中时向上偏移
        draw_y = y - 15 if selected else y

        if not face_up:
            # 画牌背
            rect = pygame.Rect(x, draw_y, self.card_width, self.card_height)
            pygame.draw.rect(self.screen, COLOR_CARD_BACK, rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_TEXT, rect, width=2, border_radius=8)
            return rect

        # 画牌面
        rect = pygame.Rect(x, draw_y, self.card_width, self.card_height)
        pygame.draw.rect(self.screen, COLOR_CARD_WHITE, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_CARD_BLACK, rect, width=2, border_radius=8)

        # 确定花色颜色
        is_red = card.suit in [Card.HEARTS, Card.DIAMONDS] if card.suit else False
        color = COLOR_CARD_RED if is_red else COLOR_CARD_BLACK

        # 大王小王特殊处理
        if card.is_high_joker:
            # 大王 - 红色
            text = self.font_medium.render("大王", True, COLOR_CARD_RED)
            text_rect = text.get_rect(center=(x + self.card_width // 2,
                                               y + self.card_height // 2))
            self.screen.blit(text, text_rect)
        elif card.is_low_joker:
            # 小王 - 黑色
            text = self.font_medium.render("小王", True, COLOR_CARD_BLACK)
            text_rect = text.get_rect(center=(x + self.card_width // 2,
                                               y + self.card_height // 2))
            self.screen.blit(text, text_rect)
        else:
            # 左上角显示牌面值
            rank_text = self.font_small.render(card.short_name, True, color)
            self.screen.blit(rank_text, (x + 5, draw_y + 5))

            # 中间显示花色
            suit_symbol = self._get_suit_symbol(card.suit)
            if suit_symbol:
                suit_text = self.font_large.render(suit_symbol, True, color)
                suit_rect = suit_text.get_rect(center=(x + self.card_width // 2,
                                                        y + self.card_height // 2))
                self.screen.blit(suit_text, suit_rect)

            # 右下角显示倒置牌面值
            rank_text_bottom = self.font_small.render(card.short_name, True, color)
            rotated = pygame.transform.rotate(rank_text_bottom, 180)
            self.screen.blit(rotated, (x + self.card_width - 25,
                                        draw_y + self.card_height - 20))

        # 选中边框
        if selected:
            pygame.draw.rect(self.screen, COLOR_GOLD, rect, width=3, border_radius=8)

        return rect

    def _get_suit_symbol(self, suit) -> str:
        """获取花色符号"""
        if suit is None:
            return ""
        symbols = {
            Card.DIAMONDS: "♦",
            Card.CLUBS: "♣",
            Card.HEARTS: "♥",
            Card.SPADES: "♠",
        }
        return symbols.get(suit, "")

    def draw_hand(self, cards: List[Card], start_x: int, start_y: int,
                  overlap: int = 25, selectable: bool = True) -> List[pygame.Rect]:
        """
        绘制手牌

        Args:
            cards: 手牌列表
            start_x, start_y: 起始位置
            overlap: 牌之间的重叠

        Returns:
            每张牌的矩形区域列表
        """
        rects = []
        for i, card in enumerate(cards):
            x = start_x + i * (self.card_width - overlap)
            selected = i in self.selected_cards
            rect = self.draw_card(card, x, start_y, face_up=True, selected=selected)
            rects.append(rect)
        return rects

    def draw_player_info(self, player_id: int, name: str, role: Optional[PlayerRole],
                         card_count: int, x: int, y: int):
        """绘制玩家信息"""
        if not self.screen:
            return

        # 玩家名称
        role_text = ""
        if role == PlayerRole.LANDLORD:
            role_text = "（地主）"
        elif role == PlayerRole.FARMER:
            role_text = "（农民）"

        name_text = self.font_medium.render(f"{name}{role_text}", True, COLOR_TEXT)
        self.screen.blit(name_text, (x, y))

        # 剩余牌数
        card_text = self.font_small.render(f"剩余：{card_count} 张", True, COLOR_TEXT)
        self.screen.blit(card_text, (x, y + 30))

    def draw_bottom_cards(self, cards: List[Card], x: int, y: int):
        """绘制底牌"""
        if not self.screen:
            return

        label = self.font_small.render("底牌:", True, COLOR_TEXT)
        self.screen.blit(label, (x, y))

        for i, card in enumerate(cards):
            self.draw_card(card, x + 60 + i * (self.card_width - 40), y, face_up=True)

    def create_button(self, name: str, text: str, x: int, y: int,
                      width: int = 120, height: int = 40,
                      callback=None) -> pygame.Rect:
        """创建按钮"""
        rect = pygame.Rect(x, y, width, height)
        self.buttons[name] = rect
        self.button_text = getattr(self, 'button_text', {})
        self.button_text[name] = text
        if callback:
            self.button_callbacks[name] = callback
        return rect

    def draw_button(self, name: str, enabled: bool = True) -> bool:
        """
        绘制按钮

        Returns:
            是否被鼠标悬停
        """
        if not self.screen or name not in self.buttons:
            return False

        rect = self.buttons[name]
        text = self.button_text.get(name, name) if hasattr(self, 'button_text') else name

        # 检查鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)

        # 确定颜色
        if not enabled:
            color = COLOR_BUTTON_DISABLED
        elif hovered:
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON_PRIMARY

        # 绘制按钮
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_TEXT, rect, width=2, border_radius=8)

        # 绘制文字
        text_surface = self.font_medium.render(text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

        return hovered

    def draw_message(self, message: str, x: int, y: int,
                     size: str = "medium", color=COLOR_TEXT):
        """绘制消息文字"""
        if not self.screen:
            return

        if size == "large":
            font = self.font_large
        elif size == "small":
            font = self.font_small
        else:
            font = self.font_medium

        text = font.render(message, True, color)
        self.screen.blit(text, (x, y))

    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        处理点击事件

        Returns:
            点击的按钮名称
        """
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return name
        return None

    def handle_card_click(self, cards: List[Card], pos: Tuple[int, int],
                          start_x: int, start_y: int,
                          overlap: int = 25) -> Optional[int]:
        """
        处理卡牌点击

        Returns:
            点击的牌索引
        """
        for i in range(len(cards)):
            x = start_x + i * (self.card_width - overlap)
            rect = pygame.Rect(x, start_y, self.card_width, self.card_height)
            if rect.collidepoint(pos):
                return i
        return None

    def update(self):
        """更新屏幕"""
        if self.screen:
            pygame.display.flip()
            if self.clock:
                self.clock.tick(60)

    def wait_for_event(self) -> Optional[pygame.event.Event]:
        """等待事件"""
        if self.clock:
            return pygame.event.wait()
        return None

    def poll_events(self) -> List[pygame.event.Event]:
        """轮询事件"""
        return list(pygame.event.get())
