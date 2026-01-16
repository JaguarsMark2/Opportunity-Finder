# Ideabrowser Methodology Analysis

## Overview
Analysis of Ideabrowser's scoring and evaluation framework to inform Opportunity Finder's implementation.

## Data Collection Date
12 January 2026

## Analysis Sources
- Idea of the Day page
- Multiple specific idea detail pages
- Value framework pages
- Value matrix pages
- Idea database listing

**Note:** Many detailed methodology pages are behind paywall (Members Only). Analysis below is based on publicly accessible content.

---

## SCORING FRAMEWORK DISCOVERED

### Four-Factor Quantitative Scoring (Opportunity Assessment)

| Factor | Scale | Displayed as | Purpose |
|---------|-------|-------------|---------|
| **Opportunity** | 1-10 | Overall opportunity quality (Exceptional to Poor) |
| **Problem** | 1-10 | Pain point severity (High Pain to Low Pain) |
| **Feasibility** | 1-10 | Execution difficulty (Manageable to Very Hard) |
| **Why Now** | 1-10 | Timing/urgency (Great Timing to Poor Timing) |

**Visual Display:**
- Score badges with emoji indicators (🌍 Massive Market, ⏰ Perfect Timing, ⚡ Unfair Advantage)
- Numeric scores displayed prominently
- Color/text descriptions (e.g., "Manageable 5/10")

### Qualitative Context Frameworks

**1. Value Equation**
- Analyzes: Audience, Community, Product, Continuity
- Positions opportunity on value axis

**2. Value Matrix**
- Analyzes: Uniqueness vs Value
- Categories: Category King, High Impact, Low Impact, Commodity Play

**3. A.C.P. Framework**
- Analyzes: Audience, Community, Product scores
- Each scored 1-10

**4. Business Fit**
- Analyzes: Market potential, execution difficulty, go-to-market feasibility
- Displays: Revenue potential ($$), Execution Difficulty, Go-To-Market score

---

## PROOF & SIGNALS COLLECTION

### Community Signals (Multi-Platform Engagement)

| Platform | What Tracked | Scored |
|----------|--------------|--------|
| **Reddit** | Engagement across subreddits | 8/10 |
| **Facebook** | Group discussions, member counts | 7/10 |
| **YouTube** | Views, engagement | 7/10 |
| **Other** | Custom community segments | 8/10 |

**Metrics:**
- Total member counts (e.g., "6 subreddits · 2.5M+ members")
- Engagement scores
- Prioritization of communities

### Proof Elements

For each idea, Ideabrowser collects:
- **Market Data:** Size estimates (TAM/SAM/SOM), growth projections
- **Competitor Examples:** Direct links to existing solutions
- **Revenue Evidence:** MRR/ARR data from listings
- **Community Signals:** Actual engagement across platforms
- **Trend Analysis:** Growth indicators (+303% Growth, Low Competition keywords)

---

## CONTEXTUAL ANALYSIS SECTIONS

### Why Now? (Timing Analysis)
- Market growth projections
- Industry trends
- Regulatory or technology shifts
- "Perfect timing" vs "poor timing" assessment

### Market Gap Analysis
- What existing solutions are missing
- Unaddressed customer needs
- Differentiation opportunities
- "Market gap matters because it presents opportunity to capture significant portion of market"

### Execution Plan
- Step-by-step approach to launch
- MVP definition
- Integration strategy
- Growth roadmap
- Marketing channels

### Founder Fit (Optional)
- Skills/experience alignment
- Resource requirements
- Personal interest factors
- **Note:** Mark does not want this feature for Opportunity Finder

---

## BUSINESS FIT METRICS

### Revenue Potential
- Estimates in ranges (e.g., "$10M-$100M ARR potential")
- Based on market size analysis
- Competitive revenue extrapolation

### Execution Difficulty
- Categorical assessment (Low/Moderate/High)
- Based on complexity of building and launching
- Factors: Tech stack required, integrations needed, regulatory hurdles

### Go-To-Market Feasibility
- Score 1-10
- Based on: Market access, competition level, customer acquisition difficulty
- Example: "9/10 Exceptional market potential with viral traction"

---

## IDEA STRUCTURE PATTERN

Each idea page contains:

1. **Hook** - Emotional opening paragraph describing the problem
2. **Business Fit Metrics** - Three key metrics displayed prominently
3. **Solution Description** - What the product does
4. **Pricing Model** - How product monetizes
5. **Target Market** - Who pays (B2B vs B2C)
6. **Execution Plan** - Step-by-step launch strategy
7. **Market Positioning** - How to differentiate
8. **Growth Path** - From initial wedge to long-term vision
9. **Proof & Signals** - Data backing opportunity claims
10. **Frameworks Applied** - Which validation frameworks support this

