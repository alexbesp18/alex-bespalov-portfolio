#!/usr/bin/env python3
"""
Stock Options Tracker UI (Mac-friendly, always-light).

Pure white background, pure black text everywhere – even inside wx.Choice and date pickers.
Shared COLUMN_WIDTHS so headers and widgets line up perfectly.
Works on wxPython 4.1 → 4.2.
"""

import datetime
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any

import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled

from src.config import settings

APP_NAME = "Stock Options Configuration"

# ─── Colours ───────────────────────────────────────────────────────────────────
WHITE = wx.Colour(255, 255, 255)
LIGHT_GRAY = wx.Colour(248, 248, 248)
GRAY_BAR = wx.Colour(245, 245, 245)
BLACK = wx.Colour(0, 0, 0)
RED_BG = wx.Colour(255, 80, 80)
GREEN_BG = wx.Colour(0, 180, 80)
BLUE_MAC = wx.Colour(0, 122, 255)

# ─── Column widths (px) – keep in sync with widget sizes ──────────────────────
COLS = {
    "ticker": 110,
    "price": 90,
    "type": 70,
    "month": 100,
    "year": 70,
    "date": 120,
}

# ─── Helpers ───────────────────────────────────────────────────────────────────


def iso_to_wx(date_str: str) -> wx.DateTime:
    """Convert 'YYYY-MM-DD' → wx.DateTime, safe on wxPython 4.1.

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        wx.DateTime object, or current date if conversion fails.
    """
    try:
        y, m, d = map(int, date_str.split("-"))
        return wx.DateTime.FromDMY(d, m - 1, y)  # wx months are 0-based
    except Exception:
        return wx.DateTime.Now()


def paint_black(ctrl: wx.Window) -> None:
    """Force the control (and its inner text field) to use black text.

    Args:
        ctrl: wxPython window control to style.
    """
    ctrl.SetOwnForegroundColour(BLACK)
    if hasattr(ctrl, "GetTextCtrl") and ctrl.GetTextCtrl():
        ctrl.GetTextCtrl().SetForegroundColour(BLACK)


# ─── Main Frame ────────────────────────────────────────────────────────────────


