"""
Boss View (Jefe) — Management and financial dashboard for the logistics system.

Provides:
- Financial dashboard with QtCharts (auto-updating via QTimer)
- Driver/group status table with custom status delegates
- Liquidation approval controls with password protection

All visible UI text is in Spanish. All code identifiers are in English.
No inline styles — all styling handled via objectName references in styles.qss.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel

from controllers.delivery_controller import DeliveryController
from models.route_report_model import LiquidationStatus
from views.delegates.status_delegate import StatusDelegate


# Password for boss-level actions (in production, use proper auth)
BOSS_PASSWORD: str = "admin123"


class BossView(QWidget):
    """
    Boss management panel with financial dashboard and liquidation controls.

    Sections:
    1. Financial charts (bar + pie, auto-refreshing)
    2. Driver/delivery group status table
    3. Liquidation approval with password protection
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("bossView")

        # Controller
        self._controller = DeliveryController()

        # State
        self._is_authenticated: bool = False

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
            "Dashboard financiero, control de liquidaciones y estado de entregas"
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

        # Pending liquidations
        self._card_pending = self._create_stat_card(
            "PENDIENTE DE LIQUIDAR", "Q 0.00"
        )
        layout.addWidget(self._card_pending["frame"])

        # Approved
        self._card_approved = self._create_stat_card(
            "LIQUIDACIONES APROBADAS", "Q 0.00"
        )
        layout.addWidget(self._card_approved["frame"])

        # Broken bags
        self._card_broken = self._create_stat_card(
            "MERMA (BOLSAS ROTAS)", "0"
        )
        layout.addWidget(self._card_broken["frame"])

        # Active groups
        self._card_groups = self._create_stat_card(
            "GRUPOS ACTIVOS", "0"
        )
        layout.addWidget(self._card_groups["frame"])

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
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Left: Bar chart — Revenue by group
        bar_group = QGroupBox("Recaudación por Grupo de Entrega")
        bar_layout = QVBoxLayout(bar_group)
        self._bar_chart_view = self._create_bar_chart()
        bar_layout.addWidget(self._bar_chart_view)
        layout.addWidget(bar_group)

        # Right: Pie chart — Payment methods breakdown
        pie_group = QGroupBox("Distribución por Método de Pago")
        pie_layout = QVBoxLayout(pie_group)
        self._pie_chart_view = self._create_pie_chart()
        pie_layout.addWidget(self._pie_chart_view)
        layout.addWidget(pie_group)

    def _create_bar_chart(self) -> QChartView:
        """Create the revenue bar chart."""
        chart = QChart()
        chart.setTitle("Ingresos por Grupo (Q)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QBrush(QColor("#242640")))
        chart.setTitleBrush(QBrush(QColor("#e8e8f0")))
        chart.setTitleFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        # Get data grouped by delivery_group_id
        reports = self._controller.get_route_reports()
        group_totals: dict[int, float] = {}
        for r in reports:
            gid = r.delivery_group_id
            group_totals[gid] = group_totals.get(gid, 0) + r.payment_collected

        # Create bar set
        bar_set_collected = QBarSet("Recaudado")
        bar_set_collected.setColor(QColor("#00bfa6"))
        bar_set_collected.setBorderColor(QColor("#00a890"))

        categories: list[str] = []
        for gid in sorted(group_totals.keys()):
            bar_set_collected.append(group_totals[gid])
            categories.append(f"Grupo {gid}")

        series = QBarSeries()
        series.append(bar_set_collected)
        chart.addSeries(series)

        # Axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor("#a0a0b8"))
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("Q %.0f")
        axis_y.setLabelsColor(QColor("#a0a0b8"))
        axis_y.setGridLineColor(QColor("#3a3c5e"))
        if group_totals:
            axis_y.setRange(0, max(group_totals.values()) * 1.2)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # Legend
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(QColor("#a0a0b8"))

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return view

    def _create_pie_chart(self) -> QChartView:
        """Create the payment methods pie chart."""
        chart = QChart()
        chart.setTitle("Métodos de Pago")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QBrush(QColor("#242640")))
        chart.setTitleBrush(QBrush(QColor("#e8e8f0")))
        chart.setTitleFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        series = QPieSeries()

        # Aggregate by payment method
        reports = self._controller.get_route_reports()
        method_totals: dict[str, float] = {}
        for r in reports:
            label = r.payment_method_display
            method_totals[label] = (
                method_totals.get(label, 0) + r.payment_collected
            )

        # Color palette for pie slices
        pie_colors = [
            "#00bfa6", "#6c63ff", "#ff9800", "#ef5350",
            "#4caf50", "#2196f3",
        ]

        for idx, (method, total) in enumerate(method_totals.items()):
            pie_slice = series.append(
                f"{method}: Q{total:,.0f}", total
            )
            pie_slice.setColor(QColor(pie_colors[idx % len(pie_colors)]))
            pie_slice.setBorderColor(QColor("#242640"))
            pie_slice.setBorderWidth(2)
            pie_slice.setLabelVisible(True)
            pie_slice.setLabelColor(QColor("#e8e8f0"))

        chart.addSeries(series)

        # Legend
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.legend().setLabelColor(QColor("#a0a0b8"))

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        return view

    def _setup_liquidation_tab(self, container: QWidget) -> None:
        """Build the liquidation control tab."""
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(12)

        # Authentication section
        auth_group = QGroupBox("Acceso Seguro")
        auth_layout = QHBoxLayout(auth_group)

        auth_label = QLabel("Contraseña de autorización:")
        auth_layout.addWidget(auth_label)

        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setPlaceholderText("Ingrese contraseña...")
        self._password_input.setMaximumWidth(250)
        auth_layout.addWidget(self._password_input)

        self._btn_authenticate = QPushButton("🔓 Desbloquear")
        auth_layout.addWidget(self._btn_authenticate)

        self._auth_status = QLabel("🔒 Bloqueado")
        self._auth_status.setObjectName("subtitleLabel")
        auth_layout.addWidget(self._auth_status)

        auth_layout.addStretch()
        layout.addWidget(auth_group)

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
            "ID", "Grupo", "Cliente", "Bolsas",
            "Merma", "Pago (Q)", "Método", "Estado"
        ])
        self._liquidation_table.setModel(self._liquidation_model)

        # Apply status delegate to column 7 (Estado)
        self._status_delegate = StatusDelegate(self._liquidation_table)
        self._liquidation_table.setItemDelegateForColumn(
            7, self._status_delegate
        )

        # Column sizing
        lh = self._liquidation_table.horizontalHeader()
        lh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        lh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        lh.resizeSection(0, 40)
        lh.resizeSection(1, 60)
        for col in [3, 4, 5, 6, 7]:
            lh.setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
            )

        table_layout.addWidget(self._liquidation_table, 1)

        # Action buttons
        btn_layout = QHBoxLayout()

        self._btn_approve = QPushButton("✓ Aprobar Seleccionado")
        self._btn_approve.setEnabled(False)
        btn_layout.addWidget(self._btn_approve)

        self._btn_reject = QPushButton("✕ Rechazar Seleccionado")
        self._btn_reject.setObjectName("dangerButton")
        self._btn_reject.setEnabled(False)
        btn_layout.addWidget(self._btn_reject)

        self._btn_approve_all = QPushButton("✓✓ Aprobar Todos los Pendientes")
        self._btn_approve_all.setObjectName("accentButton")
        self._btn_approve_all.setEnabled(False)
        btn_layout.addWidget(self._btn_approve_all)

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

    def _update_stats_cards(self) -> None:
        """Refresh the stats cards with current financial data."""
        summary = self._controller.get_financial_summary()

        self._card_collected["value"].setText(
            f"Q {summary['total_collected']:,.2f}"
        )
        self._card_pending["value"].setText(
            f"Q {summary['total_pending']:,.2f}"
        )
        self._card_approved["value"].setText(
            f"Q {summary['total_approved']:,.2f}"
        )
        self._card_broken["value"].setText(
            str(int(summary["total_broken_bags"]))
        )
        self._card_groups["value"].setText(
            str(int(summary["total_groups"]))
        )

    def _load_liquidation_table(self) -> None:
        """Load route reports into the liquidation table."""
        self._liquidation_model.removeRows(
            0, self._liquidation_model.rowCount()
        )

        reports = self._controller.get_route_reports()
        for report in reports:
            row = [
                QStandardItem(str(report.id)),
                QStandardItem(str(report.delivery_group_id)),
                QStandardItem(report.client_name),
                QStandardItem(str(report.bags_delivered)),
                QStandardItem(str(report.broken_bags)),
                QStandardItem(f"Q {report.payment_collected:,.2f}"),
                QStandardItem(report.payment_method_display),
                QStandardItem(report.liquidation_status_display),
            ]

            for item in row:
                item.setEditable(False)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Left-align client name
            row[2].setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            self._liquidation_model.appendRow(row)

    # ──────────────────────────────────────────────────────────────
    #  Signal Connections
    # ──────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect UI signals to handler slots."""
        self._btn_authenticate.clicked.connect(self._on_authenticate)
        self._password_input.returnPressed.connect(self._on_authenticate)
        self._btn_approve.clicked.connect(self._on_approve_selected)
        self._btn_reject.clicked.connect(self._on_reject_selected)
        self._btn_approve_all.clicked.connect(self._on_approve_all)
        self._btn_refresh.clicked.connect(self._on_refresh)

        self._liquidation_table.selectionModel().selectionChanged.connect(
            self._on_liquidation_selection_changed
        )

    # ──────────────────────────────────────────────────────────────
    #  Event Handlers
    # ──────────────────────────────────────────────────────────────

    def _on_authenticate(self) -> None:
        """Handle password authentication for boss actions."""
        entered = self._password_input.text()

        if entered == BOSS_PASSWORD:
            self._is_authenticated = True
            self._auth_status.setText("🔓 Desbloqueado — Acceso concedido")
            self._btn_approve_all.setEnabled(True)
            self._password_input.setEnabled(False)
            self._btn_authenticate.setEnabled(False)
            self._password_input.clear()

            QMessageBox.information(
                self,
                "Acceso Concedido",
                "Ha iniciado sesión como Jefe.\n"
                "Ahora puede aprobar o rechazar liquidaciones.",
            )
        else:
            self._is_authenticated = False
            self._auth_status.setText("🔒 Bloqueado — Contraseña incorrecta")
            self._password_input.clear()
            self._password_input.setFocus()

            QMessageBox.warning(
                self,
                "Acceso Denegado",
                "La contraseña ingresada es incorrecta.\n"
                "Intente nuevamente.",
            )

    def _on_approve_selected(self) -> None:
        """Approve the selected liquidation report."""
        if not self._is_authenticated:
            QMessageBox.warning(
                self,
                "No Autorizado",
                "Debe ingresar la contraseña de autorización primero.",
            )
            return

        report_id = self._get_selected_report_id()
        if report_id is None:
            return

        success = self._controller.update_liquidation_status(
            report_id, LiquidationStatus.APPROVED
        )
        if success:
            self._load_liquidation_table()
            self._update_stats_cards()
            QMessageBox.information(
                self,
                "Liquidación Aprobada",
                f"La liquidación #{report_id} ha sido aprobada.",
            )

    def _on_reject_selected(self) -> None:
        """Reject the selected liquidation report."""
        if not self._is_authenticated:
            QMessageBox.warning(
                self,
                "No Autorizado",
                "Debe ingresar la contraseña de autorización primero.",
            )
            return

        report_id = self._get_selected_report_id()
        if report_id is None:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Rechazo",
            f"¿Está seguro de rechazar la liquidación #{report_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        success = self._controller.update_liquidation_status(
            report_id, LiquidationStatus.REJECTED
        )
        if success:
            self._load_liquidation_table()
            self._update_stats_cards()
            QMessageBox.information(
                self,
                "Liquidación Rechazada",
                f"La liquidación #{report_id} ha sido rechazada.",
            )

    def _on_approve_all(self) -> None:
        """Approve all pending liquidation reports."""
        if not self._is_authenticated:
            QMessageBox.warning(
                self,
                "No Autorizado",
                "Debe ingresar la contraseña de autorización primero.",
            )
            return

        pending_reports = [
            r
            for r in self._controller.get_route_reports()
            if r.liquidation_status == LiquidationStatus.PENDING
        ]

        if not pending_reports:
            QMessageBox.information(
                self,
                "Sin Pendientes",
                "No hay liquidaciones pendientes para aprobar.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "Aprobar Todas",
            f"¿Está seguro de aprobar {len(pending_reports)} "
            f"liquidaciones pendientes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        approved_count = 0
        for report in pending_reports:
            if report.id is not None:
                success = self._controller.update_liquidation_status(
                    report.id, LiquidationStatus.APPROVED
                )
                if success:
                    approved_count += 1

        self._load_liquidation_table()
        self._update_stats_cards()

        QMessageBox.information(
            self,
            "Liquidaciones Aprobadas",
            f"Se aprobaron {approved_count} liquidaciones exitosamente.",
        )

    def _on_refresh(self) -> None:
        """Refresh all data displays."""
        self._load_data()

    def _on_liquidation_selection_changed(self) -> None:
        """Enable/disable action buttons based on table selection."""
        has_selection = bool(
            self._liquidation_table.selectionModel().selectedRows()
        )
        self._btn_approve.setEnabled(has_selection and self._is_authenticated)
        self._btn_reject.setEnabled(has_selection and self._is_authenticated)

    # ──────────────────────────────────────────────────────────────
    #  Auto-Refresh
    # ──────────────────────────────────────────────────────────────

    def _start_auto_refresh(self) -> None:
        """Start a QTimer for periodic dashboard refresh (every 30s)."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_timer_refresh)
        self._refresh_timer.start(30000)  # 30 seconds

    def _on_timer_refresh(self) -> None:
        """Handle timer-triggered data refresh."""
        self._update_stats_cards()

    # ──────────────────────────────────────────────────────────────
    #  Utilities
    # ──────────────────────────────────────────────────────────────

    def _get_selected_report_id(self) -> Optional[int]:
        """Get the report ID from the currently selected row."""
        selection = self._liquidation_table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Seleccione una liquidación de la tabla.",
            )
            return None

        row_idx = selection[0].row()
        id_item = self._liquidation_model.item(row_idx, 0)
        if id_item is None:
            return None

        try:
            return int(id_item.text())
        except ValueError:
            return None
