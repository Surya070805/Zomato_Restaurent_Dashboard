# Data Dictionary

## Source Table: `zomato_cleaned.csv`

**Source scope:** historical Zomato restaurant listings for Bangalore. This is a snapshot without a collection date or restaurant-level revenue/customer data.

| Field | Type | Description | Downstream use |
| --- | --- | --- | --- |
| `url` | text | Zomato listing URL; query string contains listing context | Canonical restaurant business key after query string removal |
| `address` | text | Restaurant address | Restaurant detail only; normalize cautiously |
| `name` | text | Restaurant name | Restaurant dimension |
| `online_order` | categorical | Whether online ordering is shown as available | Service dimension / feature |
| `book_table` | categorical | Whether table booking is shown as available | Service dimension / feature |
| `rate` | text | Original display rating, such as `4.1/5` | Preserve for audit only |
| `votes` | integer | Observed Zomato vote count | Engagement proxy, not demand or revenue |
| `phone` | text | Restaurant phone number | Exclude from BI and ML outputs |
| `location` | text | Bangalore locality | Location dimension |
| `rest_type` | text | Restaurant category/type | Restaurant type dimension |
| `dish_liked` | text | User-liked dishes | Optional NLP only; exclude from rating model |
| `cuisines` | text | Comma-separated cuisine list | Cuisine bridge table |
| `approx_cost(for two people)` | text | Original price field | Preserve for audit only |
| `reviews_list` | text | Historical review text | Optional NLP only; exclude from rating model |
| `menu_item` | text | Menu information | Optional detail only |
| `listed_in(type)` | text | Listing category such as Dine-out or Delivery | Listing dimension |
| `listed_in(city)` | text | Zomato grouping called city in source | Reporting grouping; validate before calling city |
| `rate_clean` | decimal | Parsed numeric rating | Rating KPI / model target |
| `cost_clean` | decimal | Parsed cost for two | Price bands / model feature |

## Derived Fields

| Field | Rule | Purpose |
| --- | --- | --- |
| `restaurant_key` | SHA-256 of canonical URL (URL without query string) | Stable restaurant identity for distinct counts and grouped ML splits |
| `price_band` | Budget: `< 400`; Mid-range: `400-799`; Premium: `800+` | Dashboard segmentation; thresholds are project assumptions |
| `is_high_rated` | `rate_clean >= 4.0` and `votes >= 20` | More credible model label than rating alone |
| `cuisine_name` | Split `cuisines` on commas, trim, deduplicate per restaurant | Enables many-to-many cuisine analysis |

## Data Constraints

- A restaurant may appear multiple times because it is listed in multiple categories. Raw row count must not be used as restaurant count.
- Rating is an observed platform snapshot. It does not prove satisfaction, revenue, demand, or causal service impact.
- Votes are an engagement proxy and can be highly skewed.
- Do not use `reviews_list`, `dish_liked`, restaurant name, URL, or phone as predictive inputs for a new-restaurant rating scenario.
