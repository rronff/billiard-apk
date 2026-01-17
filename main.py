# -*- coding: utf-8 -*-
"""
당구 점수판 (Kivy) - 레퍼런스 이미지(오른쪽)와 동일하게 맞춘 레이아웃/색상 버전
핵심:
- 배경: 검정
- 상단 Set Score: 파란 라운드 박스 + 진회색 라운드 버튼(+1/-1)
- 중앙: 회색 큰 판(검정 테두리) + 종료(회색 라운드) + 게임시작(빨강) + 일시정지(파랑)
- 좌/우 점수판: 좌 흰색, 우 노랑, 굵은 검정 테두리
- 하단 점수 버튼: 검정 라운드(+1/-1/초기화)
- 폰트: 맑은 고딕(또는 assets/NanumGothic.ttf)
- 경로 독립(exe/py 모두 동일)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle


# ------------------------
# Window resize policy
# ------------------------
# 너무 좁아지면 어떤 UI든 물리적으로 겹칠 수밖에 없어서 "급속하게 깨짐" 현상이 납니다.
# 그래서 1) 최소 크기를 걸고 2) 최초 설계 비율(가로/세로)을 유지하도록 제한합니다.
MIN_WINDOW_W = 1400
MIN_WINDOW_H = 820
# NOTE:
# 창 비율을 강제로 고정하면서 Window.size 를 콜백에서 계속 건드리면,
# OS/윈도우 매니저 환경에 따라 입력(클릭)이 불안정해질 수 있습니다.
# 안정성을 우선으로 "최소 크기만" 강제하고, 비율 고정은 끕니다.
LOCK_ASPECT_RATIO = False


# ------------------------
# Path helpers
# ------------------------
def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def app_base_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(*parts: str) -> Path:
    return app_base_dir().joinpath(*parts)


# ------------------------
# Korean font
# ------------------------
def pick_korean_font() -> str:
    p1 = resource_path("assets", "NanumGothic.ttf")
    if p1.exists():
        return str(p1)
    p2 = Path(r"C:\Windows\Fonts\malgun.ttf")
    if p2.exists():
        return str(p2)
    return ""


KOREAN_FONT_PATH = pick_korean_font()
KOREAN_FONT_NAME = "KOREAN"
if KOREAN_FONT_PATH:
    LabelBase.register(name=KOREAN_FONT_NAME, fn_regular=KOREAN_FONT_PATH)
else:
    KOREAN_FONT_NAME = ""


def FN():
    return KOREAN_FONT_NAME if KOREAN_FONT_NAME else None


# ------------------------
# Simple scaler
# ------------------------
class Scale:
    def __init__(self):
        self.update()

    def update(self, *_):
        self.w = Window.width
        self.h = Window.height
        self.min_side = min(self.w, self.h)

    def clamp(self, v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    def px(self, factor: float, lo: float, hi: float) -> float:
        return self.clamp(self.min_side * factor, lo, hi)


# ------------------------
# Draw helpers
# ------------------------
class FramedBox(BoxLayout):
    """BoxLayout + 배경/테두리 + 라운드"""
    bg_rgba = ListProperty([1, 1, 1, 1])
    border_rgba = ListProperty([0, 0, 0, 1])
    radius = NumericProperty(0.0)
    border_width = NumericProperty(2.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bgc = Color(*self.bg_rgba)
            self._bgr = RoundedRectangle(pos=self.pos, size=self.size, radius=[(self.radius, self.radius)])
        with self.canvas.after:
            self._bc = Color(*self.border_rgba)
            self._ln = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius),
                            width=self.border_width)
        self.bind(pos=self._redraw, size=self._redraw,
                  bg_rgba=self._recolor, border_rgba=self._recolor,
                  radius=self._redraw, border_width=self._redraw)

    def _recolor(self, *_):
        self._bgc.rgba = self.bg_rgba
        self._bc.rgba = self.border_rgba

    def _redraw(self, *_):
        self._bgr.pos = self.pos
        self._bgr.size = self.size
        self._bgr.radius = [(self.radius, self.radius)]
        self._ln.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
        self._ln.width = self.border_width


class RoundButton(ButtonBehavior, Widget):
    """라운드 버튼(확실하게 색상/모양 고정). 내부에 Label 포함."""
    text = StringProperty("")
    bg_rgba = ListProperty([0.17, 0.21, 0.26, 1])
    border_rgba = ListProperty([0, 0, 0, 1])
    text_rgba = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(14.0)
    border_width = NumericProperty(2.0)
    font_size = NumericProperty(20.0)
    bold = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lbl = Label(text=self.text, color=self.text_rgba, font_name=FN(), bold=self.bold)
        self.lbl.halign = "center"
        self.lbl.valign = "middle"
        self.add_widget(self.lbl)

        with self.canvas.before:
            self._bgc = Color(*self.bg_rgba)
            self._bgr = RoundedRectangle(pos=self.pos, size=self.size, radius=[(self.radius, self.radius)])
        with self.canvas.after:
            self._bc = Color(*self.border_rgba)
            self._ln = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius),
                            width=self.border_width)

        self.bind(pos=self._redraw, size=self._redraw,
                  text=self._sync, bg_rgba=self._recolor, border_rgba=self._recolor,
                  text_rgba=self._sync, radius=self._redraw, border_width=self._redraw,
                  font_size=self._sync, bold=self._sync)

        # press feedback
        self._pressed = False

    def on_press(self):
        self._pressed = True
        # slightly darken
        self._bgc.rgba = [c * 0.92 if i < 3 else c for i, c in enumerate(self.bg_rgba)]

    def on_release(self):
        self._pressed = False
        self._bgc.rgba = self.bg_rgba

    def _sync(self, *_):
        self.lbl.text = self.text
        self.lbl.color = self.text_rgba
        self.lbl.font_size = self.font_size
        self.lbl.bold = self.bold
        self.lbl.font_name = FN()
        self.lbl.text_size = self.lbl.size  # center without wrapping
        self.lbl.halign = "center"
        self.lbl.valign = "middle"

    def _recolor(self, *_):
        if not self._pressed:
            self._bgc.rgba = self.bg_rgba
        self._bc.rgba = self.border_rgba

    def _redraw(self, *_):
        self._bgr.pos = self.pos
        self._bgr.size = self.size
        self._bgr.radius = [(self.radius, self.radius)]
        self._ln.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
        self._ln.width = self.border_width

        self.lbl.pos = self.pos
        self.lbl.size = self.size
        self.lbl.text_size = self.lbl.size


# ------------------------
# Compatibility wrapper
# ------------------------
# 코드 일부에서 RoundedButton(bg_color=..., text_color=...) 형태를 사용하고 있어서
# 이름/인자를 그대로 받아 RoundButton 속성명(bg_rgba/text_rgba)으로 매핑한다.
class RoundedButton(RoundButton):
    """Backward-compatible alias.

    Earlier versions of this project used `bg_color`, `text_color`, and `border_color`.
    The base `RoundButton` uses `*_rgba` names.
    """

    def __init__(
        self,
        *args,
        bg_color=None,
        text_color=None,
        border_color=None,
        border_width=None,
        **kwargs,
    ):
        if bg_color is not None:
            kwargs.setdefault('bg_rgba', bg_color)
        if text_color is not None:
            kwargs.setdefault('text_rgba', text_color)
        if border_color is not None:
            kwargs.setdefault('border_rgba', border_color)
        if border_width is not None:
            kwargs.setdefault('border_width', border_width)
        super().__init__(*args, **kwargs)

# ------------------------
# Player panel
# ------------------------


class PlayerPanel(BoxLayout):
    def __init__(
        self,
        sc: Scale,
        title_text: str,
        bg_color: tuple[float, float, float, float],
        reverse_top: bool = False,
        **kwargs,
    ):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(10), **kwargs)
        self.sc = sc
        self.reverse_top = reverse_top

        # --- state ---
        self.score_value = 0
        self.set_score_value = 0

        # top: set score label + (set score / +1 / -1)
        top = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.lbl_set = Label(
            text="Set Score",
            font_name=FN(),
            color=(1, 1, 1, 1),
            bold=True,
            halign="left" if not reverse_top else "right",
            valign="middle",
            size_hint_y=None,
        )
        self.lbl_set.bind(size=lambda *_: setattr(self.lbl_set, "text_size", self.lbl_set.size))

        row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None)
        self._top_spacer = None
        self.set_score = RoundedButton(
            text="0",
            bg_color=(0.25, 0.45, 0.75, 1),
            text_color=(0, 0, 0, 1),
            bold=True,
            radius=dp(14),
            # NOTE: disabled=True makes the text look faint (Kivy dims disabled widgets).
            # This box is display-only, so we keep it enabled and simply don't bind any click handler.
        )
        self.btn_set_plus = RoundedButton(
            text="+1",
            bg_color=(0.18, 0.22, 0.26, 1),
            text_color=(1, 1, 1, 1),
            bold=True,
            radius=dp(14),
        )
        self.btn_set_minus = RoundedButton(
            text="-1",
            bg_color=(0.18, 0.22, 0.26, 1),
            text_color=(1, 1, 1, 1),
            bold=True,
            radius=dp(14),
        )

        if reverse_top:
            # 오른쪽 패널은 Set Score 행이 우측 기준으로 정렬되어야 한다.
            # BoxLayout은 기본적으로 왼쪽부터 쌓이므로, 가변 스페이서를 앞에 넣어
            # 남는 공간을 스페이서가 먹게 해서 전체를 오른쪽으로 밀어준다.
            self._top_spacer = Widget(size_hint_x=1)
            row.add_widget(self._top_spacer)
            row.add_widget(self.btn_set_plus)
            row.add_widget(self.btn_set_minus)
            row.add_widget(self.set_score)
        else:
            row.add_widget(self.set_score)
            row.add_widget(self.btn_set_plus)
            row.add_widget(self.btn_set_minus)

        top.add_widget(self.lbl_set)
        top.add_widget(row)

        # middle: score panel
        self.score_box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        with self.score_box.canvas.before:
            self._score_bg = Color(*bg_color)
            self._score_rect = Rectangle(pos=self.score_box.pos, size=self.score_box.size)
            self._score_border = Color(0, 0, 0, 1)
            self._score_line = Line(rectangle=(self.score_box.x, self.score_box.y, self.score_box.width, self.score_box.height), width=dp(4))
        self.score_box.bind(pos=self._update_score_canvas, size=self._update_score_canvas)

        self.lbl_title = Label(
            text=title_text,
            font_name=FN(),
            color=(0, 0, 0, 1),
            bold=True,
            size_hint_y=None,
            halign="center",
            valign="middle",
        )
        self.lbl_title.bind(size=lambda *_: setattr(self.lbl_title, "text_size", self.lbl_title.size))

        self.lbl_score = Label(
            text="0",
            font_name=FN(),
            color=(0, 0, 0, 1),
            bold=True,
            halign="center",
            valign="middle",
        )
        self.lbl_score.bind(size=lambda *_: setattr(self.lbl_score, "text_size", self.lbl_score.size))

        self.score_box.add_widget(self.lbl_title)
        self.score_box.add_widget(self.lbl_score)

        # bottom controls
        bottom = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None)
        self.btn_plus = RoundedButton(
            text="+1",
            bg_color=(0.12, 0.14, 0.16, 1),
            text_color=(1, 1, 1, 1),
            bold=True,
            radius=dp(14),
        )
        self.btn_minus = RoundedButton(
            text="-1",
            bg_color=(0.12, 0.14, 0.16, 1),
            text_color=(1, 1, 1, 1),
            bold=True,
            radius=dp(14),
        )
        self.btn_reset = RoundedButton(
            text="초기화",
            bg_color=(0.12, 0.14, 0.16, 1),
            text_color=(1, 1, 1, 1),
            bold=True,
            radius=dp(14),
        )
        bottom.add_widget(self.btn_plus)
        bottom.add_widget(self.btn_minus)
        bottom.add_widget(self.btn_reset)

        self.add_widget(top)
        self.add_widget(self.score_box)
        self.add_widget(bottom)

        # events
        self.btn_plus.bind(on_release=lambda *_: self.change_score(+1))
        self.btn_minus.bind(on_release=lambda *_: self.change_score(-1))
        self.btn_reset.bind(on_release=lambda *_: self.reset_score())

        self.btn_set_plus.bind(on_release=lambda *_: self.change_set_score(+1))
        self.btn_set_minus.bind(on_release=lambda *_: self.change_set_score(-1))

        self._row = row
        self._top = top
        self._bottom = bottom

        # IMPORTANT
        # 이 패널은 상단 Set Score 영역에서 size_hint_x=None + width 고정 값을 쓰므로,
        # 레이아웃이 "패널 폭"을 확정한 뒤에도 한 번 더 스케일을 재적용해야
        # 상단 버튼이 아래 점수판(흰/노랑 박스) 범위를 넘어가는 현상을 막을 수 있다.
        # (창을 줄일 때 특히 심해짐)
        self._scale_trigger = Clock.create_trigger(lambda *_: self.apply_scale(), 0)
        self.bind(size=lambda *_: self._scale_trigger())

        self.apply_scale()

    def _sync_score_labels(self):
        self.lbl_score.text = str(self.score_value)
        self.set_score.text = str(self.set_score_value)

    def change_score(self, delta: int):
        self.score_value += int(delta)
        # 점수는 음수로 내려가지 않게
        if self.score_value < 0:
            self.score_value = 0
        self._sync_score_labels()

    def reset_score(self):
        self.score_value = 0
        self._sync_score_labels()

    def change_set_score(self, delta: int):
        self.set_score_value += int(delta)
        if self.set_score_value < 0:
            self.set_score_value = 0
        self._sync_score_labels()

    def _update_score_canvas(self, *_):
        self._score_rect.pos = self.score_box.pos
        self._score_rect.size = self.score_box.size
        self._score_line.rectangle = (self.score_box.x, self.score_box.y, self.score_box.width, self.score_box.height)

    def apply_scale(self):
        # font sizes
        # "Set Score" label should be clearly readable (about 3x bigger than before)
        fs_set = self.sc.px(0.090, 18, 78)
        self.lbl_set.font_size = fs_set
        self.lbl_set.height = fs_set * 1.4

        fs_setscore = self.sc.px(0.060, 18, 44)
        self.set_score.font_size = fs_setscore

        fs_btn = self.sc.px(0.040, 14, 34)
        self.btn_set_plus.font_size = fs_btn
        self.btn_set_minus.font_size = fs_btn

        fs_title = self.sc.px(0.090, 22, 84)
        self.lbl_title.font_size = fs_title
        self.lbl_title.height = fs_title * 1.5

        fs_big = self.sc.px(0.270, 60, 230)
        self.lbl_score.font_size = fs_big

        fs_bottom = self.sc.px(0.050, 16, 44)
        self.btn_plus.font_size = fs_bottom
        self.btn_minus.font_size = fs_bottom
        self.btn_reset.font_size = fs_bottom

        # heights
        row_h = self.sc.px(0.085, 44, 90)
        self._row.height = row_h
        self._top.height = self.lbl_set.height + row_h + dp(6)
        # Base target widths from scale
        base_btn_w = self.sc.px(0.18, 54, 160)
        base_score_w = self.sc.px(0.48, 120, 340)

        # Make the 3 widgets (score box + +1/-1) ALWAYS fit within this panel
        # and also EXPAND to fill the available width (so it aligns with the
        # score panel below and doesn't look cramped).
        #
        # Available width = panel width - left/right padding - gaps between widgets
        # We keep the base ratio (score:button) and scale up/down to fill.

        # padding can be: (l,t,r,b) or (x,y) or scalar
        pad_l = pad_r = 0.0
        try:
            p = list(self.padding)  # type: ignore[arg-type]
            if len(p) == 4:
                pad_l, _, pad_r, _ = p
            elif len(p) == 2:
                pad_l = pad_r = p[0]
            elif len(p) == 1:
                pad_l = pad_r = p[0]
        except Exception:
            if self.padding:
                pad_l = pad_r = float(self.padding)

        # "상단 Set Score 행"은 아래 score_box(흰/노랑 박스)와 좌우 끝이 일치해야 한다.
        # panel(self)의 내부 폭과 score_box 폭이 미세하게 다를 수 있으니,
        # score_box 폭을 기준으로 우선 계산한다(값이 아직 0이면 panel 기준으로 fallback).
        panel_inner = max(0.0, float(self.width) - float(pad_l) - float(pad_r))
        score_box_w = float(getattr(self.score_box, 'width', 0.0) or 0.0)
        avail = score_box_w if score_box_w > 1.0 else panel_inner
        gap = float(self._row.spacing)
        # 오른쪽 패널은 앞에 스페이서가 하나 더 있어서 gap이 3개가 된다.
        gap_cnt = 3.0 if self.reverse_top else 2.0
        total_avail = max(0.0, avail - gap_cnt * gap)

        base_total = float(base_score_w) + 2.0 * float(base_btn_w)
        if base_total <= 0 or total_avail <= 0:
            score_w = float(base_score_w)
            btn_w = float(base_btn_w)
        else:
            s = total_avail / base_total
            # Avoid over-growing too much on very large windows
            s = min(s, 1.6)

            # 오른쪽 패널(reverse_top)은 "우측 정렬"을 위해 스페이서가 남는 폭을 먹도록
            # 상단 3개 위젯이 가득 채우지 않고(=남는 공간을 만들고) 비율대로 커/줄게 한다.
            if self.reverse_top:
                score_w = float(base_score_w) * s
                btn_w = float(base_btn_w) * s
                # 최소 폭 보장
                btn_w = max(btn_w, dp(44))
                score_w = max(score_w, dp(80))

                # 그래도 넘치면(아주 작은 창) 비율로 다시 줄인다.
                need = score_w + 2.0 * btn_w
                if need > total_avail and need > 0:
                    k = total_avail / need
                    score_w *= k
                    btn_w *= k
            else:
                score_w = float(base_score_w) * s
                btn_w = float(base_btn_w) * s

                # Minimum safety so buttons don't become unusably small
                btn_w = max(btn_w, dp(44))
                # Recompute score_w to exactly fill (after min clamp)
                score_w = max(0.0, total_avail - 2.0 * btn_w)

        for w in (self.set_score, self.btn_set_plus, self.btn_set_minus):
            w.size_hint_x = None
            w.size_hint_y = None
            w.height = row_h

        # right-align spacer keeps size_hint_x=1, only height is fixed
        if self._top_spacer is not None:
            self._top_spacer.size_hint_y = None
            self._top_spacer.height = row_h

        self.btn_set_plus.width = btn_w
        self.btn_set_minus.width = btn_w
        self.set_score.width = score_w

        bottom_h = self.sc.px(0.100, 60, 110)
        self._bottom.height = bottom_h
        for w in (self.btn_plus, self.btn_minus, self.btn_reset):
            w.size_hint_y = 1






class ColoredPanel(BoxLayout):
    def __init__(
        self,
        bg_color=(0.1, 0.1, 0.1, 1),
        radius=dp(12),
        border_color=(0, 0, 0, 1),
        border_width=dp(3),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.border_color = border_color
        self.border_width = border_width
        with self.canvas.before:
            self._bg = Color(*bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
            self._bcol = Color(*border_color)
            self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, radius), width=border_width)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)


class CenterPanel(BoxLayout):
    def __init__(self, sc: Scale, on_exit=None, **kwargs):
        # NOTE: RootUI passes on_exit callback. We must not forward it to BoxLayout.
        super().__init__(orientation="vertical", spacing=dp(10), **kwargs)
        self.sc = sc
        self._on_exit = on_exit

        # state
        # game_active: 게임이 시작(진행/일시정지 포함) 상태인지
        # running: 타이머가 실제로 흘러가고 있는지(일시정지면 False)
        self.game_active = False
        self.paused = False
        self.running = False
        self.session_seconds = 0.0
        self.total_seconds = 0.0
        self._clock_ev = None

        # 상단 높이 정렬용 컨테이너
        # - 중앙 회색판(board) 상단이 좌/우 점수판(score_box) 상단과 일치해야 함
        # - 종료 버튼은 상단 Set Score의 +1/-1 버튼(=row)의 상/하단과 일치해야 함
        # 따라서 PlayerPanel의 top 영역(라벨 + 버튼 row)과 "같은 높이"를 갖는 top_bar를 만들고,
        # 그 안에서 라벨 높이만큼 spacer를 둔 뒤 종료 버튼을 row 높이로 배치한다.
        self.top_bar = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self._top_spacer = Widget(size_hint_y=None, height=0)

        # exit button
        self.btn_exit = RoundedButton(
            text="종료",
            bg_color=(0.55, 0.55, 0.55, 1),
            text_color=(0, 0, 0, 1),
            bold=True,
            radius=dp(14),
            border_color=(0, 0, 0, 1),
            border_width=dp(2),
            size_hint_y=None,
        )

        # main grey board
        self.board = ColoredPanel(
            orientation="vertical",
            bg_color=(0.55, 0.55, 0.55, 1),
            radius=dp(12),
            border_color=(0, 0, 0, 1),
            border_width=dp(3),
            padding=(dp(10), dp(10)),
            spacing=dp(10),
        )

        self.timer = Label(
            text="00 : 00 : 00",
            color=(0, 0, 0, 1),
            font_name=FN(),
            bold=True,
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            size_hint_y=None,
        )

        # Spacer: increase the vertical gap between the timer and the start button
        # so the timer sits higher in the gray board.
        self._timer_spacer = Widget(size_hint_y=None, height=0)

        self.btn_start = RoundedButton(
            text="게임시작",
            bg_color=(0.80, 0.00, 0.00, 1),
            text_color=(0, 0, 0, 1),
            bold=True,
            radius=dp(14),
            border_color=(0, 0, 0, 1),
            border_width=dp(2),
            size_hint_y=None,
        )
        self.btn_pause = RoundedButton(
            text="일시정지",
            bg_color=(0.00, 0.65, 0.95, 1),
            text_color=(0, 0, 0, 1),
            bold=True,
            radius=dp(14),
            border_color=(0, 0, 0, 1),
            border_width=dp(2),
            size_hint_y=None,
        )

        # total time panel
        self.total_panel = ColoredPanel(
            orientation="vertical",
            bg_color=(0.05, 0.05, 0.06, 1),
            radius=dp(10),
            border_color=(0, 0, 0, 1),
            border_width=dp(2),
            padding=(dp(10), dp(10)),
            spacing=dp(8),
            size_hint_y=None,
        )
        self.total_title = Label(
            text="총 게임시간",
            color=(1, 1, 1, 1),
            font_name=FN(),
            bold=True,
            halign="center",
            valign="middle",
            size_hint_y=None,
        )
        self.total_title.bind(size=lambda *_: setattr(self.total_title, "text_size", (self.total_title.width, self.total_title.height)))

        self.total_timer = Label(
            text="00 : 00 : 00",
            color=(1, 1, 1, 1),
            font_name=FN(),
            bold=True,
            halign="center",
            valign="middle",
            shorten=True,
            shorten_from="right",
            size_hint_y=None,
        )

        self.btn_total_reset = RoundedButton(
            text="시간초기화",
            bg_color=(0.00, 0.65, 0.95, 1),
            text_color=(0, 0, 0, 1),
            bold=True,
            radius=dp(14),
            border_color=(0, 0, 0, 1),
            border_width=dp(2),
            size_hint_y=None,
        )

        # '시간초기화'는 게임이 '종료'된 이후에만 활성화
        self._set_total_reset_enabled(False)

        self.total_panel.add_widget(self.total_title)
        self.total_panel.add_widget(self.total_timer)
        self.total_panel.add_widget(self.btn_total_reset)

        self.board.add_widget(self.timer)
        self.board.add_widget(self._timer_spacer)
        self.board.add_widget(self.btn_start)
        self.board.add_widget(self.btn_pause)
        self.board.add_widget(self.total_panel)

        self.top_bar.add_widget(self._top_spacer)
        self.top_bar.add_widget(self.btn_exit)

        self.add_widget(self.top_bar)
        self.add_widget(self.board)

        # events
        self.btn_exit.bind(on_release=lambda *_: self._on_exit() if callable(self._on_exit) else None)
        self.btn_start.bind(on_release=lambda *_: self.start_game())
        self.btn_pause.bind(on_release=lambda *_: self.pause_game())
        self.btn_total_reset.bind(on_release=lambda *_: self.reset_total_time())

        # The timer labels use font sizes computed from the *current* widget widths.
        # When the window is resized, layout widths are updated slightly later,
        # so we re-apply scaling once the sizes settle to prevent text crossing panel edges.
        self._scale_trigger = Clock.create_trigger(lambda *_: self.apply_scale(), 0)
        self.bind(size=lambda *_: self._scale_trigger())
        self.board.bind(size=lambda *_: self._scale_trigger())
        self.total_panel.bind(size=lambda *_: self._scale_trigger())

        self.apply_scale()

    def _fmt(self, sec: float) -> str:
        sec = max(0, int(sec))
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d} : {m:02d} : {s:02d}"

    def apply_scale(self):
        h = max(1, self.height)

        # ------------------------------
        # Top alignment (IMPORTANT)
        # ------------------------------
        # - 중앙 회색판(board) 상단이 좌/우 점수판(score_box) 상단과 일치해야 함
        # - 종료 버튼은 상단 Set Score의 +1/-1 버튼(row)의 상/하단과 일치해야 함
        # PlayerPanel.apply_scale()의 기준 값을 그대로 사용한다.
        fs_set = self.sc.px(0.090, 18, 78)
        label_h = fs_set * 1.4
        row_h = self.sc.px(0.085, 44, 90)

        self._top_spacer.height = label_h
        self.btn_exit.height = row_h
        # 종료 버튼 폰트는 +1/-1 버튼과 비슷한 체감 크기로
        self.btn_exit.font_size = self.sc.px(0.040, 14, 34)

        self.top_bar.height = label_h + row_h + dp(6)

        # board padding/spacing (fixed dp is OK, scale adjusts overall)
        self.board.padding = (dp(10), dp(10))
        self.board.spacing = dp(10)

        # timer label (keep inside gray board width)
        # (요청 취소) 시계 글자 크기: 기본 스케일 값으로 복구
        fs_timer = self.sc.px(0.070, 18, 80)
        # Clamp by available width so the text never crosses the gray board edges.
        # Rough glyph width ~= 0.62 * font_size per char for this kind of text.
        pad_x = dp(10) * 2
        avail_w = max(dp(60), self.board.width - pad_x)
        text_len = max(1, len(self.timer.text))
        fs_by_w = max(dp(12), avail_w / (text_len * 0.62))
        fs_timer = min(fs_timer, fs_by_w)
        self.timer.font_size = fs_timer
        self.timer.height = fs_timer * 1.45
        self.timer.text_size = (avail_w, self.timer.height)
        self.timer.halign = 'center'
        self.timer.valign = 'middle'

        # Move the timer upward by increasing the gap below it.
        # (요청 취소) 이전 단계(위로 4배 올림) 수준으로 복구
        self._timer_spacer.height = self.board.spacing * 2

        # main buttons (keep inside the gray board)
        bh = max(dp(44), min(self.sc.px(0.090, 52, 120), h * 0.16))
        self.btn_start.font_size = min(self.sc.px(0.050, 16, 54), bh * 0.48)
        self.btn_pause.font_size = min(self.sc.px(0.050, 16, 54), bh * 0.48)
        self.btn_start.height = bh
        self.btn_pause.height = bh

        # total panel
        title_fs = min(self.sc.px(0.045, 14, 44), bh * 0.42)
        time_fs = min(self.sc.px(0.065, 18, 70), max(dp(16), self.board.width * 0.11))
        # Clamp total timer too so it never crosses the black total panel edges.
        pad_x2 = dp(10) * 2
        avail_w2 = max(dp(40), self.total_panel.width - pad_x2)
        text_len2 = max(1, len(self.total_timer.text))
        fs_by_w2 = max(dp(12), avail_w2 / (text_len2 * 0.62))
        time_fs = min(time_fs, fs_by_w2)
        self.total_title.font_size = title_fs
        self.total_title.height = title_fs * 1.3
        self.total_timer.font_size = time_fs
        self.total_timer.height = time_fs * 1.35
        self.total_timer.text_size = (avail_w2, self.total_timer.height)
        self.total_timer.halign = 'center'
        self.total_timer.valign = 'middle'
        self.btn_total_reset.font_size = min(self.sc.px(0.045, 14, 44), bh * 0.42)
        self.btn_total_reset.height = max(dp(40), min(self.sc.px(0.085, 48, 110), h * 0.14))

        # total panel height packs children + padding
        self.total_panel.height = (
            self.total_title.height
            + self.total_timer.height
            + self.btn_total_reset.height
            + dp(10) * 2
            + self.total_panel.spacing * 2
        )

        # Final safeguard: if the gray board is too short, shrink the two middle buttons
        # so they never overflow outside the board.
        # We now have 5 widgets inside board (timer, spacer, start, pause, total_panel) -> 4 gaps
        avail = self.board.height - (dp(10) * 2) - (self.board.spacing * 4)
        need = (
            self.timer.height
            + self._timer_spacer.height
            + self.total_panel.height
            + (self.btn_start.height + self.btn_pause.height)
        )
        if avail > 0 and need > avail:
            bh2 = max(dp(34), (avail - self.timer.height - self._timer_spacer.height - self.total_panel.height) / 2)
            self.btn_start.height = bh2
            self.btn_pause.height = bh2
            self.btn_start.font_size = min(self.btn_start.font_size, bh2 * 0.48)
            self.btn_pause.font_size = min(self.btn_pause.font_size, bh2 * 0.48)

    def _set_total_reset_enabled(self, enabled: bool):
        """'시간초기화'는 게임이 '종료'된 이후에만 활성화."""
        self.btn_total_reset.disabled = not enabled
        # 시각적으로도 구분
        self.btn_total_reset.opacity = 1.0 if enabled else 0.35

    def start_game(self):
        """게임시작/게임종료 토글.

        - 게임이 아직 시작 전이면: 시작(타이머 진행)
        - 이미 게임이 시작된 상태면(진행/일시정지 포함): 종료(세션 타이머 초기화)
        """
        if not self.game_active:
            # start
            self.game_active = True
            self.paused = False
            self.running = True
            self.btn_start.text = "게임종료"
            self.btn_pause.text = "일시정지"
            self._set_total_reset_enabled(False)
            if self._clock_ev is None:
                self._clock_ev = Clock.schedule_interval(self._tick, 1 / 30.0)
            return

        # end game
        self.game_active = False
        self.paused = False
        self.running = False
        self.session_seconds = 0.0
        self.timer.text = "00 : 00 : 00"
        self.btn_start.text = "게임시작"
        self.btn_pause.text = "일시정지"
        self._set_total_reset_enabled(True)

    def pause_game(self):
        """일시정지/해체(재개) 토글."""
        if not self.game_active:
            return

        if not self.paused:
            # pause
            self.paused = True
            self.running = False
            self.btn_pause.text = "일시정지해체"
        else:
            # resume
            self.paused = False
            self.running = True
            self.btn_pause.text = "일시정지"


    def reset_total_time(self):
        # '게임종료'를 누르기 전(=버튼 비활성/게임 진행중)에는 시간초기화 금지
        if self.game_active or self.btn_total_reset.disabled:
            return
        self.total_seconds = 0.0
        self.total_timer.text = "00 : 00 : 00"

    def _tick(self, dt):
        if not self.running:
            return
        self.session_seconds += dt
        self.total_seconds += dt
        self.timer.text = self._fmt(self.session_seconds)
        self.total_timer.text = self._fmt(self.total_seconds)

class RootUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.sc = Scale()

        # 최초 설계 비율(가로/세로)을 저장해두고, 창을 줄일 때도 이 비율을 유지한다.
        self._design_ratio = (Window.width / Window.height) if Window.height else 16 / 9
        self._resize_guard = False

        # FULL black background
        with self.canvas.before:
            self._bgc = Color(0, 0, 0, 1)
            self._bgr = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._bg_update, size=self._bg_update)

        self.spacing = dp(22)
        self.padding = [dp(22), dp(22), dp(22), dp(22)]

        self.left_panel = PlayerPanel(self.sc, title_text="선수 1번", bg_color=(1, 1, 1, 1), reverse_top=False, size_hint=(0.40, 1))
        self.center_panel = CenterPanel(self.sc, on_exit=self.open_exit_popup, size_hint=(0.20, 1))
        self.right_panel = PlayerPanel(self.sc, title_text="선수 2번", bg_color=(1.0, 0.78, 0.0, 1), reverse_top=True, size_hint=(0.40, 1))

        self.add_widget(self.left_panel)
        self.add_widget(self.center_panel)
        self.add_widget(self.right_panel)

        # 창 크기 변경 시, 고정 폭/높이를 쓰는 커스텀 위젯(특히 Set Score 행)이
        # 레이아웃처럼 같이 축소/확대되도록 스케일 재적용
        Window.bind(size=self._on_window_resize)
        Clock.schedule_once(self._apply_all_scales, 0)

    def _on_window_resize(self, *_):
        # NOTE:
        # Window.size 를 여기서 강제로 조정하면(특히 maximized 상태/윈도우 환경)
        # 입력(클릭)이 이상해질 수 있어서, 여기서는 "스케일 재적용"만 합니다.
        # 최소 창 크기는 Window.minimum_width/height 로만 제한합니다.
        Clock.schedule_once(self._apply_all_scales, 0)

    def _apply_all_scales(self, *_):
        self.sc.update()
        # PlayerPanel/CenterPanel 내부에서 min_side 기반으로 width/height/font가 다시 계산됨
        self.left_panel.apply_scale()
        self.right_panel.apply_scale()
        self.center_panel.apply_scale()

    def _bg_update(self, *_):
        self._bgr.pos = self.pos
        self._bgr.size = self.size

    def open_exit_popup(self):
        box = BoxLayout(orientation="vertical", spacing=dp(14), padding=[dp(18), dp(18), dp(18), dp(18)])
        lbl = Label(text="프로그램을 정말로 종료하시겠습니까 ?", color=(0, 0, 0, 1), font_name=FN())
        lbl.halign = "center"
        lbl.valign = "middle"
        lbl.bind(size=lambda *_: setattr(lbl, "text_size", lbl.size))

        row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None)
        btn_yes = RoundButton(text="예", bg_rgba=[0.55, 0.55, 0.55, 1], text_rgba=[0, 0, 0, 1],
                              border_rgba=[0, 0, 0, 1], radius=dp(14), border_width=dp(2), bold=True)
        btn_no = RoundButton(text="아니요", bg_rgba=[0.55, 0.55, 0.55, 1], text_rgba=[0, 0, 0, 1],
                             border_rgba=[0, 0, 0, 1], radius=dp(14), border_width=dp(2), bold=True)

        popup = Popup(title="", content=box, size_hint=(0.55, 0.35), auto_dismiss=False)

        btn_yes.bind(on_release=lambda *_: App.get_running_app().stop())
        btn_no.bind(on_release=lambda *_: popup.dismiss())

        row.add_widget(btn_yes)
        row.add_widget(btn_no)
        box.add_widget(lbl)
        box.add_widget(row)

        def scale_popup(*_):
            self.sc.update()
            row.height = self.sc.px(0.06, 42, 95)
            lbl.font_size = self.sc.px(0.040, 16, 52)
            btn_yes.font_size = self.sc.px(0.035, 14, 44)
            btn_no.font_size = self.sc.px(0.035, 14, 44)

        scale_popup()
        Window.bind(size=scale_popup)
        popup.open()


class BilliardScoreboardApp(App):
    def build(self):
        self.title = "당구 점수판"
        # 너무 작은 창에서는 레이아웃이 물리적으로 겹칠 수밖에 없어서
        # 최소 크기를 지정해 "깨짐" 구간으로 내려가지 않게 한다.
        try:
            Window.minimum_width = int(MIN_WINDOW_W)
            Window.minimum_height = int(MIN_WINDOW_H)
        except Exception:
            pass
        return RootUI()

    def on_start(self):
        try:
            Window.maximize()
        except Exception:
            pass


if __name__ == "__main__":
    BilliardScoreboardApp().run()