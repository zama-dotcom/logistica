"""
Custom QStyledItemDelegate for rendering payment status badges.

Paints 'Pagado' (Paid) cells in green and 'Pendiente' (Pending) cells in red
with rounded badge styling in QTableView cells.
"""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QWidget,
)


# Badge color definitions
STATUS_COLORS: dict[str, dict[str, str]] = {
    "Aprobado": {
        "background": "#1b5e20",
        "text": "#81c784",
        "border": "#4caf50",
    },
    "Pendiente": {
        "background": "#b71c1c",
        "text": "#ef9a9a",
        "border": "#ef5350",
    },
    "Rechazado": {
        "background": "#e65100",
        "text": "#ffcc02",
        "border": "#ff9800",
    },
}

# Fallback for unknown statuses
DEFAULT_STATUS_COLORS: dict[str, str] = {
    "background": "#303358",
    "text": "#a0a0b8",
    "border": "#3a3c5e",
}


class StatusDelegate(QStyledItemDelegate):
    """
    Custom delegate that renders status cells as colored badge pills.

    Recognized statuses (Spanish):
    - 'Aprobado'  → Green badge
    - 'Pendiente' → Red badge
    - 'Rechazado' → Orange badge
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Paint the status cell as a colored badge."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Get cell value
        value = str(index.data(Qt.ItemDataRole.DisplayRole) or "")

        # Determine colors
        colors = STATUS_COLORS.get(value, DEFAULT_STATUS_COLORS)

        # Draw selection highlight if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(
                option.rect,
                QBrush(QColor(0, 191, 166, 40)),
            )

        # Calculate badge rectangle (centered, with padding)
        badge_width = min(option.rect.width() - 16, 120)
        badge_height = 26
        badge_x = option.rect.x() + (option.rect.width() - badge_width) // 2
        badge_y = option.rect.y() + (option.rect.height() - badge_height) // 2
        badge_rect = QRect(badge_x, badge_y, badge_width, badge_height)

        # Draw badge background
        bg_color = QColor(colors["background"])
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(colors["border"]), 1.5))
        painter.drawRoundedRect(badge_rect, 13, 13)

        # Draw text
        text_color = QColor(colors["text"])
        painter.setPen(QPen(text_color))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, value)

        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> "QRect":
        """Return the preferred size for the badge cell."""
        from PySide6.QtCore import QSize
        return QSize(130, 40)
