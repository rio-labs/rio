import rio
from datetime import datetime

# <additional-imports>
from .. import components as comps
from .. import constants
from ..services import faker, settings, transactions

# </additional-imports>


# <component>
@rio.page(
    name="Transactions",
    url_segment="transactions",
)
class TransactionPage(rio.Component):
    """
    Enhanced Transactions page with comprehensive transaction management.
    
    Features:
    - Transaction history table with sorting and filtering
    - Add new transactions with validation
    - Import/export functionality
    - Transaction analytics
    - Search and filter capabilities
    """

    show_add_dialog: bool = False
    add_type: transactions.TransactionType = transactions.TransactionType.TRADE_BUY
    add_asset: str = ""
    add_quantity: float = 0.0
    add_unit_price: float = 0.0
    add_counterparty: str = ""
    add_notes: str = ""
    add_fee: float = 0.0
    
    # Filter and search states
    filter_type: str = "All"
    filter_asset: str = "All"
    search_query: str = ""
    sort_by: str = "Date"
    sort_descending: bool = True

    def build(self) -> rio.Component:
        # Access settings
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        
        # Apply filters and sorting
        filtered_txs = self._filter_and_sort_transactions(user_settings.transactions)
        
        # Create transaction summary
        summary_cards = self._create_summary_cards(user_settings.transactions)
        
        # Create filters section
        filters_section = self._create_filters_section(user_settings.transactions)
        
        # Table data
        table_data = [
            {
                "Date": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Type": tx.type.value,
                "Asset": tx.asset,
                "Quantity": f"{tx.quantity:.6f}",
                "Unit Price": f"${tx.unit_price:.2f}",
                "Total": f"${tx.total_value():.2f}",
                "Fee": f"${tx.fee_quantity:.2f}",
                "Counterparty": tx.counterparty or "N/A",
                "Notes": tx.notes[:50] + "..." if len(tx.notes) > 50 else tx.notes,
            }
            for tx in filtered_txs
        ]
        
        main_content = rio.Column(
            rio.Text("Transaction Management", style="heading1"),
            summary_cards,
            filters_section,
            rio.Row(
                rio.Button(
                    "Add Transaction", 
                    on_press=self._open_add_dialog,
                    style="major"
                ),
                rio.Button("Generate Sample Data", on_press=self._generate_fake),
                rio.Button("Export CSV", on_press=self._export_transactions),
                spacing=1,
            ),
            rio.Table(
                data=table_data,
                grow_y=True,
            ),
            spacing=2,
            grow_y=True,
            margin=2,
        )
        
        if self.show_add_dialog:
            dialog = self._create_add_dialog()
            return rio.Overlay(main_content, dialog)
        else:
            return main_content
    
    def _create_summary_cards(self, transactions_list: list) -> rio.Component:
        """Create summary statistics cards."""
        
        if not transactions_list:
            return rio.Text("No transactions yet. Add some to see analytics!", style="dim")
        
        # Calculate statistics
        total_transactions = len(transactions_list)
        buy_transactions = sum(1 for tx in transactions_list if tx.type == transactions.TransactionType.TRADE_BUY)
        sell_transactions = sum(1 for tx in transactions_list if tx.type == transactions.TransactionType.TRADE_SELL)
        total_fees = sum(float(tx.fee_quantity) for tx in transactions_list)
        
        # Unique assets
        unique_assets = len(set(tx.asset for tx in transactions_list))
        
        return rio.Row(
            rio.Card(
                rio.Column(
                    rio.Text("Total Transactions", style="heading4"),
                    rio.Text(str(total_transactions), style="heading2"),
                    spacing=0.5,
                ),
                margin=0.5,
            ),
            rio.Card(
                rio.Column(
                    rio.Text("Buy/Sell Ratio", style="heading4"),
                    rio.Text(f"{buy_transactions}/{sell_transactions}", style="heading2"),
                    spacing=0.5,
                ),
                margin=0.5,
            ),
            rio.Card(
                rio.Column(
                    rio.Text("Total Fees", style="heading4"),
                    rio.Text(f"${total_fees:.2f}", style="heading2"),
                    spacing=0.5,
                ),
                margin=0.5,
            ),
            rio.Card(
                rio.Column(
                    rio.Text("Assets Traded", style="heading4"),
                    rio.Text(str(unique_assets), style="heading2"),
                    spacing=0.5,
                ),
                margin=0.5,
            ),
            spacing=1,
        )
    
    def _create_filters_section(self, transactions_list: list) -> rio.Component:
        """Create filters and search section."""
        
        # Get unique values for filters
        transaction_types = ["All"] + [t.value for t in transactions.TransactionType]
        assets = ["All"] + sorted(list(set(tx.asset for tx in transactions_list)))
        sort_options = ["Date", "Asset", "Type", "Amount"]
        
        return rio.Card(
            rio.Column(
                rio.Text("Filters & Search", style="heading3"),
                rio.Row(
                    rio.Column(
                        rio.Text("Search:", style="dim"),
                        rio.TextInput(
                            text=self.search_query,
                            placeholder="Search transactions...",
                            on_change=self._update_search,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Type:", style="dim"),
                        rio.Dropdown(
                            options=transaction_types,
                            selected=self.filter_type,
                            on_change=self._update_type_filter,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Asset:", style="dim"),
                        rio.Dropdown(
                            options=assets,
                            selected=self.filter_asset,
                            on_change=self._update_asset_filter,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Sort by:", style="dim"),
                        rio.Dropdown(
                            options=sort_options,
                            selected=self.sort_by,
                            on_change=self._update_sort,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Order:", style="dim"),
                        rio.Switch(
                            text="Descending",
                            is_on=self.sort_descending,
                            on_change=self._toggle_sort_order,
                        ),
                        spacing=0.5,
                    ),
                    spacing=2,
                ),
                spacing=1,
            ),
            margin=1,
        )
    
    def _create_add_dialog(self) -> rio.Component:
        """Create the add transaction dialog."""
        
        # Available assets from portfolio
        available_assets = [coin.ticker for coin in constants.MY_PORTFOLIO]
        
        return rio.Dialog(
            title="Add New Transaction",
            content=rio.Column(
                rio.Row(
                    rio.Column(
                        rio.Text("Transaction Type:", style="dim"),
                        rio.Dropdown(
                            options=[t.value for t in transactions.TransactionType],
                            selected=self.add_type.value,
                            on_change=self._update_add_type,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Asset:", style="dim"),
                        rio.Dropdown(
                            options=available_assets,
                            selected=self.add_asset,
                            on_change=self._update_add_asset_dropdown,
                        ),
                        spacing=0.5,
                    ),
                    spacing=2,
                ),
                rio.Row(
                    rio.Column(
                        rio.Text("Quantity:", style="dim"),
                        rio.NumberInput(
                            value=self.add_quantity,
                            on_change=self._update_add_quantity,
                            min_value=0.000001,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Unit Price ($):", style="dim"),
                        rio.NumberInput(
                            value=self.add_unit_price,
                            on_change=self._update_add_unit_price,
                            min_value=0,
                        ),
                        spacing=0.5,
                    ),
                    rio.Column(
                        rio.Text("Fee ($):", style="dim"),
                        rio.NumberInput(
                            value=self.add_fee,
                            on_change=self._update_add_fee,
                            min_value=0,
                        ),
                        spacing=0.5,
                    ),
                    spacing=2,
                ),
                rio.TextInput(
                    label="Counterparty (Exchange/Wallet)",
                    text=self.add_counterparty,
                    on_change=self._update_add_counterparty,
                ),
                rio.TextInput(
                    label="Notes",
                    text=self.add_notes,
                    on_change=self._update_add_notes,
                    multiline=True,
                ),
                # Show calculated total
                rio.Text(
                    f"Total Value: ${self.add_quantity * self.add_unit_price:.2f}",
                    style="heading4"
                ) if self.add_quantity and self.add_unit_price else rio.Spacer(),
                rio.Row(
                    rio.Button("Cancel", on_press=self._close_add_dialog),
                    rio.Button(
                        "Add Transaction", 
                        on_press=self._add_transaction,
                        style="major"
                    ),
                    spacing=1,
                    justify="end",
                ),
                spacing=1.5,
            ),
            on_close=self._close_add_dialog,
        )
    
    def _filter_and_sort_transactions(self, transactions_list: list) -> list:
        """Apply filters and sorting to transactions."""
        
        filtered = transactions_list.copy()
        
        # Apply type filter
        if self.filter_type != "All":
            filtered = [tx for tx in filtered if tx.type.value == self.filter_type]
        
        # Apply asset filter
        if self.filter_asset != "All":
            filtered = [tx for tx in filtered if tx.asset == self.filter_asset]
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                tx for tx in filtered
                if (query in tx.asset.lower() or 
                    query in tx.counterparty.lower() or 
                    query in tx.notes.lower() or
                    query in tx.type.value.lower())
            ]
        
        # Apply sorting
        if self.sort_by == "Date":
            filtered.sort(key=lambda tx: tx.timestamp, reverse=self.sort_descending)
        elif self.sort_by == "Asset":
            filtered.sort(key=lambda tx: tx.asset, reverse=self.sort_descending)
        elif self.sort_by == "Type":
            filtered.sort(key=lambda tx: tx.type.value, reverse=self.sort_descending)
        elif self.sort_by == "Amount":
            filtered.sort(key=lambda tx: tx.total_value(), reverse=self.sort_descending)
        
        return filtered
    
    # Event handlers
    def _open_add_dialog(self, event: rio.ButtonPressEvent) -> None:
        self.show_add_dialog = True
        self.force_refresh()
    
    def _close_add_dialog(self, event=None) -> None:
        self.show_add_dialog = False
        # Reset form
        self.add_type = transactions.TransactionType.TRADE_BUY
        self.add_asset = ""
        self.add_quantity = 0.0
        self.add_unit_price = 0.0
        self.add_counterparty = ""
        self.add_notes = ""
        self.add_fee = 0.0
        self.force_refresh()
    
    def _update_add_type(self, event: rio.DropdownChangeEvent) -> None:
        self.add_type = transactions.TransactionType(event.new_value)
    
    def _update_add_asset_dropdown(self, event: rio.DropdownChangeEvent) -> None:
        self.add_asset = event.new_value
    
    def _update_add_quantity(self, event: rio.NumberInputChangeEvent) -> None:
        self.add_quantity = event.new_value
        self.force_refresh()  # Refresh to update total
    
    def _update_add_unit_price(self, event: rio.NumberInputChangeEvent) -> None:
        self.add_unit_price = event.new_value
        self.force_refresh()  # Refresh to update total
    
    def _update_add_fee(self, event: rio.NumberInputChangeEvent) -> None:
        self.add_fee = event.new_value
    
    def _update_add_counterparty(self, event: rio.TextInputChangeEvent) -> None:
        self.add_counterparty = event.new_text
    
    def _update_add_notes(self, event: rio.TextInputChangeEvent) -> None:
        self.add_notes = event.new_text
    
    def _update_search(self, event: rio.TextInputChangeEvent) -> None:
        self.search_query = event.new_text
        self.force_refresh()
    
    def _update_type_filter(self, event: rio.DropdownChangeEvent) -> None:
        self.filter_type = event.new_value
        self.force_refresh()
    
    def _update_asset_filter(self, event: rio.DropdownChangeEvent) -> None:
        self.filter_asset = event.new_value
        self.force_refresh()
    
    def _update_sort(self, event: rio.DropdownChangeEvent) -> None:
        self.sort_by = event.new_value
        self.force_refresh()
    
    def _toggle_sort_order(self, event) -> None:
        self.sort_descending = event.is_on
        self.force_refresh()
    
    def _add_transaction(self, event: rio.ButtonPressEvent) -> None:
        # Validation
        if not self.add_asset or self.add_quantity <= 0 or self.add_unit_price < 0:
            return
        
        tx = transactions.TransactionRecord(
            type=self.add_type,
            asset=self.add_asset,
            quantity=transactions.decimal.Decimal(str(self.add_quantity)),
            unit_price=transactions.decimal.Decimal(str(self.add_unit_price)),
            fee_quantity=transactions.decimal.Decimal(str(self.add_fee)),
            counterparty=self.add_counterparty,
            notes=self.add_notes,
        )
        
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        user_settings.transactions.append(tx)
        self._close_add_dialog()
    
    def _generate_fake(self, event: rio.ButtonPressEvent) -> None:
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        fake_txs = faker.generate_fake_transactions(seed=42, count=10)
        user_settings.transactions.extend(fake_txs)
        self.force_refresh()
    
    def _export_transactions(self, event: rio.ButtonPressEvent) -> None:
        # Placeholder for CSV export functionality
        # In a real implementation, this would generate and download a CSV file
        pass


# </component>