---

## KEY METHODOLOGY INSIGHTS

### Layered Evaluation Approach
Ideabrowser uses **multi-layered evaluation**, not just single score:
1. Quantitative scores (0-100 equivalent)
2. Qualitative frameworks for context
3. Market analysis for timing
4. Growth strategy for path forward

### Evidence-Based Validation
- Not just claims - every assertion backed by:
  - Community engagement data
  - Revenue examples
  - Competitor links
  - Market trend analysis

### Narrative Structure
- Each idea tells a **story** from problem to solution
- Emotional hooks + data backing + execution plan
- Makes ideas actionable and memorable

### Keyword Volume Analysis
- Each idea page shows:
  - "Volume" metrics (e.g., "2.9K", "4.4K")
  - "Growth" indicators (e.g., "+303%")
  - "Competition" level (LOW/MEDIUM/HIGH)
- Based on search term analysis

---

## IMPLEMENTATION NOTES FOR OPPORTUNITY FINDER

### What to Implement

**From Ideabrowser methodology, Opportunity Finder should include:**

| Feature | Implementation Priority |
|---------|----------------------|
| **Four-Factor Scoring** (Opportunity/Problem/Feasibility/Why Now) | Phase 1 |
| **Community Signals Collection** (Reddit/FB/YouTube) | Phase 1 |
| **Timing/Trend Analysis** (Market growth rates) | Phase 1 |
| **Market Gap Documentation** (What's missing?) | Phase 1 |
| **Keyword Volume Metrics** (Volume, Growth, Competition) | Phase 1 |
| **Competitor Examples** (Direct links) | Phase 1 |
| **Revenue Evidence** (MRR/ARR from sources) | Phase 1 |

### What to Skip

| Feature | Reason |
|---------|---------|
| **Founder Fit Analysis** | Mark does not want this feature |
| **Detailed Execution Plans** | Too manual for MVP - product owner determines |
| **Value Framework Displays** (Matrix/Equation/ACP) | Can be Phase 2 - nice-to-have |

### Key Differences from Current PRD

| Current PRD | Ideabrowser Approach | Recommendation |
|-------------|-------------------|--------|
| Score 0-100 based on 4 weights (demand, revenue, competition, complexity) | 4-factor qualitative assessment (Opportunity, Problem, Feasibility, Why Now) | **Hybrid approach recommended** |
| Validation separate from scoring | Validation integrated into overall assessment | **Keep validation as separate gate as in PRD** |
| Keyword-based clustering not defined | Keyword volume analysis prominent | **Add keyword volume metrics to data collection** |
| Timing mentioned but not detailed | Dedicated "Why Now" analysis | **Formalize timing analysis in PRD** |
| Revenue proof mentioned | Market size + revenue potential | **Expand revenue analysis beyond individual competitor MRR** |

---

## LIMITATIONS & ASSUMPTIONS

### Access Limitations
- Ideabrowser's detailed scoring algorithms and validation logic are behind paywall
- Cannot access: exact weighting formulas, automatic scoring logic, specific validation thresholds
- Analysis based on publicly visible structure and patterns

### Assumptions Made
- Four-factor scoring uses similar weighting principles to PRD's 4-factor approach
- Community signals collected via APIs or public engagement metrics
- Market timing derived from trend analysis and growth data
- Execution plans generated or manually curated based on opportunity type

---

## RECOMMENDED NEXT STEPS

1. **Update PRD Section 4** to include:
   - Four-factor scoring methodology (Opportunity, Problem, Feasibility, Why Now)
   - Timing/Trend analysis section
   - Market gap analysis framework
   - Keyword volume metrics

2. **Define Clustering Algorithm** to convert pain points to opportunities:
   - Based on Ideabrowser's keyword-based approach
   - Consider NLP/ML clustering for Phase 2

3. **Implement Community Signals Collector**:
   - Reddit engagement metrics
   - YouTube views/engagement
   - Facebook group discussions
   - Aggregate into community signals score

4. **Formalize "Why Now" Analysis**:
   - Market growth rate calculation
   - Industry trend indicators
   - Timing score 1-10

5. **Add Market Gap Analysis**:
   - Competitor feature gap identification
   - Unmet customer needs documentation
   - Differentiation opportunity scoring

