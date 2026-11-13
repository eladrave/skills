---
name: monthly-home-finance
description: Create or regenerate the user's monthly consolidated expense report from SimpleFIN, Privacy and Amazon, and save a reconciled Google Sheet in Home Finance.
---

# Monthly Home Finance

Create a transaction-level report with merchant details, Amazon items, explicit source accounts and reconciled totals.

## Scope and destination

- Default accounts: Chase checking **2169**, Chase Sapphire Reserve **1335**, and Chase Sapphire Reserve **6535**. Resolve their current SimpleFIN account IDs from the live account inventory. Retrieve transaction history only for those accounts. Follow an explicit user override.
- Use the requested calendar month. When invoked without a month, report the previous calendar month in **America/New_York**. The intended recurring use is on the **2nd of each month**.
- Include posted transactions by **bank posting date**, from the first day inclusive to the next month's first day exclusive. Exclude pending transactions. Supporting orders and Privacy records may fall outside the reporting month.
- Save in [Home Finance](https://drive.google.com/drive/folders/1UUQjeq2CIrTDTK7yzfL1B1Fl0b8Mhsov). Find an existing report for the month before creating one. Regenerate that report in place when requested, preserving its URL, location and sharing. Leave other months unchanged.
- Use the [October 2026 report](https://docs.google.com/spreadsheets/d/1xEzps6MhTeINc6UNmvPjbk0K4fFAJ3ORx124oQJJngY/edit) as the format reference. Derive dates, counts and totals from current source data.
- This skill does not create or modify a schedule. Scheduling requires a separate user request.

## Retrieve the bank records

1. Discover the available connectors. Call `simplefin_status`, then inspect the account inventory and uniquely resolve the authorized accounts. If an account is missing or ambiguous, report the issue before retrieving a different account.
2. Retrieve bounded transaction ranges with pending transactions excluded. Include a boundary buffer and locally filter `posted_at`: the connector's date query can include records posted outside the requested month. Prefer short requests; split surrounding windows when necessary.
3. Check source errors, missing-data indicators and synchronization freshness, particularly when running on the 2nd. Do not present incomplete history as a complete report. Explain the specific gap and preserve useful progress.
4. Preserve source account, transaction ID, original descriptor, signed amount, posting date and transaction date. SimpleFIN amounts use positive credits and negative debits. Display credits and debits as positive amounts in separate columns; net outflow is debit minus credit. Use integer cents or decimal arithmetic for matching and reconciliation.

## Identify Privacy merchants

- For each Privacy bank debit or credit, retrieve supporting Privacy records. For debits, start with **settled**, exact-amount records created on the bank date or within the preceding **7 calendar days**, using Eastern dates.
- Match records one-to-one across the report. Check prior-month selected evidence near the boundary so one Privacy record is not reused. Treat amount/date matches as candidates when the funding-account identity is unavailable.
- If prior-month selection history cannot be checked, disclose that cross-month evidence reuse remains unverified.
- Preserve candidate merchants, source IDs, dates and matching notes. Do not pick a merchant merely because its date is closest when multiple feasible assignments remain.
- If several candidate records identify the same merchant, distinguish a known merchant from unresolved record assignment. If two bank debits share one eligible Privacy record, flag the evidence shortfall instead of assigning it twice.
- Handle refunds and reversals according to their source type and sign. A broader date window needs supporting evidence and an explanation.

## Itemize Amazon activity

- Resolve Amazon charges and refunds on each included card against **actual payment records**, checking exact amount, charge/refund direction, the source card ending (normally **1335 or 6535**), and date proximity. Order dates alone do not establish the bank match. Record the matching date window; if multiple feasible payments remain, require additional reference evidence or flag the assignment. Do not resolve a tie by date proximity alone.
- Use bounded order-history pages and individual order-detail calls. Keep list-level `all_pages` and `full_details` false where those options exist. Follow returned pagination markers. Search earlier orders when shipping or payment is delayed.
- If general payment history fails, try per-order payment lookups. If authentication or another technical issue blocks progress, notify the user and identify the affected records.
- Replace a verified purchase's bank row with separate item rows. Account for quantities, discounts, tax, shipping and split payments. Allocate shared adjustments with exact-cent rounding and label estimates. Never assign the whole order to every shipment or every payment card.
- Do not reuse one payment to match multiple bank charges unless source evidence documents the split and the allocations reconcile.
- When source quantities are omitted, use one unit per source line only if that interpretation reconciles the complete order subtotal; disclose the inference. Keep unexplained residuals explicitly labeled rather than presenting them as verified item costs.
- For indistinguishable equal-value charges, preserve the unresolved bank rows and show candidate item details separately as **non-additive evidence**, with blank allocated bank amounts. Do not count those details again.
- Identify services without retail item details and unmatched refunds explicitly. A Whole Foods store descriptor alone is not evidence of an online Amazon order or its items.
- When a refund matches a payment and order but the refunded item is unknown, retain the bank refund amount and flag item identification as unresolved. Do not allocate the refund across the original items without supporting evidence.

## Build the report

Follow the available Google Sheets and spreadsheet authoring skills. Produce a native Google Sheet with these tabs:

| Tab | Required content |
| --- | --- |
| Summary | Scope, per-account counts and activity, combined purchases after refunds, excluded repayments/transfers, other payments, matching issues and reconciliation differences. |
| Transactions | Every source transaction or its replacement Amazon item rows. Include a prominent **Source account** column identifying **2169**, **1335**, **6535**, or an explicitly authorized override on every row. |
| Bank activity | One row per original bank transaction, source account, original values, treatment, allocated total and difference. |
| Privacy matches | Bank reference, source account, candidate/selected evidence, merchant, dates and uncertainty. |
| Amazon detail | Source account, bank/payment/order references, items, allocation components and method, plus clearly separated evidence-only rows. |

Keep dates and amounts typed, use filters and frozen headers for detail, and preserve traceable source IDs. Create formulas for summary and reconciliation calculations. For regeneration, refresh formulas, filters and exception formatting through the final populated row.

Apply these accounting rules:

- Keep checking-to-card repayments and corresponding card payment credits in activity, excluding both from purchases and income. Recognize payments between **2169 and either Sapphire card** without counting them as new expenses.
- Keep account transfers separate from spending. Show person-to-person payments separately when purpose is unconfirmed. Show loan/lease payments separately when principal/interest splits are unavailable, and cash withdrawals separately when use is unknown.
- Distinguish cash inflows from income. Count merchant refunds in the month credited under the posting-date rule, even if the purchase was earlier.
- In expanded Amazon rows, count the item allocations instead of also counting the original charge.

## Verify and deliver

Before reporting completion, verify:

1. Every included source record has the authorized account and posting month, with no duplicate source IDs or pending rows.
2. For each bank transaction, allocated credits minus allocated debits equal its original signed amount to the cent. Evidence-only rows contribute nothing to totals.
3. Debits and credits reconcile separately, both by account and combined. Purchases exclude repayments and transfers. Count exceptions by affected source bank transaction, not by candidate records or expanded item rows. Report row counts separately from source transaction counts.
4. Every expense row has the correct source account. Privacy evidence is not reused; Amazon matches use the correct card. No unsupported assignment is labeled verified.
5. The saved Google Sheet has the correct title, tabs, folder, formulas and values. Read it back, check formula errors and inspect the rendered layout. A successful write alone is not completion.

Return the verified sheet link, transaction/report row counts, reconciliation result and material unresolved matches or technical limitations. Do not claim the file is private without checking its actual sharing.
