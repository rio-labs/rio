import rio

# <additional-imports>
from .. import components as comps
from .. import constants

# </additional-imports>


# <component>
class TransactionsOverview(rio.Component):
    """
    A component that provides an overview of all user transactions.

    The component displays a list of transactions in a styled format, including:
    - Transaction details such as type, amount, and date.
    - Separators between transactions for visual distinction.
    - A header titled "Transaction" for context.
    """

    def build(self) -> rio.Component:
        # Create a column to hold the transaction list
        content = rio.Column(spacing=1)

        # Get the total number of transactions to determine where separators are
        # needed
        total_transactions = len(constants.TRANSACTIONS)

        for i, transaction in enumerate(constants.TRANSACTIONS):
            # Add a styled transaction component for the current transaction
            content.add(comps.StyledTransaction(transaction))

            # Add a separator if the current item is not the last in the list
            if i < total_transactions - 1:
                content.add(rio.Separator())

        return comps.ContentCard(
            header="Transaction",
            content=content,
        )


# </component>
