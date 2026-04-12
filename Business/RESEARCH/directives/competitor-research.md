# Competitor Research — RESEARCH Directive

## Purpose

Standard operating procedure for systematic competitor identification, profiling, and structured comparison as part of a business thesis or standalone competitive analysis.

## Owner

RESEARCH

## Trigger

Use this skill when:
- Building Section 4 (Market and Competitors) of a business thesis
- A user requests a standalone competitive analysis
- Validating whether a business idea has viable market positioning

## Resources

| Resource | Path | Description |
|----------|------|-------------|
| Research Sources | `Business/RESEARCH/resources/research-sources.md` | Authoritative source directory |

---

## How It Works — Step by Step

### Step 1 — Exhaustive Competitor Discovery (Multi-Pass)

The goal is **zero blind spots**. The user must never google their idea and find a company we missed. Execute **all** passes below, in order. Each pass is designed to catch competitors that earlier passes miss.

---

#### Pass 1 — Seed List

1. **User-provided competitors** — start with any competitors the user named.
2. **Obvious category search** — search for the product category in plain language (e.g., "AI email assistant for HR").

#### Pass 2 — Keyword Permutation Matrix

The most common reason competitors are missed is that they describe the same product using different words.

**Build a keyword matrix** before searching:

| Dimension | Generate variants |
|-----------|-----------------|
| **Function verbs** | What the product does — list every synonym (e.g., "automate", "streamline", "manage", "optimise", "generate", "analyse") |
| **Object nouns** | What it acts on — list every synonym and related term (e.g., "emails", "messages", "correspondence", "communications", "outreach") |
| **Customer descriptors** | Who buys it — list every synonym (e.g., "HR teams", "people ops", "talent acquisition", "human resources", "recruiters") |
| **Product type labels** | How it's categorised — list every label (e.g., "tool", "platform", "assistant", "copilot", "agent", "software", "SaaS", "app", "solution") |
| **Technology descriptors** | How the tech is described — list every variant (e.g., "AI", "AI-powered", "GPT", "LLM", "machine learning", "intelligent", "smart", "automated") |

**Then execute searches** using combinations across dimensions:
- `[function verb] + [object noun] + [product type]` (e.g., "automate emails tool")
- `[technology descriptor] + [object noun] + [customer descriptor]` (e.g., "AI correspondence HR teams")
- `[function verb] + [object noun] + "for" + [customer descriptor]` (e.g., "manage communications for recruiters")
- Search at least **15 unique keyword combinations** drawn from the matrix.

**Search operators to use on each combination:**
- `"[phrase]"` — exact match
- `[phrase] + "alternative"` / `"alternatives to"` / `"competitor"` / `"vs"` / `"compared to"` / `"review"`
- `[phrase] + site:reddit.com`
- `[phrase] + site:producthunt.com`
- `[phrase] + site:g2.com`

#### Pass 3 — Aggregator and Directory Sweep

Search **every** relevant aggregator, not just the obvious ones:

| Aggregator type | Sources to check |
|-----------------|-----------------|
| **Software review sites** | G2, Capterra, TrustRadius, GetApp, Software Advice, SourceForge |
| **Product launch platforms** | Product Hunt (search + browse categories), BetaList, Launching Next |
| **Curated lists** | "Awesome" GitHub lists (search `awesome-[domain]`), AlternativeTo.net, There's An AI For That (theresanaiforthat.com), Future Tools (futuretools.io) |
| **Startup databases** | Crunchbase (search by category + keywords), AngelList/Wellfound, F6S, PitchBook (if accessible) |
| **Industry-specific directories** | Identify the domain-specific aggregator (e.g., MQL5 marketplace for trading, Atlassian Marketplace for project tools, Salesforce AppExchange for CRM tools) and search it |
| **AI-specific aggregators** | There's An AI For That, AI Tool Directory, TopAI.tools, AItoolsclub.com, Futurepedia |

#### Pass 4 — Community and Forum Deep Dive

Go beyond surface-level searches. **Enter and search within** communities:

1. **Reddit** — search the product category in:
   - r/SaaS, r/startups, r/Entrepreneur, r/smallbusiness
   - Domain-specific subreddits (identify and list them)
   - Search "what tool do you use for [function]" and "best [product type] for [customer]"
   - Search "I built a [product description]" to find indie makers building the same thing
2. **Hacker News** — search via hn.algolia.com for:
   - "Show HN" posts with related keywords
   - "Ask HN" posts where people discuss tools in the space
   - "Launch HN" posts (newer)
3. **Discord / Slack / Telegram** — identify and search public communities in the domain
4. **Twitter/X** — search for product category keywords, scan replies for tool recommendations
5. **YouTube** — search for "[category] tools 2025", "[category] tools 2026", "best [product type] for [customer]", comparison and review videos
6. **Quora** — search for questions about the problem the product solves
7. **Stack Overflow / domain forums** — if the product is developer-facing, search the relevant technical forums
8. **LinkedIn** — search posts and articles discussing tools in the space

