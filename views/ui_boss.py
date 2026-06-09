from __future__ import annotations

from typing import Optional

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QDateTimeAxis,
    QValueAxis,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel

from controllers.delivery_controller import DeliveryController
from models.route_report_model import LiquidationStatus
from views.delegates.status_delegate import StatusDelegate


class BossView(QWidget):
    """
    Boss management panel with financial dashboard and liquidation controls.

    Sections:
    1. Financial charts (line + bar, auto-refreshing)
    2. Driver/delivery group status table
    3. Liquidation approval
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("bossView")

        # Controller
        self._controller = DeliveryController()

        self._setup_ui()
        self._connect_signals()
        self._load_data()
        self._start_auto_refresh()

    # ──────────────────────────────────────────────────────────────
    #  UI Setup
    # ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Build the complete boss view layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("Panel del Jefe")
        header.setObjectName("headerLabel")
        main_layout.addWidget(header)

        subtitle = QLabel(
            "Dashboard financiero y control de liquidaciones"
        )
        subtitle.setObjectName("subtitleLabel")
        main_layout.addWidget(subtitle)

        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(separator)

        # Stats cards row
        stats_row = self._create_stats_row()
        main_layout.addLayout(stats_row)

        # Tab widget
        self._tab_widget = QTabWidget()
        main_layout.addWidget(self._tab_widget, 1)

        # Tab 1: Financial Dashboard
        charts_tab = QWidget()
        self._tab_widget.addTab(charts_tab, "📊 Dashboard Financiero")
        self._setup_charts_tab(charts_tab)

        # Tab 2: Liquidation Control
        liquidation_tab = QWidget()
        self._tab_widget.addTab(liquidation_tab, "💰 Control de Liquidaciones")
        self._setup_liquidation_tab(liquidation_tab)

    def _create_stats_row(self) -> QHBoxLayout:
        """Create the top-level stats summary cards."""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Total collected
        self._card_collected = self._create_stat_card(
            "TOTAL RECAUDADO", "Q 0.00"
        )
        layout.addWidget(self._card_collected["frame"])
        layout.addStretch()

        return layout

    def _create_stat_card(
        self, title: str, initial_value: str
    ) -> dict[str, QFrame | QLabel]:
        """Create a single stats card with title and value."""
        frame = QFrame()
        frame.setObjectName("statsCard")
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(12, 12, 12, 12)

        value_label = QLabel(initial_value)
        value_label.setObjectName("statsValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setObjectName("statsTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)

        return {"frame": frame, "value": value_label, "title": title_label}

    def _setup_charts_tab(self, container: QWidget) -> None:
        """Build the financial charts dashboard."""
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Top: Line chart - Bags sold over time
        line_group = QGroupBox("Bolsas Vendidas en el Tiempo")
        line_layout = QVBoxLayout(line_group)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtro:"))
        self._time_filter = QComboBox()
        self._time_filter.addItems(["Día", "Semana", "Mes"])
        self._time_filter.currentIndexChanged.connect(self._refresh_line_chart)
        filter_layout.addWidget(self._time_filter)
        filter_layout.addStretch()
        line_layout.addLayout(filter_layout)

        self._line_chart_view = QChartView()
        line_layout.addWidget(self._line_chart_view)
        layout.addWidget(line_group, 1)

        # Bottom: Bar chart - Top clients
        bar_group = QGroupBox("Ranking de Clientes (Bolsas Pedidas)")
        bar_layout = QVBoxLayout(bar_group)
        self._bar_chart_view = QChartView()
        bar_layout.addWidget(self._bar_chart_view)
        layout.addWidget(bar_group, 1)

    def _refresh_line_chart(self) -> None:
        chart = QChart()
        chart.setTitle("Bolsas Vendidas")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QBrush(QColor("#242640")))
        chart.setTitleBrush(QBrush(QColor("#e8e8f0")))
        chart.setTitleFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        series = QLineSeries()
        pen = QPen(QColor("#00bfa6"))
        pen.setWidth(3)
        series.setPen(pen)

        reports = self._controller.get_route_reports()
        
        # Filter reports that have a valid delivery_timestamp
        valid_reports = [r for r in reports if r.delivery_timestamp is not None]
        data_points = sorted(valid_reports, key=lambda r: r.delivery_timestamp)
        
        use_datetime_axis = len(data_points) > 0
        cumulative_bags = 0
        for r in data_points:
            cumulative_bags += r.bags_delivered
            # delivery_timestamp is a Python datetime object, convert to QDateTime
            py_dt = r.delivery_timestamp
            q_dt = QDateTime(py_dt.year, py_dt.month, py_dt.day,
                             py_dt.hour, py_dt.minute, py_dt.second)
            series.append(q_dt.toMSecsSinceEpoch(), cumulative_bags)

        chart.addSeries(series)

        if use_datetime_axis and series.count() > 0:
            axis_x = QDateTimeAxis()
            axis_x.setFormat("dd/MM hh:mm")
            axis_x.setLabelsColor(QColor("#a0a0b8"))
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)
        else:
            axis_x = QValueAxis()
            axis_x.setLabelsColor(QColor("#a0a0b8"))
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelsColor(QColor("#a0a0b8"))
        axis_y.setGridLineColor(QColor("#3a3c5e"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().hide()
        self._line_chart_view.setChart(chart)
        self._line_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    def _refresh_bar_chart(self) -> None:
        chart = QChart()
        chart.setTitle("Top Clientes")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QBrush(QColor("#242640")))
        chart.setTitleBrush(QBrush(QColor("#e8e8f0")))
        chart.setTitleFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        reports = self._controller.get_route_reports()
        client_totals: dict[str, int] = {}
        for r in reports:
            client_totals[r.client_name] = client_totals.get(r.client_name, 0) + r.bags_delivered

        sorted_clients = sorted(client_totals.items(), key=lambda x: x[1], reverse=True)[:10]

        bar_set = QBarSet("Bolsas")
        bar_set.setColor(QColor("#6c63ff"))
        
        categories = []
        for name, total in sorted_clients:
            bar_set.append(total)
            categories.append(name)

        series = QBarSeries()
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor("#a0a0b8"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelsColor(QColor("#a0a0b8"))
        axis_y.setGridLineColor(QColor("#3a3c5e"))
        if sorted_clients:
            axis_y.setRange(0, sorted_clients[0][1] * 1.2)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().hide()
        self._bar_chart_view.setChart(chart)
        self._bar_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    def _setup_liquidation_tab(self, container: QWidget) -> None:
        """Build the liquidation control tab."""
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Reports table with status delegate
        table_group = QGroupBox("Estado de Liquidaciones por Entrega")
        table_layout = QVBoxLayout(table_group)

        self._liquidation_table = QTableView()
        self._liquidation_table.setAlternatingRowColors(True)
        self._liquidation_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self._liquidation_table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )
        self._liquidation_table.verticalHeader().setVisible(False)

        self._liquidation_model = QStandardItemModel()
        self._liquidation_model.setHorizontalHeaderLabels([
            "ID", "F. Creación", "F. Entrega", "Promotor",
            "Cliente", "Bolsas", "Pago (Bs)", "Método", "Estado"
        ])
        self._liquidation_table.setModel(self._liquidation_model)

        self._status_delegate = StatusDelegate(self._liquidation_table)
        self._liquidation_table.setItemDelegateForColumn(
            8, self._status_delegate
        )

        lh = self._liquidation_table.horizontalHeader()
        lh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        lh.resizeSection(0, 40)
        lh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3, 5, 6, 7, 8]:
            lh.setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
            )

        table_layout.addWidget(self._liquidation_table, 1)

        btn_layout = QHBoxLayout()

        self._btn_save = QPushButton("💾 Guardar Aprobados")
        self._btn_save.setObjectName("accentButton")
        self._btn_save.setEnabled(False)
        self._btn_save.hide()
        btn_layout.addWidget(self._btn_save)

        btn_layout.addStretch()

        self._btn_refresh = QPushButton("🔄 Actualizar")
        self._btn_refresh.setObjectName("secondaryButton")
        btn_layout.addWidget(self._btn_refresh)

        table_layout.addLayout(btn_layout)
        layout.addWidget(table_group, 1)

    # ──────────────────────────────────────────────────────────────
    #  Data Loading
    # ──────────────────────────────────────────────────────────────

    def _load_data(self) -> None:
        """Load all data into UI elements."""
        self._update_stats_cards()
        self._load_liquidation_table()
        self._refresh_line_chart()
        self._refresh_bar_chart()

    def _update_stats_cards(self) -> None:
        """Refresh the stats cards with current financial data."""
        summary = self._controller.get_financial_summary()
        self._card_collected["value"].setText(
            f"Bs {summary['total_collected']:,.2f}"
        )

    def _load_liquidation_table(self) -> None:
        """Load route reports into the liquidation table."""
        self._liquidation_model.removeRows(
            0, self._liquidation_model.rowCount()
        )

        reports = self._controller.get_route_reports()
        
        all_approved = True
        has_reports = False

        for report in reports:
            has_reports = True
            if report.liquidation_status != LiquidationStatus.APPROVED:
                all_approved = False

            created_str = report.created_at.strftime("%d/%m %H:%M") if report.created_at else ""
            delivery_str = report.delivery_timestamp.strftime("%d/%m %H:%M") if report.delivery_timestamp else ""

            row = [
                QStandardItem(str(report.id)),
                QStandardItem(created_str),
                QStandardItem(delivery_str),
                QStandardItem(report.promoter_name),
                QStandardItem(report.client_name),
                QStandardItem(str(report.bags_delivered)),
                QStandardItem(f"Bs {report.payment_collected:,.2f}"),
                QStandardItem(report.payment_method_display),
                QStandardItem(report.liquidation_status_display),
            ]

            for item in row:
                item.setEditable(False)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            row[4].setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            self._liquidation_model.appendRow(row)
            
        if has_reports and all_approved:
            self._btn_save.show()
            self._btn_save.setEnabled(True)
        else:
            self._btn_save.hide()
            self._btn_save.setEnabled(False)

    # ──────────────────────────────────────────────────────────────
    #  Signal Connections
    # ──────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect UI signals to handler slots."""
        self._btn_save.clicked.connect(self._on_save_liquidations)
        self._btn_refresh.clicked.connect(self._on_refresh)
        self._liquidation_table.clicked.connect(self._on_table_clicked)

    # ──────────────────────────────────────────────────────────────
    #  Event Handlers
    # ──────────────────────────────────────────────────────────────

    def _on_table_clicked(self, index) -> None:
        """Handle click on table cells (specifically status column)."""
        if index.column() == 8: # Status column
            row_idx = index.row()
            id_item = self._liquidation_model.item(row_idx, 0)
            if not id_item:
                return
            report_id = int(id_item.text())
            
            # Find the report to toggle status
            reports = self._controller.get_route_reports()
            for r in reports:
                if r.id == report_id:
                    # Toggle status
                    new_status = LiquidationStatus.APPROVED if r.liquidation_status == LiquidationStatus.PENDING else LiquidationStatus.PENDING
                    self._controller.update_liquidation_status(report_id, new_status)
                    self._load_data()
                    break

    def _on_save_liquidations(self) -> None:
        """Save approved liquidations to DB (simulated)."""
        count = self._controller.save_approved_liquidations()
        self._load_data()
        QMessageBox.information(
            self,
            "Guardado Exitoso",
            f"Se guardaron {count} liquidaciones aprobadas en las carpetas de clientes."
        )

    def _on_refresh(self) -> None:
        """Refresh all data displays."""
        self._load_data()

    # ──────────────────────────────────────────────────────────────
    #  Auto-Refresh
    # ──────────────────────────────────────────────────────────────

    def _start_auto_refresh(self) -> None:
        """Start a QTimer for periodic dashboard refresh (every 30s)."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_timer_refresh)
        self._refresh_timer.start(30000)

    def _on_timer_refresh(self) -> None:
        """Handle timer-triggered data refresh."""
        self._load_data()

    # ──────────────────────────────────────────────────────────────
    #  Utilities
    # ──────────────────────────────────────────────────────────────

    # Methods _get_selected_report_id removed
