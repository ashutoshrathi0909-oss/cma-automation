# Scoped Classification v2 — Accuracy Report

Generated: 2026-03-26 07:10:08
Ground truth: BCIPL (448 items)

## Overall Metrics

| Metric | Value | Baseline | Delta |
|--------|-------|----------|-------|
| Overall accuracy | 62.7% | 87% | -24.3pp |
| Doubt rate | 5.4% | 13% | -7.6pp |
| Accuracy within classified | 66.3% | — | — |
| Wrong items | 143 | — | — |
| Doubt items | 24 | — | — |
| Total elapsed | 1158s | — | — |

## Error Categories

| Category | Count | % of errors | Fix |
|----------|-------|-------------|-----|
| Confident wrong (both agreed, wrong row) | 131 | 92% | Improve prompt/examples |
| Debate wrong (debated, still wrong) | 12 | 8% | Strengthen debate prompt |
| Single-model wrong | 0 | 0% | Model failure / retry |
| Other wrong | 0 | 0% | Investigate |

## Section Routing Analysis

Items whose section text contains 'other expenses': **25**
- Routed to `admin_expense`: 25
- Routed to `manufacturing_expense`: 0

## Top 5 Worst Sections

| Section | Total | Correct | Accuracy | Wrong | Doubt |
|---------|-------|---------|----------|-------|-------|
| investments | 1 | 0 | 0.0% | 1 | 0 |
| admin_expense | 90 | 20 | 22.2% | 59 | 11 |
| borrowings_short | 4 | 1 | 25.0% | 3 | 0 |
| tax | 10 | 3 | 30.0% | 6 | 1 |
| selling_expense | 9 | 3 | 33.3% | 5 | 1 |

## Model Self-Diagnosis (Top Patterns)

Patterns detected in model interrogation responses:

| Pattern | DeepSeek V3 | Gemini Flash |
|---------|-------------|--------------|
| correct_row_not_in_list | 12 | 10 |
| defaulted_to_others | 7 | 0 |
| ambiguous_item_text | 6 | 4 |
| conflicting_examples | 0 | 2 |
| model_reasoning_error | 20 | 7 |

## Top 10 Worst Errors (with Model Explanations)

### 1. `Consumption of Stores & Spares`
- **Section:** `other expenses` → routed to `admin_expense`
- **Correct:** Row 44 (Stores and spares consumed ( Indigenous))
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** 1. **Was Row 44 (Stores and spares consumed ( Indigenous)) even in the list you were shown? (Yes/No)**  
   No, Row 44 was not in the list of possible CMA rows provided in the prompt.

2. **If yes, why did you pick Row 71 instead?**  
   N/A (Row 44 was not an option in the prompt.)

3. **What in the prompt confused you or led you to the wrong answer?**  
   The prompt only provided a limited set of CMA rows to choose from, and Row 44 was not included. The examples from other companies mentioned Row 44, but it wasn't an available option in the classification task.

4. **What change to the prompt would have helped you pick the correct row?**  
   Including Row 44 (Stores and spares consumed ( Indigenous)) in the list of possible CMA rows would have allowed for the correct classification. Additionally, clarifying that "Consumption of Stores & Spares" should be mapped to Row 44, even if it’s not explicitly listed, would have helped.

**Gemini Flash:** 1. No
2. N/A
3. Row 44 was not in the list of possible CMA rows provided. I followed the instructions and picked the best matching row from the provided list, which was "Others" based on the provided rules for similar expense types.
4. Including Row 44 (Stores and spares consumed ( Indigenous)) in the list of possible CMA rows would have allowed me to select the correct answer.

### 2. `Other Materials Comsumed - Scrap`
- **Section:** `note 21 - other materials consumed` → routed to `admin_expense`
- **Correct:** Row 44 (Stores and spares consumed ( Indigenous))
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** Here's the JSON response first:  
```json
{"cma_row": 44, "cma_code": "II_D44", "confidence": 0.9, "reasoning": "Scrap aligns with stores/spares"}
```

Answers to your questions:  
1. **No**, Row 44 was not in the original POSSIBLE CMA ROWS list provided.  
2. I picked Row 71 ("Others") because:  
   - Row 44 was missing from the options.  
   - "Other Materials Consumed - Scrap" lacked explicit mapping rules, defaulting to "Others".  
