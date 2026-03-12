"""屏幕管理和渲染"""
import pygame
from typing import Optional, Tuple, List, Dict, Any
from ..game.deck import Card, Suit
from ..game.rules import GameRule, PlayerRole


# 颜色定义
COLOR_BACKGROUND = (15, 82, 45)  # 深绿色背景（牌桌）
COLOR_BACKGROUND_GRADIENT_TOP = (25, 100, 55)  # 渐变顶部
COLOR_BACKGROUND_GRADIENT_BOTTOM = (10, 60, 35)  # 渐变底部
COLOR_CARD_BACK = (41, 128, 185)  # 卡牌背面蓝色
COLOR_CARD_BACK_PATTERN = (52, 152, 219)  # 卡牌背面图案
COLOR_CARD_WHITE = (255, 255, 255)  # 卡牌白色区域
COLOR_CARD_RED = (231, 76, 60)  # 红色花色
COLOR_CARD_BLACK = (44, 62, 80)  # 黑色花色
COLOR_TEXT = (255, 255, 255)  # 白色文字
COLOR_TEXT_SHADOW = (0, 0, 0)  # 文字阴影
COLOR_GOLD = (241, 196, 15)  # 金色
COLOR_GOLD_BRIGHT = (255, 215, 0)  # 亮金色
COLOR_BUTTON_PRIMARY = (52, 152, 219)  # 蓝色按钮
COLOR_BUTTON_HOVER = (41, 128, 185)  # 悬停蓝色
COLOR_BUTTON_DISABLED = (127, 140, 141)  # 禁用灰色
COLOR_BUTTON_SUCCESS = (46, 204, 113)  # 绿色按钮
COLOR_BUTTON_WARNING = (243, 156, 18)  # 橙色按钮
COLOR_LANDLORD = (241, 196, 15)  # 地主金色
COLOR_FARMER = (52, 152, 219)  # 农民蓝色
COLOR_SHADOW = (0, 0, 0, 100)  # 阴影色


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
        self.button_text: Dict[str, str] = {}
        self.button_callbacks: Dict[str, Any] = {}

        # 选中状态
        self.selected_cards: List[int] = []  # 选中的牌索引

    def initialize(self):
        """初始化 Pygame"""
        pygame.init()
        pygame.display.set_caption("斗地主 - Three Player Poker")

        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        # 初始化字体
        pygame.font.init()

        # 加载中文字体
        chinese_font_paths = [
            "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",  # 文泉驿正黑
            "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",  # 文泉驿微米黑
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Ubuntu path
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Noto CJK
            "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows 微软雅黑
            "C:\\Windows\\Fonts\\simhei.ttf",  # Windows 黑体
        ]

        font_loaded = False
        for font_path in chinese_font_paths:
            try:
                self.chinese_font = pygame.font.Font(font_path, 36)
                self.font_large = pygame.font.Font(font_path, 48)
                self.font_medium = pygame.font.Font(font_path, 36)
                self.font_small = pygame.font.Font(font_path, 24)
                font_loaded = True
                break
            except Exception:
                continue

        if not font_loaded:
            # 如果没有找到中文字体，使用默认字体
            self.chinese_font = pygame.font.Font(None, 36)
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)

        # 创建桌面渐变效果
        self.background_surface = self._create_gradient_background()

    def quit(self):
        """退出 Pygame"""
        pygame.quit()

    def clear(self):
        """清屏"""
        if self.screen:
            if hasattr(self, 'background_surface') and self.background_surface:
                self.screen.blit(self.background_surface, (0, 0))
            else:
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

        # 绘制阴影
        shadow_rect = pygame.Rect(x + 3, draw_y + 3, self.card_width, self.card_height)
        shadow_surface = pygame.Surface((self.card_width, self.card_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=8)
        self.screen.blit(shadow_surface, (x + 3, draw_y + 3))

        if not face_up:
            # 画牌背
            rect = pygame.Rect(x, draw_y, self.card_width, self.card_height)
            pygame.draw.rect(self.screen, COLOR_CARD_BACK, rect, border_radius=8)
            self._draw_card_back_pattern(rect)
            return rect

        # 画牌面
        rect = pygame.Rect(x, draw_y, self.card_width, self.card_height)
        pygame.draw.rect(self.screen, COLOR_CARD_WHITE, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_CARD_BLACK, rect, width=2, border_radius=8)

        # 确定花色颜色
        is_red = card.suit in [Suit.HEARTS, Suit.DIAMONDS] if card.suit else False
        color = COLOR_CARD_RED if is_red else COLOR_CARD_BLACK

        # 大王小王特殊处理
        if card.is_high_joker:
            # 大王 - 红色渐变背景
            gradient_rect = pygame.Rect(x + 5, draw_y + 5, self.card_width - 10, self.card_height - 10)
            pygame.draw.rect(self.screen, (255, 240, 240), gradient_rect, border_radius=5)
            text = self.font_medium.render("大王", True, COLOR_CARD_RED)
            text_rect = text.get_rect(center=(x + self.card_width // 2,
                                               y + self.card_height // 2))
            self.screen.blit(text, text_rect)
            # 添加装饰星号
            star_text = self.font_small.render("★", True, COLOR_GOLD)
            self.screen.blit(star_text, (x + self.card_width // 2 - 10, draw_y + 10))
        elif card.is_low_joker:
            # 小王 - 黑色
            text = self.font_medium.render("小王", True, COLOR_CARD_BLACK)
            text_rect = text.get_rect(center=(x + self.card_width // 2,
                                               y + self.card_height // 2))
            self.screen.blit(text, text_rect)
            # 添加装饰月亮
            moon_text = self.font_small.render("☾", True, COLOR_CARD_BLACK)
            self.screen.blit(moon_text, (x + self.card_width // 2 - 10, draw_y + 10))
        else:
            # 左上角显示牌面值
            rank_text = self.font_small.render(card.short_name, True, color)
            self.screen.blit(rank_text, (x + 5, draw_y + 5))

            # 中间显示花色（带阴影效果）
            suit_symbol = self._get_suit_symbol(card.suit)
            if suit_symbol:
                # 阴影
                suit_text_shadow = self.font_large.render(suit_symbol, True, (200, 200, 200))
                suit_rect_shadow = suit_text_shadow.get_rect(center=(x + self.card_width // 2 + 1,
                                                        y + self.card_height // 2 + 1))
                self.screen.blit(suit_text_shadow, suit_rect_shadow)
                # 本体
                suit_text = self.font_large.render(suit_symbol, True, color)
                suit_rect = suit_text.get_rect(center=(x + self.card_width // 2,
                                                        y + self.card_height // 2))
                self.screen.blit(suit_text, suit_rect)

            # 右下角显示倒置牌面值
            rank_text_bottom = self.font_small.render(card.short_name, True, color)
            rotated = pygame.transform.rotate(rank_text_bottom, 180)
            self.screen.blit(rotated, (x + self.card_width - 25,
                                        draw_y + self.card_height - 20))

        # 选中边框（发光效果）
        if selected:
            # 外发光
            glow_rect = pygame.Rect(x - 2, draw_y - 2, self.card_width + 4, self.card_height + 4)
            pygame.draw.rect(self.screen, COLOR_GOLD_BRIGHT, glow_rect, width=4, border_radius=10)
            # 内边框
            pygame.draw.rect(self.screen, COLOR_GOLD, rect, width=3, border_radius=8)

        return rect

    def _get_suit_symbol(self, suit) -> str:
        """获取花色符号"""
        if suit is None:
            return ""
        symbols = {
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
            Suit.HEARTS: "♥",
            Suit.SPADES: "♠",
        }
        return symbols.get(suit, "")

    def _create_gradient_background(self) -> pygame.Surface:
        """创建渐变背景"""
        surface = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            ratio = y / self.height
            r = int(COLOR_BACKGROUND_GRADIENT_TOP[0] * (1 - ratio) + COLOR_BACKGROUND_GRADIENT_BOTTOM[0] * ratio)
            g = int(COLOR_BACKGROUND_GRADIENT_TOP[1] * (1 - ratio) + COLOR_BACKGROUND_GRADIENT_BOTTOM[1] * ratio)
            b = int(COLOR_BACKGROUND_GRADIENT_TOP[2] * (1 - ratio) + COLOR_BACKGROUND_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))
        return surface

    def _draw_card_back_pattern(self, rect: pygame.Rect):
        """绘制卡牌背面图案"""
        if not self.screen:
            return
        # 绘制菱形图案
        center_x = rect.centerx
        center_y = rect.centery
        # 外框
        pygame.draw.rect(self.screen, COLOR_CARD_BACK_PATTERN, rect, width=3, border_radius=8)
        # 中心菱形
        points = [
            (center_x, rect.top + 15),
            (rect.right - 15, center_y),
            (center_x, rect.bottom - 15),
            (rect.left + 15, center_y)
        ]
        pygame.draw.polygon(self.screen, COLOR_CARD_BACK_PATTERN, points)
        # 中心圆
        pygame.draw.circle(self.screen, COLOR_CARD_BACK_PATTERN, (center_x, center_y), 12, 2)

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
        role_color = COLOR_TEXT
        if role == PlayerRole.LANDLORD:
            role_text = "（地主）"
            role_color = COLOR_LANDLORD
        elif role == PlayerRole.FARMER:
            role_text = "（农民）"
            role_color = COLOR_FARMER

        # 绘制名称（带阴影）
        name_with_role = f"{name}{role_text}"
        text_shadow = self.font_medium.render(name_with_role, True, COLOR_TEXT_SHADOW)
        self.screen.blit(text_shadow, (x + 1, y + 1))

        name_text = self.font_medium.render(name_with_role, True, role_color)
        self.screen.blit(name_text, (x, y))

        # 剩余牌数（带背景框）
        card_text = self.font_small.render(f"剩余：{card_count} 张", True, COLOR_TEXT)
        # 绘制半透明背景
        text_width = card_text.get_width() + 10
        text_height = card_text.get_height() + 4
        bg_rect = pygame.Rect(x, y + 28, text_width, text_height)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect, border_radius=4)
        self.screen.blit(card_text, (x + 5, y + 30))

    def draw_bottom_cards(self, cards: List[Card], x: int, y: int):
        """绘制底牌"""
        if not self.screen:
            return

        # 绘制标签（带背景）
        label = self.font_medium.render("底牌:", True, COLOR_GOLD)
        label_bg_rect = pygame.Rect(x - 5, y - 5, label.get_width() + 10, label.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), label_bg_rect, border_radius=5)
        self.screen.blit(label, (x, y))

        # 绘制底牌（带边框）
        for i, card in enumerate(cards):
            card_x = x + 60 + i * (self.card_width - 40)
            # 绘制底牌外框
            card_rect = pygame.Rect(card_x - 2, y - 2, self.card_width + 4, self.card_height + 4)
            pygame.draw.rect(self.screen, COLOR_GOLD, card_rect, width=2, border_radius=10)
            self.draw_card(card, card_x, y, face_up=True)

    def create_button(self, name: str, text: str, x: int, y: int,
                      width: int = 120, height: int = 40,
                      callback=None) -> pygame.Rect:
        """创建按钮"""
        rect = pygame.Rect(x, y, width, height)
        self.buttons[name] = rect
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
        text = self.button_text.get(name, name)

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

        # 绘制按钮阴影
        shadow_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
        shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=8)
        self.screen.blit(shadow_surface, (rect.x + 2, rect.y + 2))

        # 绘制按钮
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_TEXT, rect, width=2, border_radius=8)

        # 悬停效果 - 高亮边框
        if hovered and enabled:
            hover_rect = pygame.Rect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4)
            pygame.draw.rect(self.screen, COLOR_GOLD, hover_rect, width=2, border_radius=10)

        # 绘制文字（带阴影）
        text_surface_shadow = self.font_medium.render(text, True, COLOR_TEXT_SHADOW)
        text_rect_shadow = text_surface_shadow.get_rect(center=(rect.centerx + 1, rect.centery + 1))
        self.screen.blit(text_surface_shadow, text_rect_shadow)

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

        # 绘制阴影
        text_shadow = font.render(message, True, COLOR_TEXT_SHADOW)
        self.screen.blit(text_shadow, (x + 1, y + 1))

        # 绘制文字
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
