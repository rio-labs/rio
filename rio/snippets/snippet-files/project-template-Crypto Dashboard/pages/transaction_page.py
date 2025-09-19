import rio

# <additional-imports>
from .. import components as comps
from ..services import faker, settings, transactions

# </additional-imports>


# <component>
import rio

# <additional-imports>
from .. import components as comps
from ..services import faker, settings, transactions

# </additional-imports>


# <component>
@rio.page(
    name="Transactions",
    url_segment="transactions",
)
class TransactionPage(rio.Component):
    """
    Transactions page with table, add, and generate fake.
    """

    show_add_dialog: bool = False
    add_type: transactions.TransactionType = transactions.TransactionType.TRADE_BUY
    add_asset: str = ""
    add_quantity: float = 0.0
    add_unit_price: float = 0.0
    add_counterparty: str = ""
    add_notes: str = ""

    def build(self) -> rio.Component:
        # Access settings
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        
        # Sort transactions by timestamp
        sorted_txs = sorted(user_settings.transactions, key=lambda tx: tx.timestamp, reverse=True)
        
        # Table data
        table_data = [
            {
                "Date": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Type": tx.type.value,
                "Asset": tx.asset,
                "Quantity": f"{tx.quantity}",
                "Unit Price": f"{tx.unit_price}",
                "Total": f"{tx.total_value()}",
                "Fee": f"{tx.fee_quantity}",
                "Counterparty": tx.counterparty,
                "TxID": tx.txid,
                "Notes": tx.notes,
            }
            for tx in sorted_txs
        ]
        
        main_content = rio.Column(
            rio.Row(
                rio.Button("Add Transaction", on_press=self._open_add_dialog),
                rio.Button("Generate Fake (10)", on_press=self._generate_fake),
                spacing=1,
            ),
            rio.Table(
                data=table_data,
                grow_y=True,
            ),
            spacing=1,
            grow_y=True,
        )
        
        if self.show_add_dialog:
            dialog = rio.Dialog(
                title="Add Transaction",
                content=rio.Column(
                    rio.Dropdown(
                        label="Type",
                        options=[t.value for t in transactions.TransactionType],
                        selected=self.add_type.value,
                        on_change=self._update_add_type,
                    ),
                    rio.TextInput(
                        label="Asset",
                        text=self.add_asset,
                        on_change=self._update_add_asset,
                    ),
                    rio.NumberInput(
                        label="Quantity",
                        value=self.add_quantity,
                        on_change=self._update_add_quantity,
                    ),
                    rio.NumberInput(
                        label="Unit Price",
                        value=self.add_unit_price,
                        on_change=self._update_add_unit_price,
                    ),
                    rio.TextInput(
                        label="Counterparty",
                        text=self.add_counterparty,
                        on_change=self._update_add_counterparty,
                    ),
                    rio.TextInput(
                        label="Notes",
                        text=self.add_notes,
                        on_change=self._update_add_notes,
                    ),
                    rio.Row(
                        rio.Button("Cancel", on_press=self._close_add_dialog),
                        rio.Button("Add", on_press=self._add_transaction),
                        spacing=1,
                    ),
                    spacing=1,
                ),
                on_close=self._close_add_dialog,
            )
            return rio.Overlay(main_content, dialog)
        else:
            return main_content
    
    def _open_add_dialog(self, event: rio.ButtonPressEvent) -> None:
        self.show_add_dialog = True
        self.force_refresh()
    
    def _close_add_dialog(self, event: rio.DialogCloseEvent = None) -> None:
        self.show_add_dialog = False
        # Reset form
        self.add_type = transactions.TransactionType.TRADE_BUY
        self.add_asset = ""
        self.add_quantity = 0.0
        self.add_unit_price = 0.0
        self.add_counterparty = ""
        self.add_notes = ""
        self.force_refresh()
    
    def _update_add_type(self, event: rio.DropdownChangeEvent) -> None:
        self.add_type = transactions.TransactionType(event.new_value)
    
    def _update_add_asset(self, event: rio.TextInputChangeEvent) -> None:
        self.add_asset = event.new_text
    
    def _update_add_quantity(self, event: rio.NumberInputChangeEvent) -> None:
        self.add_quantity = event.new_value
    
    def _update_add_unit_price(self, event: rio.NumberInputChangeEvent) -> None:
        self.add_unit_price = event.new_value
    
    def _update_add_counterparty(self, event: rio.TextInputChangeEvent) -> None:
        self.add_counterparty = event.new_text
    
    def _update_add_notes(self, event: rio.TextInputChangeEvent) -> None:
        self.add_notes = event.new_text
    
    def _add_transaction(self, event: rio.ButtonPressEvent) -> None:
        if not self.add_asset or self.add_quantity <= 0 or self.add_unit_price < 0:
            # Basic validation
            return
        tx = transactions.TransactionRecord(
            type=self.add_type,
            asset=self.add_asset,
            quantity=transactions.decimal.Decimal(str(self.add_quantity)),
            unit_price=transactions.decimal.Decimal(str(self.add_unit_price)),
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


# </component>
class TransactionPage(rio.Component):
    """
    Transactions page with table, add, and generate fake.
    """

    def build(self) -> rio.Component:
        # Access settings
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        
        # Sort transactions by timestamp
        sorted_txs = sorted(user_settings.transactions, key=lambda tx: tx.timestamp, reverse=True)
        
        # Table data
        table_data = [
            {
                "Date": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Type": tx.type.value,
                "Asset": tx.asset,
                "Quantity": f"{tx.quantity}",
                "Unit Price": f"{tx.unit_price}",
                "Total": f"{tx.total_value()}",
                "Fee": f"{tx.fee_quantity}",
                "Counterparty": tx.counterparty,
                "TxID": tx.txid,
                "Notes": tx.notes,
            }
            for tx in sorted_txs
        ]
        
        return rio.Column(
            rio.Row(
                rio.Button("Add Transaction", on_press=self._add_transaction),
                rio.Button("Generate Fake (10)", on_press=self._generate_fake),
                spacing=1,
            ),
            rio.Table(
                data=table_data,
                grow_y=True,
            ),
            spacing=1,
            grow_y=True,
        )
    
    def _add_transaction(self, event: rio.ButtonPressEvent) -> None:
        # Placeholder: open dialog to add
        pass
    
    def _generate_fake(self, event: rio.ButtonPressEvent) -> None:
        user_settings = rio.UserSettings.get(settings.DashboardSettings)
        fake_txs = faker.generate_fake_transactions(seed=42, count=10)
        user_settings.transactions.extend(fake_txs)
        # Trigger rebuild
        self.force_refresh()


# </component>
