# 斗地主 (Three Player Poker)

经典的三人斗地主游戏，使用 Python 和 Pygame 开发，支持简体中文界面。

## 游戏特色

- **经典玩法**: 完整的斗地主游戏规则，包括叫地主、出牌、炸弹、王炸等
- **精美界面**: 绿色牌桌背景，清晰的卡牌显示
- **智能 AI**: 两个电脑对手，具有叫分和出牌策略
- **简体中文**: 完整的中文化界面
- **跨平台**: 支持 Windows、Linux、macOS

## 牌型说明

| 牌型 | 说明 | 示例 |
|------|------|------|
| 单张 | 任意一张牌 | 3, 4, 5...2, A, K |
| 对子 | 两张点数相同的牌 | 33, 44, 55... |
| 三张 | 三张点数相同的牌 | 333, 444... |
| 三带一 | 三张相同 + 一张单牌 | 333+4 |
| 三带二 | 三张相同 + 一对牌 | 333+44 |
| 顺子 | 五张或以上连续单牌 | 34567, 45678... |
| 连对 | 三个或以上连续对子 | 334455, 445566... |
| 飞机 | 两个或以上连续三张 | 333444, 444555... |
| 炸弹 | 四张相同点数 | 3333, 4444... |
| 王炸 | 大王 + 小王 | 最大牌型 |

## 安装说明

### 从源码运行

1. 确保已安装 Python 3.10 或更高版本

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行游戏：
   ```bash
   python -m src.main
   ```

### 下载安装包

从 [Releases](https://github.com/ganecheng-ai/three-player-poker/releases) 页面下载对应操作系统的安装包：

- **Windows**: `three-player-poker-windows.zip`
- **Linux**: `three-player-poker-linux.tar.gz`
- **macOS**: `three-player-poker-macos.tar.gz`

## 游戏操作

### 键盘快捷键

| 按键 | 功能 |
|------|------|
| R | 重新开始游戏 |
| ESC | 退出游戏 |
| 空格 | 出牌（已选牌时） |

### 鼠标操作

- **点击卡牌**: 选择/取消选择要出的牌
- **点击按钮**: 执行对应操作（叫分、出牌、过牌等）

## 游戏规则

1. **发牌**: 54 张牌，三人各 17 张，底牌 3 张
2. **叫地主**: 玩家轮流叫分（1/2/3 分或不叫），最高分者成为地主并获得底牌
3. **出牌**: 地主先出，按逆时针顺序轮流，下家必须出相同牌型且更大的牌或选择过牌
4. **获胜**: 先出完所有手牌的一方获胜（地主一方 vs 农民两方）

## 项目结构

```
three-player-poker/
├── src/
│   ├── main.py           # 游戏入口
│   ├── game/
│   │   ├── deck.py       # 扑克牌和牌堆
│   │   ├── cards.py      # 牌型定义和比较
│   │   ├── rules.py      # 游戏规则
│   │   └── state.py      # 游戏状态管理
│   ├── player/
│   │   ├── human.py      # 人类玩家
│   │   └── ai.py         # AI 玩家
│   └── ui/
│       └── screen.py     # 屏幕渲染
├── locales/
│   └── zh_CN/
│       └── messages.json # 中文翻译
├── tests/
│   ├── test_deck.py      # 卡牌测试
│   └── test_rules.py     # 规则测试
├── .github/workflows/
│   └── build.yml         # CI/CD 配置
├── requirements.txt      # 依赖列表
├── plan.md              # 项目规划
└── README.md            # 本文件
```

## 开发

### 运行测试

```bash
python -m unittest discover -s tests
```

### 构建可执行文件

```bash
pyinstaller --onefile --name three-player-poker --windowed src/main.py
```

## 版本发布

1. 确保所有测试通过
2. 创建新的 git tag：`git tag v0.1.0`
3. 推送 tag：`git push origin v0.1.0`
4. GitHub Actions 会自动构建并发布

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！