class StockOptionsFrame(wx.Frame):
    """Main application frame for stock options configuration."""

    def __init__(self, parent: Optional[wx.Window] = None) -> None:
        """Initialize the frame.

        Args:
            parent: Parent window, if any.
        """
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        super().__init__(parent, title=APP_NAME, size=(1020, 650), style=style)

        self.is_mac = platform.system() == "Darwin"
        if self.is_mac:
            try:
                self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)  # force light appearance
            except wx.wxAssertionError:
                pass

        self.config_file = settings.get_config_path()

        self.panel = scrolled.ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        self.panel.SetupScrolling(scroll_x=False, rate_y=20)
        self.panel.SetBackgroundColour(WHITE)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self._build_header()
        self._build_column_headers()
        self._build_rows_container()
        self.vbox.AddSpacer(20)  # bottom padding
        self.panel.SetSizer(self.vbox)

        self.CreateStatusBar()
        self.rows: List[Dict[str, Any]] = []  # list of widget dicts
        self.load_config()
        self.Centre()
        self.Show()

    # ── UI Builders ───────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        """Build the header panel with title and save button."""
        pnl = wx.Panel(self.panel)
        pnl.SetBackgroundColour(WHITE)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(pnl, label=APP_NAME)
        title.SetFont(
            wx.Font(
                16 if self.is_mac else 14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
            )
        )
        title.SetForegroundColour(BLACK)

        save_btn = wx.Button(pnl, label="Save Changes")
        if self.is_mac:
            save_btn.SetBackgroundColour(BLUE_MAC)
            save_btn.SetForegroundColour(WHITE)
        save_btn.Bind(wx.EVT_BUTTON, self.save_config)

        hbox.Add(title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)
        hbox.AddStretchSpacer()
        hbox.Add(save_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)
        pnl.SetSizer(hbox)
        self.vbox.Add(pnl, 0, wx.EXPAND)
        self.vbox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    def _build_column_headers(self) -> None:
        """Build the column header row."""

        def add_header(text: str, width: int) -> None:
            """Add a header label.

            Args:
                text: Header text.
                width: Column width in pixels.
            """
            lbl = wx.StaticText(pnl, label=text)
            lbl.SetFont(
                wx.Font(
                    11 if self.is_mac else 10,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD,
                )
            )
            lbl.SetForegroundColour(BLACK)
            hbox.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            spacer = width - lbl.GetBestSize().GetWidth()
            hbox.AddSpacer(spacer if spacer > 0 else 0)

        pnl = wx.Panel(self.panel)
        pnl.SetBackgroundColour(GRAY_BAR)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        hbox.AddSpacer(45)  # for + button
        hbox.AddSpacer(35)  # for checkbox
        add_header("Ticker", COLS["ticker"])
        add_header("Strike Price", COLS["price"])
        add_header("Type", COLS["type"])
        add_header("Month", COLS["month"])
        add_header("Year", COLS["year"])
        add_header("Start Date", COLS["date"])
        add_header("End Date", COLS["date"])

        pnl.SetSizer(hbox)
        pnl.SetMinSize((-1, 35))
        self.vbox.Add(pnl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

    def _build_rows_container(self) -> None:
        """Build the container for configuration rows."""
        self.rows_panel = wx.Panel(self.panel)
        self.rows_panel.SetBackgroundColour(WHITE)
        self.rows_sizer = wx.BoxSizer(wx.VERTICAL)
        self.rows_panel.SetSizer(self.rows_sizer)
        self.vbox.Add(
            self.rows_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10
        )

    # ── Config I/O ────────────────────────────────────────────────────────────

    def load_config(self) -> None:
        """Load configuration from file."""
        self.rows_sizer.Clear(delete_windows=True)
        self.rows.clear()
        if self.config_file.exists():
            try:
                for line in self.config_file.read_text().splitlines():
                    if line.strip():
                        self.add_row(data=json.loads(line))
                self.SetStatusText(f"Loaded {len(self.rows)} row(s) from {self.config_file}")
            except Exception as e:
                self.SetStatusText(f"Error loading config: {e}")
                self.add_row()
        else:
            self.add_row()
            self.SetStatusText("No config file – starting fresh.")
        self._refresh_rows()

    def save_config(self, _evt: Optional[wx.CommandEvent] = None) -> None:
        """Save configuration to file.

        Args:
            _evt: Event object (unused).
        """
        data_out = []
        for idx, w in enumerate(self.rows, 1):
            ticker = w["ticker"].GetValue().strip()
            if not ticker:
                self.SetStatusText(f"Row {idx}: ticker cannot be empty")
                return
            if w["start"].GetValue() > w["end"].GetValue():
                self.SetStatusText(f"Row {idx}: start date after end date")
                return
            data_out.append(
                {
                    "enabled": w["chk"].IsChecked(),
                    "ticker": ticker,
                    "price": w["price"].GetValue(),
                    "type": w["type"].GetStringSelection(),
                    "month": w["month"].GetStringSelection(),
                    "year": w["year"].GetValue(),
                    "start_date": w["start"].GetValue().FormatISODate(),
                    "end_date": w["end"].GetValue().FormatISODate(),
                    "strike": 0.0,  # Default values for fields not in GUI
                    "otm_min": 0.0,
                    "otm_max": 100.0,
                    "open_interest": 0,
                }
            )
        try:
            self.config_file.write_text("\n".join(json.dumps(r) for r in data_out))
            self.SetStatusText("Changes saved ✓")
        except Exception as e:
            self.SetStatusText(f"Error saving config: {e}")

    # ── Row management ───────────────────────────────────────────────────────

    def add_row(self, idx: int = -1, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a new configuration row.

        Args:
            idx: Index to insert at, or -1 to append.
            data: Optional data dictionary to pre-populate fields.
        """
        w = self._make_row_widgets()
        if data:  # pre-populate
            w["chk"].SetValue(data.get("enabled", True))
            w["ticker"].SetValue(data.get("ticker", ""))
            w["price"].SetValue(data.get("price", 100.0))
            w["type"].SetStringSelection(data.get("type", "Call"))
            w["month"].SetStringSelection(data.get("month", "January"))
            w["year"].SetValue(data.get("year", str(datetime.datetime.now().year)))
            w["start"].SetValue(iso_to_wx(data.get("start_date", "")))
            w["end"].SetValue(iso_to_wx(data.get("end_date", "")))
        if idx == -1:
            idx = len(self.rows)
        self.rows_sizer.Insert(idx, w["panel"], 0, wx.EXPAND | wx.BOTTOM, 2)
        self.rows.insert(idx, w)
        self._refresh_rows()
        self.panel.Layout()
        self.panel.FitInside()

    def _delete_row(self, w: Dict[str, Any]) -> None:
        """Delete a configuration row.

        Args:
            w: Widget dictionary for the row to delete.
        """
        self.rows.remove(w)
        w["panel"].Destroy()
        self._refresh_rows()
        self.panel.Layout()
        self.panel.FitInside()

    def _refresh_rows(self) -> None:
        """Refresh row styling and enable/disable delete buttons."""
        last = len(self.rows) == 1
        for i, w in enumerate(self.rows):
            w["del"].Enable(not last)
            bg = WHITE if i % 2 == 0 else LIGHT_GRAY
            w["panel"].SetBackgroundColour(bg)
            for c in w["panel"].GetChildren():
                if not isinstance(
                    c, (wx.Button, wx.Choice, wx.adv.DatePickerCtrl, wx.SpinCtrlDouble)
                ):
                    c.SetBackgroundColour(bg)

    # ── Row factory ──────────────────────────────────────────────────────────

    def _make_row_widgets(self) -> Dict[str, Any]:
        """Create widgets for a configuration row.

        Returns:
            Dictionary containing all widget references for the row.
        """
        p = wx.Panel(self.rows_panel)
        h = wx.BoxSizer(wx.HORIZONTAL)
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        plus = wx.Button(p, label="+", size=(40, 25), style=wx.BORDER_NONE)
        plus.SetBackgroundColour(GREEN_BG)
        plus.SetForegroundColour(WHITE)

        chk = wx.CheckBox(p)
        ticker = wx.TextCtrl(p, size=(COLS["ticker"], -1))
        paint_black(ticker)
        price = wx.SpinCtrlDouble(
            p, value="100.00", min=0.0, max=1e5, inc=0.01, size=(COLS["price"], -1)
        )
        price.SetDigits(2)
        paint_black(price)
        typ = wx.Choice(p, choices=["Call", "Put"], size=(COLS["type"], -1))
        typ.SetSelection(0)
        paint_black(typ)
        month = wx.Choice(p, choices=months, size=(COLS["month"], -1))
        month.SetSelection(0)
        paint_black(month)
        year = wx.TextCtrl(
            p, value=str(datetime.datetime.now().year), size=(COLS["year"], -1)
        )
        paint_black(year)

        sz = (COLS["date"], -1)
        DateCtrl = (
            wx.adv.GenericDatePickerCtrl if self.is_mac else wx.adv.DatePickerCtrl
        )
        start = DateCtrl(p, size=sz)
        paint_black(start)
        end = DateCtrl(p, size=sz)
        paint_black(end)
        end_dt = wx.DateTime.Now()
        end_dt.Add(wx.DateSpan(days=30))
        end.SetValue(end_dt)

        w: Dict[str, Any] = {
            "panel": p,
            "chk": chk,
            "ticker": ticker,
            "price": price,
            "type": typ,
            "month": month,
            "year": year,
            "start": start,
            "end": end,
        }

        delete = wx.Button(p, label="×", size=(40, 25), style=wx.BORDER_NONE)
        delete.SetBackgroundColour(RED_BG)
        delete.SetForegroundColour(WHITE)
        delete.Bind(wx.EVT_BUTTON, lambda e: self._delete_row(w))
        w["del"] = delete

        plus.Bind(wx.EVT_BUTTON, lambda e: self.add_row(self.rows.index(w) + 1))

        def pad(ctrl: wx.Window) -> None:
            h.Add(ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        h.Add(plus, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        h.Add(chk, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        for ctrl in (ticker, price, typ, month, year, start, end, delete):
            pad(ctrl)
        p.SetSizer(h)
        return w


# ─── main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    """Main entry point for GUI application."""
    app = wx.App(False)
    if platform.system() == "Darwin":
        try:
            app.SetHighDPIAware()
        except AttributeError:
            pass
    StockOptionsFrame()
    app.MainLoop()


if __name__ == "__main__":
    main()

