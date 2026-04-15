"""
Route Definitions for FinBot Semantic Router.

Each route represents a departmental intent with at least 10 representative
utterances used to train the semantic classifier.
"""

from semantic_router import Route


# ---------------------------------------------------------------------------
# 1. Finance Route
# ---------------------------------------------------------------------------
finance_route = Route(
    name="finance_route",
    utterances=[
        "What was the revenue for Q3 2024?",
        "Show me the latest budget allocations for the R&D department.",
        "Tell me about our investor relations strategy.",
        "How much did we spend on marketing last year?",
        "Give me a summary of the annual financial report FY2024.",
        "What are the current financial projections for next quarter?",
        "Are there any updates on dividends for shareholders?",
        "List all major expenses recorded in the audit.",
        "What is the net profit margin for this fiscal year?",
        "Find details about the Q3 earnings call summary.",
        "What is the company's debt-to-equity ratio?",
        "Show me the cash flow statement for last quarter.",
        "Tell me the finance report executive summary for 2024.",
        "What is the executive summary of the financial report?",
        "Can you provide the executive summary for the finance department?",
        "Give me an executive summary of the finance status.",
    ],
)

# ---------------------------------------------------------------------------
# 2. Engineering Route
# ---------------------------------------------------------------------------
engineering_route = Route(
    name="engineering_route",
    utterances=[
        "How do I access the internal API?",
        "Explain the current system architecture.",
        "Where are the deployment runbooks stored?",
        "What was the root cause of the last system outage?",
        "Show me the technical specs for the indexing service.",
        "How do I onboard a new microservice?",
        "What database are we using for high-concurrency tasks?",
        "Find the documentation for the auth-service.",
        "List the steps for emergency rollback.",
        "Provide details on the Kubernetes cluster configuration.",
        "What CI/CD pipeline do we use for production deployments?",
        "How is the logging infrastructure set up?",
    ],
)

# ---------------------------------------------------------------------------
# 3. Marketing Route
# ---------------------------------------------------------------------------
marketing_route = Route(
    name="marketing_route",
    utterances=[
        "What are the official brand colors?",
        "Give me an overview of the Spring Surge campaign.",
        "How is our market share compared to Competitor X?",
        "Show me the latest market research findings.",
        "What is the primary target audience for our new product?",
        "List the active marketing channels for Q4.",
        "Where can I find the brand logo assets?",
        "Summarize the competitor analysis report.",
        "What is the ROI on our social media campaigns?",
        "Tell me about our brand positioning strategy.",
        "How did the email campaign perform last month?",
        "What is our customer acquisition cost trend?",
        "What is the executive summary of the annual marketing report 2024?",
        "Give me a summary of the marketing performance report.",
        "Find the latest marketing campaign summary.",
        "Show me the annual marketing report for this year.",
    ],
)

# ---------------------------------------------------------------------------
# 4. HR / General Route
# ---------------------------------------------------------------------------
hr_general_route = Route(
    name="hr_general_route",
    utterances=[
        "What is the company's leave policy?",
        "How do I apply for health insurance benefits?",
        "Where is the HR handbook located?",
        "What are the company's core values?",
        "Show me the code of conduct document.",
        "How many sick days are allowed per year?",
        "What is the policy for remote work?",
        "Tell me about the employee referral program.",
        "When is the next company-wide meeting?",
        "What is the procedure for reporting a grievance?",
        "How do I submit a reimbursement request?",
        "What holidays does the company observe?",
    ],
)

# ---------------------------------------------------------------------------
# 5. Cross-Department Route
# ---------------------------------------------------------------------------
cross_department_route = Route(
    name="cross_department_route",
    utterances=[
        "Give me a general overview of the company status.",
        "What major updates happened across all departments this month?",
        "Are there any cross-departmental initiatives currently active?",
        "Tell me everything about the new product launch from both design and marketing perspectives.",
        "How do departmental budgets align with our engineering goals?",
        "Show me general news and financial highlights.",
        "I have a broad question about company operations.",
        "List all ongoing projects across the organization.",
        "What are the key priorities for this fiscal year overall?",
        "Summarize recent reports from all sectors.",
        "What is the overall company performance this quarter?",
        "Give me a combined update from HR, finance, and engineering.",
    ],
)

# ---------------------------------------------------------------------------
# Aggregate list for easy import
# ---------------------------------------------------------------------------
ALL_ROUTES = [
    finance_route,
    engineering_route,
    marketing_route,
    hr_general_route,
    cross_department_route,
]