#### Pass 5 — App Store and Marketplace Search

If the product operates in or near a platform ecosystem, search **all** relevant stores:

- VS Code Marketplace, JetBrains Marketplace (developer tools)
- Chrome Web Store, Firefox Add-ons (browser extensions)
- Shopify App Store (e-commerce)
- Salesforce AppExchange (CRM)
- Zapier / Make / n8n integration directories (automation)
- Slack App Directory, Microsoft Teams App Store (workplace tools)
- Apple App Store, Google Play Store (mobile apps)
- AWS Marketplace, Azure Marketplace, GCP Marketplace (cloud/enterprise)
- WordPress Plugin Directory (web/CMS)
- HubSpot App Marketplace (marketing/sales)
- Relevant MCP server registries (if MCP-based product)

#### Pass 6 — Stealth and Pre-Launch Detection

Catch competitors that haven't fully launched yet:

1. **Crunchbase funding search** — search for recent seed/pre-seed funding in the category. Companies that just raised money but haven't launched are future competitors.
2. **AngelList/Wellfound job postings** — search for startups hiring roles that imply they're building a competing product (e.g., hiring "AI email engineer" if the product is an AI email tool).
3. **Patent search** — search Google Patents and USPTO for recent patent applications using domain keywords. Companies filing patents are often building products.
4. **Academic / research projects** — search Google Scholar and arXiv for recent papers that describe systems matching the product concept. Researchers sometimes commercialise.
5. **Accelerator cohorts** — check recent cohorts at Y Combinator (ycombinator.com/companies), Techstars, 500 Global, and other accelerators for companies in the space.
6. **VC portfolio pages** — check portfolios of VCs known to invest in the domain (e.g., a16z, Sequoia AI portfolio, etc.).

#### Pass 7 — Adjacent Market and Platform Encroachment Check

The most dangerous competitors are often **not** startups — they're features inside larger platforms:

1. **Big tech / incumbent feature check** — has Google, Microsoft, Salesforce, HubSpot, or any dominant platform in the domain announced, beta-tested, or shipped a feature that does what this product does? Search for "[platform name] + [product function] feature" and "[platform name] AI [function]".
2. **Adjacent market movers** — identify companies in neighbouring verticals that could trivially add this functionality. If the product is "AI email drafting for HR", check whether existing HR platforms (Workday, BambooHR, Rippling) or email platforms (Superhuman, Front, Missive) already offer or are building similar features.
3. **Open-source alternatives** — search GitHub for repositories matching the product function. Use keyword searches, topic tags, and "awesome" lists. A well-maintained open-source project is a competitor even without a company behind it.
4. **No-code / low-code workarounds** — can a non-technical user replicate the core value using Zapier + GPT, Make + Claude, or similar toolchains? If yes, this is a competitor.

#### Pass 8 — International Competitor Scan

Don't limit discovery to English-language markets:

1. **Non-English search** — repeat the core keyword searches in the primary non-English languages of the target market (e.g., German, French, Japanese, Mandarin, Spanish, Portuguese).
2. **Regional platforms** — check region-specific platforms (e.g., MindMeister for DACH, JiGuang for China, Naver for Korea).
3. **Localized aggregators** — check local startup databases (e.g., Dealroom.co for Europe, Tracxn for India, 36kr for China).

#### Pass 9 — De-duplication and Completeness Audit

1. **De-duplicate** — merge any entries that refer to the same company under different names or URLs.
2. **Cross-reference check** — for every Tier 1 competitor identified so far, visit their website and check their "Alternatives" or "Compare" pages — these often name competitors you haven't found yet.
3. **AlternativeTo.net validation** — search AlternativeTo for each Tier 1 competitor. The listed alternatives are potential competitors you may have missed.
4. **"People also search for" mining** — when searching for each identified competitor by name, note Google's "People also search for" and "Related searches" suggestions.
5. **Final gap check** — ask: "If someone googled this exact idea right now, what would they find?" Execute that literal search and verify every result on page 1–3 is already in the competitor list.

---

**Output**: A comprehensive long list of all identified competitors (aim for 15–50+ entries before filtering), with:
- Company/project name
- URL
- One-line description
- Discovery source (which pass found them)
- Initial tier guess (Tier 1 / 2 / 3)

### Step 2 — Tier Classification

Classify every identified competitor into:

| Tier | Definition | Research depth |
|------|-----------|----------------|
| **Tier 1 — Direct** | Same core value proposition, same target customer segment | Full profile (Step 3) |
| **Tier 2 — Adjacent** | Overlapping feature set, but broader positioning or different primary segment | Summary profile (Step 4) |
| **Tier 3 — Peripheral** | Tangentially related, but different enough that direct comparison is misleading | Name and one-sentence note only |
| **Status Quo** | The dominant alternative is doing nothing / doing it manually | Always include in analysis |

