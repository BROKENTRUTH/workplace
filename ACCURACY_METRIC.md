## Suggested Metrics for Accuracy Assessment

The accuracy of the information extraction process from technical PDF documents can be assessed by comparing the script's output against a manually curated "ground truth" dataset. This ground truth would be created by a human expert for one or more representative test documents.

Here's a combination of metrics suggested for a comprehensive evaluation:

### 1. Field-Level Precision, Recall, and F1-Score

This metric evaluates the performance for each of the main extracted fields:
*   `Test Name/Reference Code/Standard as per the given document (with reference page number)`
*   `Specific Material Type/Material Definition`
*   `Any other relevant information`

**Concept:**
For each field within each material, the set of extracted strings (e.g., individual test names, specific definitions) are treated as predictions.

**Ground Truth Requirement:**
A human expert would list all correct items that *should* be extracted for each field for every material in the test document(s).

**Calculation Steps:**
For each field within each material:
*   **True Positives (TP):** Extracted items that are present in the ground truth for that specific field and material.
*   **False Positives (FP):** Extracted items that are *not* present in the ground truth (i.e., the script extracted something incorrect or irrelevant).
*   **False Negatives (FN):** Items that *are* present in the ground truth but were *not* extracted by the script.

From these counts, calculate:
*   **Precision (P) = TP / (TP + FP)**
    *   *Interpretation:* Of all the items the script extracted for a field, what proportion was actually correct?
*   **Recall (R) = TP / (TP + FN)**
    *   *Interpretation:* Of all the correct items that should have been extracted for a field, what proportion did the script successfully find?
*   **F1-Score = 2 * (Precision * Recall) / (Precision + Recall)**
    *   *Interpretation:* The harmonic mean of Precision and Recall, providing a single score that balances both. Useful when there's an uneven class distribution or when both false positives and false negatives are important.

**Application:**
These scores can be calculated per field per material. They can then be averaged (e.g., macro-average or micro-average) across all materials for each field type, or even across all fields and materials to get an overall performance snapshot. This approach is well-suited for fields that can contain multiple distinct pieces of information (e.g., a list of tests).

**Note on Matching:** Determining a "match" between an extracted item and a ground truth item might require:
*   Exact string comparison.
*   Normalized comparison (e.g., ignoring case, extra whitespace, or minor punctuation differences).
*   Using a string similarity threshold (e.g., Levenshtein distance) if partial textual matches are considered acceptable. The definition of a "match" should be consistent.

### 2. Exact Match Ratio (EMR) for Materials

**Concept:**
A stricter, holistic metric that assesses if *all* information for a given material is extracted perfectly as per the ground truth.

**Calculation:**
1.  For each material in the ground truth:
2.  Compare the *entire set* of extracted items for *all* its fields (Tests, Definitions, Other Info) against the corresponding ground truth for that material.
3.  If every extracted item across all fields for that material exactly matches the ground truth (i.e., all required items are present, no extra items are extracted, and no required items are missing), then that material is considered an "exact match."
4.  **EMR = (Number of exactly matched materials) / (Total number of materials in the ground truth)**

**Usefulness:**
Provides a high-level view of overall record-level correctness. It's demanding but clearly indicates how many materials were processed flawlessly.

### 3. String Similarity Scores (for Textual Accuracy of Extractions)

**Concept:**
If the precise textual content of an extracted item is critical (beyond just its identification), string similarity metrics can quantify how close an extracted string is to its corresponding ground truth string.

**Examples of Metrics:**
*   **Normalized Levenshtein Distance:** Measures the minimum number of single-character edits (insertions, deletions, or substitutions) to change one string into another, normalized by the length of the longer string. A score of 0 means an exact match; a higher score means less similarity.
*   **Jaro-Winkler Distance:** Measures string similarity, typically giving more weight to strings that match from the beginning. Produces a score between 0 (no similarity) and 1 (exact match).

**Application:**
For all items identified as True Positives (TP) in the Field-Level F1-score calculation, compute the string similarity between the extracted string and the ground truth string. The average similarity score across all TPs can then be reported. This helps quantify the *quality* of the extracted text.

### Justification for Suggested Metrics

*   **Comprehensive Evaluation:** This combination of metrics provides a multi-faceted view of the extraction accuracy:
    *   F1-score (with Precision and Recall) assesses the ability to correctly identify and retrieve individual pieces of information.
    *   EMR evaluates the overall correctness at the material/record level.
    *   String similarity scores assess the textual fidelity of the extracted data.
*   **Actionable Insights:** Performance on these different metrics can guide improvements:
    *   Low precision might indicate overly broad extraction rules or misclassification.
    *   Low recall could mean rules are too narrow or miss relevant patterns.
    *   Low string similarity (despite correct identification) might point to issues in the raw text extraction from the PDF or subsequent text cleaning steps.
*   **Adaptability:** The strictness of what constitutes a "match" in the F1 calculation or for EMR can be tuned based on the specific requirements of the evaluation (e.g., is "ordinary portland cement" an acceptable match for "Ordinary Portland Cement"?).
*   **Standard Practice:** Precision, Recall, and F1-score are standard and widely understood metrics in Information Retrieval and Natural Language Processing tasks.

### Implementation Steps for Assessment

1.  **Prepare Test Data:** Select one or more representative PDF documents that the script is intended to process.
2.  **Create Ground Truth:** Manually and meticulously extract all required information from the test document(s) into the specified table format. This forms the gold standard for comparison. Ensure page numbers are accurately recorded in the ground truth.
3.  **Run the Script:** Process the same test document(s) using the script.
4.  **Compare Output to Ground Truth:** Programmatically or manually compare the script's output (e.g., the generated CSV file) against the ground truth data.
5.  **Calculate Metrics:** Based on the comparison, calculate the TP, FP, FN counts for each field and material, and then compute the Precision, Recall, F1-scores, EMR, and average string similarity scores.

This structured approach allows for a quantitative and objective assessment of the script's performance, highlighting both its strengths and areas needing refinement.
