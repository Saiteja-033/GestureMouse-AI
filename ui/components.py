"""
GestureMouse AI - UI Components Module
Reusable CustomTkinter widgets and cards for a modern, sleek dark dashboard.
"""

import customtkinter as ctk
from typing import Callable, Optional, Any


# Theme Palette
COLOR_BG_DARK = "#0F141C"
COLOR_CARD_BG = "#1A2230"
COLOR_CARD_BORDER = "#26354A"
COLOR_ACCENT_GREEN = "#00E676"
COLOR_ACCENT_CYAN = "#00E5FF"
COLOR_ACCENT_RED = "#FF5252"
COLOR_ACCENT_YELLOW = "#FFD600"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#90A4AE"
COLOR_TEXT_MUTED = "#546E7A"


class StatusCard(ctk.CTkFrame):
    """
    Dashboard card displaying a metric, status label, and colored indicator light.
    """

    def __init__(
        self,
        master: Any,
        title: str,
        initial_value: str = "---",
        indicator_color: str = COLOR_ACCENT_GREEN,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=10,
            **kwargs
        )

        self.title_label = ctk.CTkLabel(
            self,
            text=title.upper(),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        self.title_label.pack(anchor="w", padx=14, pady=(10, 2))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=14, pady=(0, 10))

        # Glowing dot indicator
        self.dot_canvas = ctk.CTkCanvas(
            self.content_frame,
            width=12,
            height=12,
            bg=COLOR_CARD_BG,
            highlightthickness=0,
        )
        self.dot_canvas.pack(side="left", padx=(0, 8))
        self.dot_id = self.dot_canvas.create_oval(
            2, 2, 10, 10, fill=indicator_color, outline=""
        )

        self.value_label = ctk.CTkLabel(
            self.content_frame,
            text=initial_value,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.value_label.pack(side="left", fill="x", expand=True)

    def set_value(self, value: str, color: Optional[str] = None):
        """Update label value and optionally text color."""
        self.value_label.configure(text=value)
        if color:
            self.value_label.configure(text_color=color)

    def set_indicator_color(self, hex_color: str):
        """Update glowing indicator dot color."""
        self.dot_canvas.itemconfig(self.dot_id, fill=hex_color)


class SliderControl(ctk.CTkFrame):
    """
    Labeled slider with dynamic numeric readout and title.
    """

    def __init__(
        self,
        master: Any,
        label: str,
        from_val: float,
        to_val: float,
        initial_val: float,
        on_change: Callable[[float], None],
        unit: str = "",
        is_float: bool = True,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label_text = label
        self.unit = unit
        self.is_float = is_float
        self.on_change = on_change

        # Top row: Title and current value
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 4))

        self.title_lbl = ctk.CTkLabel(
            top_frame,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.title_lbl.pack(side="left")

        val_display = f"{initial_val:.2f}{unit}" if is_float else f"{int(initial_val)}{unit}"
        self.val_lbl = ctk.CTkLabel(
            top_frame,
            text=val_display,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_ACCENT_CYAN,
        )
        self.val_lbl.pack(side="right")

        # Slider bar
        self.slider = ctk.CTkSlider(
            self,
            from_=from_val,
            to=to_val,
            number_of_steps=50,
            command=self._handle_change,
            button_color=COLOR_ACCENT_GREEN,
            button_hover_color="#00C853",
            progress_color=COLOR_ACCENT_GREEN,
            fg_color="#26354A",
            height=16,
        )
        self.slider.set(initial_val)
        self.slider.pack(fill="x")

    def _handle_change(self, val: float):
        if self.is_float:
            display = f"{val:.2f}{self.unit}"
        else:
            val = round(val)
            display = f"{int(val)}{self.unit}"
        self.val_lbl.configure(text=display)
        self.on_change(val)

    def set_value(self, val: float):
        self.slider.set(val)
        self._handle_change(val)


class GestureCard(ctk.CTkFrame):
    """
    Instruction card displaying gesture description and visual status.
    """

    def __init__(
        self,
        master: Any,
        gesture_name: str,
        action_name: str,
        icon_str: str = "🖐",
        **kwargs
    ):
        super().__init__(
            master,
            fg_color="#141B24",
            border_color="#222C3A",
            border_width=1,
            corner_radius=8,
            **kwargs
        )

        left = ctk.CTkLabel(
            self,
            text=icon_str,
            font=ctk.CTkFont(size=18),
            width=36,
        )
        left.pack(side="left", padx=(10, 4), pady=6)

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, pady=4)

        g_lbl = ctk.CTkLabel(
            mid,
            text=gesture_name,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        g_lbl.pack(anchor="w")

        a_lbl = ctk.CTkLabel(
            mid,
            text=action_name,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_ACCENT_GREEN,
            anchor="w",
        )
        a_lbl.pack(anchor="w")
