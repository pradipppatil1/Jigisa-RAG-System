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
        # Onboarding & Benefits
        "What happens on my first day in the company?",
        "Explain onboarding process step by step",
        "What documents are required before joining?",
        "Do we get a mentor during onboarding?",
        "What benefits does the company provide?",
        "Is there health insurance for employees?",
        "Does insurance cover family members?",
        "What wellness programs are available?",
        "Do we get gym reimbursement?",
        "Tell me about employee referral program",
        "What perks do employees get?",
        "Explain company benefits",

        # Leave Policy
        "How many leaves do I get per year?",
        "What is sick leave policy?",
        "Can I carry forward my leaves?",
        "What is maternity leave policy?",
        "Do we get paternity leave?",
        "What is bereavement leave?",
        "How do I apply for leave?",
        "What happens if leave is rejected?",
        "What is leave without pay?",
        "How many vacation days do I get?",
        "Can I take unpaid leave?",
        "What is annual leave entitlement?",

        # Work Hours & Attendance
        "What are working hours?",
        "Is flexible timing allowed?",
        "What are core working hours?",
        "How is attendance tracked?",
        "What happens if I am late?",
        "Is overtime paid?",
        "Can I work beyond office hours?",
        "How do I log work hours?",
        "What is shift timing policy?",
        "Do we have time tracking tools?",

        # Code of Conduct
        "What is company code of conduct?",
        "What behavior is expected at workplace?",
        "Is discrimination allowed?",
        "What is harassment policy?",
        "How do I report harassment?",
        "What is dress code policy?",
        "Can I wear casual clothes?",
        "What is policy on alcohol at workplace?",
        "What are workplace ethics rules?",

        # Health & Safety
        "What are safety guidelines in office?",
        "How to report workplace accident?",
        "Do we have mental health support?",
        "What is employee assistance program?",
        "Are there wellness programs?",
        "What to do in emergency situation?",
        "Is fire drill mandatory?",

        # IT & Equipment Policy
        "What equipment will I get from company?",
        "Can I use office laptop for personal use?",
        "What is acceptable use policy?",
        "Can I install my own software?",
        "Is VPN mandatory?",
        "What is BYOD policy?",
        "How do I raise IT support ticket?",
        "What happens to laptop after resignation?",
        "How do I contact IT support?",

        # Payroll & Compensation
        "What is salary structure?",
        "When is salary credited?",
        "What deductions are there in salary?",
        "How is bonus calculated?",
        "What is PF contribution?",
        "How to report salary discrepancy?",
        "When do salary increments happen?",
        "What is gratuity policy?",
        "How is tax deducted from salary?",

        # Reimbursement
        "What expenses can I claim?",
        "How to submit reimbursement?",
        "What documents are required for claims?",
        "What is reimbursement timeline?",
        "Are meal expenses covered?",
        "Can I claim travel expenses?",
        "Is home office setup reimbursed?",
        "What receipts are needed for reimbursement?",

        # Travel Policy
        "What is travel policy for employees?",
        "Can I book business class flight?",
        "What is hotel allowance?",
        "How to book travel through company?",
        "Do we get travel advance?",
        "What is international travel policy?",
        "What expenses are covered in business trips?",

        # Remote & Hybrid Work
        "What is work from home policy?",
        "How many days remote work allowed?",
        "What are core hours in remote work?",
        "Can I work from another city?",
        "Is full remote allowed?",
        "What is home office allowance?",
        "What is expected response time on Slack?",
        "What is hybrid work model?",

        # Training & Development
        "What training programs are available?",
        "Do we get access to online courses?",
        "Is certification reimbursed?",
        "What is mentorship program?",
        "How can I grow in company?",
        "Are leadership programs available?",

        # Performance & Feedback
        "How performance review works?",
        "What is rating system?",
        "What are OKRs?",
        "How often reviews happen?",
        "What is 360 feedback?",
        "How promotions are decided?",
        "Can I appeal my rating?",

        # Company Events
        "What company events are conducted?",
        "What is annual retreat?",
        "Are hackathons organized?",
        "Do we get volunteering days?",
        "What is company day?",
        "Are town halls mandatory?",

        # Data Security & Privacy
        "How is employee data protected?",
        "What is password policy?",
        "Can I share company data on WhatsApp?",
        "What to do in case of data breach?",
        "How long is employee data stored?",
        "What is data classification policy?",

        # Exit Policy
        "What is notice period?",
        "How to resign from company?",
        "What is exit process?",
        "Do we get severance pay?",
        "What is final settlement process?",
        "Can I get reference letter?",
        "What happens to PF after exit?",

        # General / FAQ
        "How to claim insurance?",
        "Can I take salary advance?",
        "How internal transfer works?",
        "Is gym membership covered?",
        "What is relocation policy?",
        "Where can I find HR policies?",
        "How do I contact HR?",
        "What are general company policies?",
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