### Step 3 — Tier 1 Full Profiling

For each Tier 1 competitor, scrape their website and research the following:

**Company Information**:
- Full legal name and any trading names
- Jurisdiction of registration (check company registers where possible)
- Registration number if available
- Year founded / launched
- Team size (LinkedIn, about page)
- Funding history (Crunchbase, press releases)

**Product Information** (scrape the website):
- Product description (in their own words — quote directly)
- Delivery model (cloud, desktop, hybrid, API, plugin)
- Platform support (which integrations, which platforms)
- Execution model (relevant technical details)
- Key features list

**Commercial Information**:
- Pricing (exact figures — scrape pricing page)
- Pricing model (subscription, per-seat, usage-based, one-time licence)
- Free tier or trial availability
- Published user/customer count
- Any verifiable traction metrics (trades copied, projects completed, etc.)

**Go-to-Market**:
- Sales model (self-serve, sales-led, hybrid)
- Community presence (Discord, Slack, Telegram, forum)
- Content strategy (blog, YouTube, social)
- Trustpilot / G2 / review presence and rating

**For AI wrapper competitors, additionally research**:
- Which model(s) / API(s) they use
- Whether they expose model selection to the user
- Whether they have proprietary fine-tuning or only prompt engineering
- What happens to user data (privacy policy check)

### Step 4 — Tier 2 Summary Profiling

For each Tier 2 competitor, collect a reduced profile:
- Company name, URL, one-paragraph description
- Primary positioning (how they frame their product)
- Pricing range
- Any notable traction metrics
- Why they are Tier 2 and not Tier 1 (what makes them adjacent rather than direct)

### Step 5 — Basis of Competition Analysis

Identify the 4–6 dimensions on which competition actually operates. Common dimensions:

| Dimension | Description |
|-----------|-------------|
| Framing and positioning | How the product is marketed (insurance vs. tool vs. platform) |
| Price and pricing model | Entry cost, recurring cost, pricing structure |
| Platform breadth | Number of integrations, supported platforms |
| Ease of access | Onboarding friction (free trial vs. sales call vs. licence purchase) |
| Reputation and social proof | Verified users, reviews, community size |
| Feature depth | Analytics, reporting, automation sophistication |
| Data and network effects | Whether the product improves with more users |

Map each competitor's position on each identified dimension.

### Step 6 — Structured Comparison Table

Build a comprehensive comparison table. **Every cell must be factual and sourced**. If a data point cannot be verified, write "Undisclosed" or "Not published."

Standard columns: Subject Company, then each Tier 1 competitor, then each notable Tier 2 competitor.

Standard rows (adapt to the domain):
- Primary framing
- Delivery model
- Platforms supported
- Execution model
- Key differentiating feature
- Entry pricing
- Free tier
- User base / traction
- Team size
- Funding
- Community
- Analytics / reporting

### Step 7 — Differentiation Assessment

For each claimed differentiator of the subject company:

| Differentiator | Is it real? | Is it defensible? | For how long? |
|----------------|-------------|-------------------|---------------|
| ... | Evidence-based assessment | Moat analysis | Time horizon |

### Step 8 — Barrier and Response Analysis

**Barriers the subject company faces as a new entrant**:
- Trust (no track record)
- Platform coverage (limited at launch)
- Distribution (search authority, content library, affiliate network)
- Incumbency advantage (existing user bases, data, brand)

**Likely competitive responses** (probability-weighted):
- Non-response (most probable at zero scale)
- Messaging adaptation (update website copy to match positioning)
- Price retaliation (if market is price-sensitive)
- Feature imitation (straightforward for software)
- Acquisition (unlikely unless significant traction)

### Step 9 — Customer Perception

Research how actual customers discuss existing tools:

**Sources to check**:
- Reddit: search for product names, category terms
- Discord/Telegram: join or search public servers in the domain
- YouTube: search for reviews, comparisons, tutorials
- Trustpilot/G2/Capterra: check review pages for each competitor
- MQL5/domain-specific forums: search for tool discussions
- Twitter/X: search for product mentions

**Key questions to answer**:
- What do customers praise most?
- What do they complain about most?
- What is the switching frequency (do they try multiple tools)?
- What is the default alternative (doing nothing)?
- What would it take for a new entrant to win their adoption?

---

## Anti-Patterns

| Don't | Why | Instead |
|-------|-----|---------|
| List competitors without profiling them | A name without data is useless | Scrape every competitor's website for actual data |
| Claim "no competitors exist" | There are always competitors, even if indirect | The status quo (doing nothing) is always a competitor |
| Use competitor marketing claims as facts | Companies exaggerate | Verify with third-party sources where possible |
| Ignore pricing details | Pricing is the most investor-relevant competitive dimension | Scrape exact pricing from every competitor |
| Skip community and sentiment research | Customer perception drives adoption more than features | Check forums, reviews, and social channels |