3. **Confusion points**:  
   - The prompt excluded Row 44 as a possible choice despite it being the correct classification.  
   - The EXAMPLES section (e.g., "Packing Expenses" → Row 44) contradicted the absence of Row 44 in the main list.  
4. **Needed change**:  
   - Include Row 44 in the POSSIBLE CMA ROWS list upfront.  
   - Add a classification rule like: `"Scrap" → Row 44 (Stores and spares consumed)` to avoid ambiguity.  

The error stemmed from incomplete options, not reasoning.

**Gemini Flash:** 1. Yes
2. I picked Row 71 because the classification rules had many examples of expenses being classified as "Others". I didn't see a direct match for "scrap" and defaulted to the general "Others" category.
3. The prompt was missing a clear rule or example that would directly link "scrap" or "materials consumed" to "Stores and spares consumed (Indigenous)". The examples provided for Row 44 were related to "Packing", which didn't seem directly relevant to "scrap".
4. Adding a classification rule like: "Materials Consumed (including scrap)" -> Row 44 (Stores and spares consumed ( Indigenous)) or an example like "Scrap Materials" -> Row 44 would have helped me pick the correct row.

```json
{"cma_row": 44, "cma_code": "II_D1", "confidence": 0.9, "reasoning": "\"Scrap\" is a material consumed, thus stores and spares consumed (Indigenous)."}
```

### 3. `Directors Remuneration`
- **Section:** `salaries & wages` → routed to `employee_cost`
- **Correct:** Row 67 (Salary and staff expenses)
- **Predicted:** Row 73 (Audit Fees & Directors Remuneration)

**DeepSeek V3:** 1. **Was Row 67 (Salary and staff expenses) even in the list you were shown? (Yes/No)**  
   Yes.

2. **If yes, why did you pick Row 73 instead?**  
   I picked Row 73 because the example provided in the prompt explicitly stated:  
   `"Directors Remuneration" → Row 73 (Audit Fees & Directors Remuneration)`.  
   This example directly influenced my decision.

3. **What in the prompt confused you or led you to the wrong answer?**  
   The example `"Directors Remuneration" → Row 73` was misleading because it contradicted the correct classification rule. The prompt did not clarify that Row 67 (Salary and staff expenses) was the correct row for "Directors Remuneration" despite the example.

4. **What change to the prompt would have helped you pick the correct row?**  
   Adding a classification rule like:  
   `"Directors Remuneration" → Row 67 (Salary and staff expenses)`  
   would have clarified the correct row and overridden the misleading example.

**Gemini Flash:** ```json
{"cma_row": 67, "cma_code": "II_D1", "confidence": 0.95, "reasoning": "Directors remuneration is a salary expense, fitting 'Salary and staff expenses'."}
```

1. Yes
2. I relied too heavily on the single example provided: "Directors Remuneration" → Row 73 (Audit Fees & Directors Remuneration). I should have prioritized the section information "salaries & wages" and the general meaning of "Directors Remuneration" as a form of salary.
3. The example "Directors Remuneration" → Row 73 (Audit Fees & Directors Remuneration) was misleading, especially since it was the only direct example for the item. It outweighed the general understanding that director remuneration falls under salary expenses.
4. Removing or correcting the misleading example "Directors Remuneration" → Row 73 (Audit Fees & Directors Remuneration) would have helped. Alternatively, adding more examples showing similar items classified under salary expenses would have been beneficial.

### 4. `Job Work Charges & Contract Labour`
- **Section:** `other expenses` → routed to `admin_expense`
- **Correct:** Row 46 (Processing / Job Work Charges)
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** 1. No, Row 46 (Processing / Job Work Charges) was not in the list of possible CMA rows provided in the prompt.  

2. I picked Row 71 ("Others") because:  
   - The classification rules listed "General expenses," "Conveyance," and other indirect expenses under Row 71.  
   - "Job Work Charges & Contract Labour" wasn’t explicitly mapped to any other row in the rules or examples.  

3. The confusion arose because:  
   - The prompt limited choices to a predefined set (Rows 67-77), and Row 46 wasn’t an option.  
   - The only guidance for similar items (e.g., "Packing charges") defaulted to Row 71.  

