# Dataset: UCI Online Retail II

This project uses the **UCI Online Retail II** dataset.

## Source

https://archive.ics.uci.edu/dataset/502/online+retail+ii

## File

Place `online_retail_II.xlsx` in this directory.

## Dataset Description

The dataset contains transaction-level retail data from a UK-based online retailer.

### Columns

- **Invoice**: Invoice number (prefix "C" indicates cancellation)
- **StockCode**: Product (SKU) code
- **Description**: Product description
- **Quantity**: Quantity of items in the transaction
- **InvoiceDate**: Transaction date and time
- **Price**: Unit price
- **Customer ID**: Customer identifier
- **Country**: Customer country

### Coverage

- Period: December 2009 to December 2011
- ~1M transactions across two sheets
- ~4,000-5,000 unique SKUs
- ~4,300 unique customers
- 38-40 countries

## Preprocessing

The cleaning pipeline:

1. Removes duplicate rows
2. Removes cancelled invoices (Invoice starting with "C")
3. Removes returns (negative quantities)
4. Removes invalid prices (Price <= 0)
5. Removes invalid quantities (Quantity <= 0)
6. Fills missing descriptions and customer IDs with "unknown"

## Aggregation

Transactions are aggregated to daily SKU-level demand:

- Date x StockCode
- DailyDemand: sum of quantities
- Revenue: sum of quantity * price
- NumberOfTransactions: unique invoice count
- AvgPrice: mean unit price per day
