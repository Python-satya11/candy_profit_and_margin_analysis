# Nassau Candy Distributor - Column Dictionary

| Column | Description |
|---|---|
| Row ID | Unique row identifier for the dataset record. |
| Order ID | Identifier for the order associated with the transaction record. |
| Order Date | Date on which the order was placed. |
| Ship Date | Date on which the order was shipped. |
| Ship Mode | Shipping method used for the order. |
| Customer ID | Identifier for the customer associated with the order. |
| Country/Region | Country or geographic country/region associated with the transaction. |
| City | City associated with the transaction. |
| State/Province | State or province associated with the transaction. |
| Postal Code | Postal or ZIP code associated with the transaction. |
| Division | Business/product division, such as Chocolate, Other, or Sugar. |
| Region | Geographic sales region, such as Pacific, Atlantic, Interior, or Gulf. |
| Product ID | Unique identifier for the product. |
| Product Name | Name of the product. |
| Sales | Total sales value of the order line. |
| Units | Number of units sold in the order line. |
| Gross Profit | Gross profit for the order line, defined in this project as Sales minus Cost. |
| Cost | Cost associated with the order line. |
| Gross Margin % | Derived metric: (Gross Profit / Sales) × 100. |
| Profit per Unit | Derived metric: Gross Profit / Units. |

## Notes

The first 18 fields are the original dataset columns. **Gross Margin %** and **Profit per Unit** were created during feature engineering and are derived analytical fields.