4. A change that would have helped:  
   - Including Row 46 explicitly in the "POSSIBLE CMA ROWS" list or adding a rule like:  
     `- "Job Work Charges" → Row 46 (Processing / Job Work Charges)`  

Final correction (had Row 46 been an option):  
```json
{"cma_row": 46, "cma_code": "II_D_Processing", "confidence": 0.9, "reasoning": "Directly matches job work charges"}
```  

Your original classification ("Row 71 - Others") was technically correct *given the limited options*, but the system should have included Row 46 as a valid choice.

**Gemini Flash:** ```json
{
"cma_row": 0,
"cma_code": null,
"confidence": 0.1,
"reasoning": "Row 46 was not in the provided list. I cannot select an option not given."
}
```

1. No
2. Row 46 was not in the list of possible rows.
3. The correct answer was not in the list of possible rows.
4. Including Row 46 (Processing / Job Work Charges) in the list of possible rows.

### 5. `Power & Fuel`
- **Section:** `other expenses` → routed to `admin_expense`
- **Correct:** Row 48 (Power, Coal, Fuel and Water)
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** 1. **Was Row 48 (Power, Coal, Fuel and Water) even in the list you were shown? (Yes/No)**  
   No.

2. **If yes, why did you pick Row 71 instead?**  
   N/A (Row 48 was not in the list).

3. **What in the prompt confused you or led you to the wrong answer?**  
   The list of possible CMA rows did not include Row 48, which is the correct row for "Power & Fuel." The absence of Row 48 forced me to choose the closest available option, Row 71 (Others).

4. **What change to the prompt would have helped you pick the correct row?**  
   Including Row 48 (Power, Coal, Fuel and Water) in the list of possible CMA rows would have allowed me to classify the item correctly.

**Gemini Flash:** ```json
{"cma_row": 0, "cma_code": null, "confidence": 0.0, "reasoning": "Row 48 was not in the provided list of possible CMA rows."}
```

1. No
2. Row 48 was not in the list of possible rows. I picked Row 71 because it was the "catch-all" category.
3. The prompt did not include Row 48 in the list of possible CMA rows.
4. Including Row 48 (Power, Coal, Fuel and Water) in the list of possible CMA rows would have helped me pick the correct row.

### 6. `Manufacturing Expenses`
- **Section:** `auditor's remuneration:` → routed to `admin_expense`
- **Correct:** Row 49 (Others)
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** Here's the JSON response along with answers to your questions:  

```json
{"cma_row": 49, "cma_code": "II_D5", "confidence": 0.9, "reasoning": "Manufacturing expenses defaults to Others."}
```

**Answers to your questions:**  
1. **Yes**, Row 49 ("Others") was in the list (Row 71 was labeled "II_D5 | Others").  
2. I picked **Row 71** initially because "Manufacturing Expenses" was not explicitly covered in the rules, and "Others" seemed the safest fallback.  
3. **What confused me:** The classification rules did not explicitly define "Manufacturing Expenses," and since other unclassified expenses tend to go to Row 71, I defaulted there.  
4. **What would have helped:** A rule like: _"Manufacturing Expenses (not clearly attributable to production) → Row 49 (Others)"_ would have made it unambiguous.  

(Note: You originally said **Row 49** is correct, but in the list, **Row 71** is II_D5/"Others"—same as Row 49's classification. If Row 49 is truly the intended answer, the CMA row numbering may need verification.)

**Gemini Flash:** ```json
{"cma_row": 71, "cma_code": "II_D5", "confidence": 0.8, "reasoning": "Manufacturing expenses are general and fall under the 'Others' category based on the rules."}
```

1. No
2. N/A
3. The prompt contained two different lists of "POSSIBLE CMA ROWS". The first list (Rows 67-77) was used for the classification. The second list (Rows 44-71) was only used in the "EXAMPLES FROM OTHER COMPANIES" section. I incorrectly assumed that the examples were using the same list of rows as the classification task.
4. The prompt should have only included one list of "POSSIBLE CMA ROWS" and the examples should have referenced that list. Alternatively, the prompt could have explicitly stated that the examples were using a different list of rows.

### 7. `Machinery Maintenance`
- **Section:** `other expenses` → routed to `admin_expense`
- **Correct:** Row 49 (Others)
- **Predicted:** Row 72 (Repairs & Maintenance)

**DeepSeek V3:** Here's the JSON response with reflection on the mistake:

```json
{"cma_row": 49, "cma_code": "II_D5", "confidence": 0.95, "reasoning": "Machinery maintenance doesn't match repair-specific examples"}
```

Answers to your questions:
1. Yes, Row 49 (Others) was shown as Row 71 | II_D5 | Others
2. Tunnel vision on "Maintenance" → saw "Repairs & Maintenance" and stopped evaluating other options
3. The example "Building Maintenance → Repairs" misled me to generalize all maintenance
4. Adding "Machinery Maintenance → Others" as an explicit classification rule would have prevented this error

Key realization: "Repairs & Maintenance" applies only when explicitly tied to building/facility upkeep, while machinery maintenance defaults to Others unless specified otherwise in the rules.

**Gemini Flash:** ```json
{"cma_row": 71, "cma_code": "II_D5", "confidence": 0.9, "reasoning": "Machinery maintenance is not explicitly repairs, so it falls under 'Others'."}
```

1. Yes
2. I was overly influenced by the rule "Building Maintenance (Others) → Row 72 (Repairs & Maintenance)". I incorrectly generalized this to all maintenance.
3. The rule about "Building Maintenance" being classified as "Repairs & Maintenance" led me to believe that "Machinery Maintenance" should also be classified as "Repairs & Maintenance". I failed to recognize that the "Others" in "Building Maintenance (Others)" was meant to indicate that it was *not* a typical repair.
4. A rule explicitly stating that "Machinery Maintenance" falls under "Others" or a clarification that only *building* maintenance goes to "Repairs & Maintenance" would have helped. Also, the examples from other companies did not include any maintenance examples, which could have been helpful.

### 8. `Depreciation`
- **Section:** `depreciation & amortisation expense` → routed to `depreciation`
- **Correct:** Row 63 (Depreciation)
- **Predicted:** Row 56 (Depreciation)

**DeepSeek V3:** Here's the JSON response followed by answers to your questions:

```json
{"cma_row": 63, "cma_code": "II_C20", "confidence": 1.0, "reasoning": "Exact match for Depreciation"}
```

Answers to your questions:
1. Yes, Row 63 (Depreciation) was in the list I was shown
2. I initially picked Row 56 because it also showed "Depreciation" in the label and I didn't carefully check the codes
3. The prompt confused me because:
   - Both Row 56 and Row 63 were labeled "Depreciation"
   - I didn't carefully compare the codes (II_C14 vs II_C20)
   - No rules specifically distinguished between these depreciation rows
4. These prompt changes would have helped:
   - Clearer distinction rules for depreciation (e.g., "Depreciation expense → Row 63")
   - More examples showing depreciation mapped to Row 63 specifically
   - Removing the duplicate label or adding codes in parentheses in the list

**Gemini Flash:** ```json
{"cma_row": 63, "cma_code": "II_C20", "confidence": 0.95, "reasoning": "There are two depreciation rows, and the section implies it's a manufacturing expense."}
```

1. Yes
2. I initially chose Row 56 because the example "To Depreciation" mapped to it. I overlooked the section "depreciation & amortisation expense" which strongly suggests it belongs to the manufacturing expense section, where Row 63 is located.
3. The example "To Depreciation" mapping to Row 56 was misleading. It made me prioritize the example over the contextual information provided by the "depreciation & amortisation expense" section.
4. Adding a rule that prioritizes the section information when multiple rows have the same name would be helpful. For example: "When multiple rows have the same name, prioritize the row that aligns with the section the item belongs to."

### 9. `Amortization Expenses`
- **Section:** `depreciation & amortisation expense` → routed to `depreciation`
- **Correct:** Row 63 (Depreciation)
- **Predicted:** Row 56 (Depreciation)

**DeepSeek V3:** 1. **Was Row 63 (Depreciation) even in the list you were shown? (Yes/No)**  
   Yes.

2. **If yes, why did you pick Row 56 instead?**  
   I focused on the term "Depreciation" in the examples and rules, which linked to Row 56, and overlooked Row 63.

3. **What in the prompt confused you or led you to the wrong answer?**  
   The examples explicitly linked "Depreciation" to Row 56, and Row 63 wasn’t highlighted or explained as an alternative.

4. **What change to the prompt would have helped you pick the correct row?**  
   Adding a rule or example explicitly stating: "Amortization Expenses → Row 63 (Depreciation)" would have clarified the distinction.

**Gemini Flash:** Here's an analysis of my mistake and how to improve the prompt:

1.  Was Row 63 (Depreciation) even in the list you were shown? **Yes**

2.  If yes, why did you pick Row 56 instead? I picked Row 56 because the example "To Depreciation" mapped to Row 56. I prioritized the example over the fact that there were two "Depreciation" rows.

3.  What in the prompt confused you or led you to the wrong answer? The prompt was confusing because it included two rows with the exact same name ("Depreciation"). This made it unclear which one was the correct choice, and I relied too heavily on the example provided.

4.  What change to the prompt would have helped you pick the correct row? The prompt should have included additional information to differentiate between the two "Depreciation" rows. This could have been done by:

    *   Adding more context to the row names (e.g., "Depreciation - Tangible Assets", "Depreciation - Intangible Assets").
    *   Providing more specific classification rules that would help distinguish between the two.
    *   Removing the duplicate row if they are truly identical.

Here's the corrected JSON response:

```json
{"cma_row": 63, "cma_code": "II_C20", "confidence": 0.9

### 10. `Packing Materials - GST @ 12%`
- **Section:** `selling and distribution expenses - subnotes` → routed to `selling_expense`
- **Correct:** Row 70 (Advertisements and Sales Promotions)
- **Predicted:** Row 71 (Others)

**DeepSeek V3:** ```json
{
  "cma_row": 70,
  "cma_code": "II_D4",
  "confidence": 0.9,
  "reasoning": "Packing materials aid sales promotions"
}
```

1. **Was Row 70 (Advertisements and Sales Promotions) even in the list you were shown? (Yes/No)**  
   **Yes**, Row 70 was in the list.

2. **If yes, why did you pick Row 71 instead?**  
   Initially misinterpreted "Packing Materials" as a generic expense (like "Packing charges" in rules) rather than a sales-enabling cost.  

3. **What in the prompt confused you or led you to the wrong answer?**  
   The rule *"Packing charges → Row 71 (Others)"* seemed to directly apply, but missed the nuance that secondary packing (for sales/distribution) aligns with promotions.  

4. **What change to the prompt would have helped you pick the correct row?**  
   Clarify if packing is *primary* (manufacturing) or *secondary* (sales/distribution). Example:  
   *"Secondary packing materials → Row 70 (Advertisements and Sales Promotions)"*  
   *"Primary packing → Include in manufacturing costs"*.  
   Alternatively, highlight examples like *"Delivery Expenses → Row 70"* to show sales-related classification.  

(Note:

**Gemini Flash:** ```json
{
  "cma_row": 70,
  "cma_code": "II_D4",
  "confidence": 0.9,
  "reasoning": "Packing materials are used for sales promotions and are part of distribution expenses."
}
```

1. Yes
2. I was misled by the rule "Packing charges" → Row 71 (Others). I didn't fully consider the context of "selling and distribution expenses" and the connection to sales promotions.
3. The rule "Packing charges" → Row 71 (Others) was too general and didn't account for packing materials specifically used for sales and distribution.
4. A more specific rule like "Packing materials for sales promotions" → Row 70 (Advertisements and Sales Promotions) would have helped. Also, highlighting the connection between packing materials and sales promotions in the examples would have been beneficial.

## Recommended Fixes (prioritized)

1. **131 items where both models agreed on the wrong row** — add more disambiguation examples in the scoped context for the worst sections
2. **12 items failed after debate** — strengthen the debate prompt to penalize 'Others' row selection and require explicit reasoning
3. **Section `investments` accuracy 0.0%** — review routing regex and add more training examples
4. **Section `admin_expense` accuracy 22.2%** — review routing regex and add more training examples
5. **Section `borrowings_short` accuracy 25.0%** — review routing regex and add more training examples

---
*Generated by `run_bcipl_full.py`. 448 items tested. API calls in Phase 3: 60.*