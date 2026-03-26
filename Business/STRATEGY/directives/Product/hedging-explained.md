# Hedge Edge — Ultimate Prop Firm Hedging Guide

> Important: Hedge Edge is a software tool for traders. It is not a prop firm, broker, investment manager, or financial adviser.
> Important: Hedge Edge is not affiliated with, endorsed by, or sponsored by any prop firm.
> Important: Traders must check each prop firm's rules before hedging. Hedging may be legal in general and still be restricted by a firm's contract.

This document is the single-source reference for how Hedge Edge thinks about prop firm hedging: the operating logic, the economics, the hedge-type taxonomy, the challenge-selection framework, and the guardrails.

## 1. Core Thesis

Most traders approach prop firms as a directional trading problem.

Hedge Edge reframes it as a controlled payoff-engine problem.

The prop account and the hedge account are doing different jobs:

- The prop side is trying to unlock payout rights.
- The hedge side is absorbing or transforming the loss path.
- The real question is not "can I predict the market?"
- The real question is "what payoff structure am I building, and is that payoff worth the cost and capital required?"

That is the entire game.

## 2. What Hedge Edge Is And Is Not

### What it is

- A desktop trade-management application.
- A hedge automation layer between prop accounts and personal broker accounts.
- A way to reduce execution error when mirroring trades across accounts.
- A framework for evaluating challenge economics before you buy.

### What it is not

- Not financial advice.
- Not a promise of profits.
- Not a guarantee that a live challenge will succeed.
- Not permission to ignore firm rules.
- Not a replacement for broker margin discipline, spread control, or execution monitoring.

## 3. The Basic Hedge Mechanic

The simplest version looks like this:

1. You buy on the prop account.
2. Hedge Edge sells the same instrument on the hedge side.
3. If the prop trade wins, the hedge loses.
4. If the prop trade loses, the hedge wins.

You are not eliminating cost. You are relocating risk.

That matters because the prop account offers asymmetric upside:

- On failure, the fee is usually lost.
- On success, you unlock a funded account and future payout rights.

Hedging converts uncontrolled failure into a measurable payoff structure.

## 4. Why The EV Formula Changes By Hedge Type

This is the improvement that matters.

There is no single universal EV formula for "prop firm hedging". The EV formula depends on what happens after the challenge phase.

Three layers determine the formula:

1. What account is hedging the challenge.
2. Whether the hedge stops once funded or continues at funded.
3. Whether the funded hedge is only for recovery, or for recovery plus surplus profit.

So the correct statement is:

$$
	ext{EV} = \text{value created by the hedge structure} - \text{all costs of that structure}
$$

The expression on the left stays the same. The meaning of the value term changes by hedge type.

## 5. The Main Hedge Types

There are four core hedge types worth separating.

### Type A. Challenge-Only Insurance Hedge

This is the base model already implemented in the challenge notebook.

**Interactive model:** [`type_a_challenge_insurance.ipynb`](../PropFirmData/type_a_challenge_insurance.ipynb)

Structure:

- You buy a challenge.
- You hedge the challenge while trying to pass it.
- When funded, you stop thinking about the hedge as an active recovery engine.
- Your economic prize is the funded payout itself.

This is the cleanest formula for classic deterministic challenge modelling.

#### EV formula

$$
	ext{funded payout} = \text{account size} \times \text{funded target \%} \times \text{profit split \%}
$$

$$
	ext{EV}_{A} = \text{funded payout} - (\text{challenge fee} + \text{challenge hedge losses})
$$

#### What this means in plain English

You are asking:

"If I insure my way through the challenge, is the first funded payout large enough to cover what I spent getting there?"

#### Example

Take a $100k challenge:

- Fee = $500
- Total hedge losses across phases = $800
- Total cost to get funded = $1,300
- Funded target = 8%
- Profit split = 80%

Then:

$$
	ext{funded payout} = 100{,}000 \times 8\% \times 80\% = 6{,}400
$$

$$
	ext{EV}_{A} = 6{,}400 - 1{,}300 = 5{,}100
$$

This is the formula the current challenge model primarily uses.

### Type B. Funded-Continuation Recovery Hedge

This is what you mean by continuing to hedge at funded with the challenge losses and challenge costs included.

**Interactive model:** [`type_b_funded_recovery.ipynb`](../PropFirmData/type_b_funded_recovery.ipynb)

Structure:

- You hedge through the challenge.
- You get funded.
- You keep hedging after funding.
- The funded hedge is now sized so that if the funded account eventually fails, the hedge side recovers the full historical cost stack.

That cost stack now includes:

- challenge fee
- challenge hedge losses
- any funded-stage hedge losses already accumulated

This is no longer just a "first payout covers entry cost" model. It becomes a running recovery model.

#### EV logic

The value is not just one funded payout. The value is the expected funded cash extracted before the funded account dies, minus the full hedge stack required to defend that path.

One useful way to write it is:

$$
	ext{EV}_{B} = \text{net funded cashflows before failure} + \text{recovery value at failure} - \text{all hedge costs}
$$

If the hedge at failure is sized to fully recover the stack, then recovery value is approximately the accumulated insured base.

A simplified trader version is:

$$
	ext{EV}_{B} = \text{funded withdrawals} - \text{net funded hedge drag}
$$

because the challenge cost stack is intended to be recoverable if the funded account is eventually lost.

#### What this means in plain English

You are asking:

"If I keep hedging the funded account, can I treat challenge costs as recoverable capital instead of sunk capital?"

#### Example

Suppose:

- Challenge fee = $500
- Challenge hedge losses = $800
- So insured stack when funded starts = $1,300
- At funded, you keep hedging with the hedge sized to recover that $1,300 if the funded account fails
- Over time, you withdraw $3,000 from the funded account
- While doing so, the funded hedge loses $700
- Then the funded account eventually hits its loss boundary and the hedge wins back the insured $2,000 stack that has built up

Then economically:

- You kept $3,000 in funded withdrawals
- You paid $700 of funded hedge drag while the funded account survived
- The failure event did not wipe out the historical stack because the hedge was carrying it

So the simplified result is closer to:

$$
	ext{EV}_{B} \approx 3{,}000 - 700 = 2{,}300
$$

The important conceptual shift is this: in Type B, challenge costs are no longer treated as dead forever. They are part of the insured base.

### Type C. Funded-Continuation Surplus Hedge

This is your variant where you keep hedging at funded, but you deliberately oversize the hedge so that a losing challenge or a funded-account failure does not just recover costs, it also leaves surplus profit.

**Interactive model:** [`type_c_funded_surplus.ipynb`](../PropFirmData/type_c_funded_surplus.ipynb)

Structure:

- Hedge through challenge.
- Continue hedging at funded.
- Size the hedge not to recover exactly $L$, but to recover $L + P$.
- Here $P$ is desired surplus profit.

#### Hedge sizing logic

Base recovery sizing is:

$$
S = \frac{L}{DD}
$$

Surplus sizing becomes:

$$
S = \frac{L + P}{DD}
$$

Where:

- $L$ = historical insured stack
- $P$ = desired surplus on failure

#### EV logic

Now the failure state itself has positive value.

One way to write it is:

$$
	ext{EV}_{C} = \text{funded withdrawals while alive} + \text{surplus on failure} - \text{all hedge drag and friction}
$$

#### What this means in plain English

You are asking:

"Can I build the hedge so that even when the prop side loses, that loss event becomes a monetisable outcome rather than just a recovery event?"

#### Example

Suppose at funded your insured stack is $1,500, but you want a further $500 profit if the funded account dies.

Then you size for:

$$
L + P = 1{,}500 + 500 = 2{,}000
$$

If funded trading produces:

- funded withdrawals of $2,200 before failure
- hedge drag of $900 while the funded account survives
- then a failure event that pays the hedge $2,000

of which:

- $1,500 replaces the historical stack
- $500 is true surplus

then the simplified economic view is:

$$
	ext{EV}_{C} \approx 2{,}200 + 500 - 900 = 1{,}800
$$

This method is more aggressive than Type B.

The benefit:

- You can make the loss event itself profitable.

The cost:

- Bigger hedge size
- Bigger drag during favourable prop performance
- Bigger capital requirement
- More operational fragility

### Type D. Funded-vs-Funded Cross Hedge

This is the type where two funded accounts hedge each other.

Structure:

- Instead of hedging a prop account against a personal broker, you hedge one funded prop account against another funded prop account.
- One account is long, the other short.
- You are now using one funded account as the hedge engine for the other.

This is fundamentally different from challenge insurance.

Why:

- Both sides can generate payout rights.
- Both sides have prop rules.
- Both sides have drawdown rules.
- The loss on one side may be acceptable if it helps preserve or monetise the other side.

#### EV logic

Now your value term is the net extraction from both funded accounts, not just one.

$$
	ext{EV}_{D} = \text{withdrawals from funded account 1} + \text{withdrawals from funded account 2} - \text{combined drag, resets, and losses}
$$

If one account is intentionally sacrificed as the hedge leg, then a more practical simplification is:

$$
	ext{EV}_{D} = \text{cash extracted from winner} - \text{value destroyed on loser} - \text{friction}
$$

#### What this means in plain English

You are asking:

"Can I use one funded account as the insurance or monetisation engine for another funded account, instead of using a personal broker as the hedge side?"

#### Example

Suppose you have two funded $100k accounts.

- Account A trends into profit and you withdraw $4,000
- Account B is the opposite-side hedge and eventually fails, destroying $1,200 of remaining embedded value
- Combined friction and execution drag across the life of the pair = $500

Then a simple view is:

$$
	ext{EV}_{D} = 4{,}000 - 1{,}200 - 500 = 2{,}300
$$

This is not the same as the challenge model. It is a portfolio-structure problem.

## 6. The Key Difference Between The Hedge Types

The easiest summary is:

- Type A asks: can the first funded payout justify the challenge cost?
- Type B asks: can funded hedging convert old costs from sunk to recoverable?
- Type C asks: can failure itself become a profit event?
- Type D asks: can one funded prop account hedge another and still leave net extractable value?

That is what you mean when you say expected value varies by hedge type.

## 7. The Cost Stack

The mistake most traders make is thinking the cost is just the challenge fee.

The real cost stack can include:

1. Challenge fee
2. Challenge hedge losses while moving toward the target
3. Spread and friction on both sides
4. Margin and safety buffer on the hedge side
5. Funded-stage hedge drag
6. Re-hedging or resizing cost
7. Opportunity cost of using another funded account as the hedge leg

Different hedge types include different parts of this stack.

## 8. Phase-Based Hedge Sizing For Challenge Hedges

In the deterministic challenge model, the hedge is sized against the current insured base.

The insured base starts as the challenge fee and grows as hedge losses accumulate.

### State variable

$$
L_1 = F
$$

Where:

- $L_1$ is the insured base entering phase 1
- $F$ is the challenge fee

### Hedge size per phase

$$
S_n = \frac{L_n}{DD}
$$

Where:

- $S_n$ is hedge size in phase $n$
- $L_n$ is current insured base
- $DD$ is the maximum drawdown allowance as a decimal

### Cost growth if the phase is passed

$$
L_{n+1} = L_n + \text{hedge loss}_n
$$

This is why multi-step challenges can still be profitable, but they must earn their keep. Every extra phase grows the cost stack.

## 9. Static Vs Trailing Drawdown

This is one of the most important distinctions in the entire business.

### Static drawdown

Static means the floor does not trail the balance upward.

In the current model taxonomy, these are treated as static:

- Balance Based
- Balance/Equity - Highest at EOD
- Equity Based
- Blank or unknown drawdown field

Why static is attractive:

- Hedge sizing is simpler.
- Costs grow more slowly.
- The drawdown floor does not keep chasing the account upward.
- Tight budgets survive static structures far more often than trailing ones.

Static phase cost is approximated as:

$$
	ext{phase cost} = \left(\frac{L}{DD}\right) \times \text{target} + \text{spread}
$$

#### Static example

Say:

- Fee stack entering phase = $500
- Drawdown = 10%
- Phase target = 8%

Then hedge size is:

$$
S = \frac{500}{10\%} = 5{,}000
$$

If the phase is passed, the hedge loses roughly:

$$
5{,}000 \times 8\% = 400
$$

plus spread.

So your stack rises from about $500 to about $900 plus friction.

Simple. Linear. Predictable.

### Trailing drawdown

Trailing means the allowed floor follows the account upward.

In the current model taxonomy, explicit trailing language is treated as trailing, especially:

- Trailing Highest Balance/Equity

Why trailing is dangerous:

- Hedge losses become sunk cost.
- The amount at risk grows.
- The room does not widen enough to offset that growth.
- Hedge size has to be resized upward.
- Costs compound.

Core trailing rule:

$$
	ext{hedge size} = \frac{\text{total at risk}}{DD\%}
$$

Conceptually, each resize step behaves like:

$$
L \leftarrow L \times \left(1 + \frac{\delta}{DD}\right)
$$

#### Trailing example

Say:

- Initial insured stack = $500
- Drawdown = 5%
- The account rises in increments while the trailing floor follows upward

Initial hedge size:

$$
S = \frac{500}{5\%} = 10{,}000
$$

If the prop side rises 2%, the hedge may lose about $200.

Now the total at risk is no longer $500. It is about $700.

So the new hedge size becomes:

$$
S_{new} = \frac{700}{5\%} = 14{,}000
$$

That is the trap. The hedge must grow just because the prop side did well.

### Why static vs trailing matters by hedge type

- For Type A, trailing can destroy EV quickly.
- For Type B and C, trailing can make funded continuation expensive enough to kill the strategy.
- For Type D, if both funded accounts have strict trailing rules, the pair can become operationally unstable.

## 10. Capital Required

Profitability is not enough. You must be able to carry the hedge.

For the current challenge model:

$$
	ext{Capital} = \text{Margin} + \text{Buffer}
$$

with:

$$
	ext{Margin} = \frac{S_n}{\text{leverage}}
$$

and:

$$
	ext{Buffer} = S_n \times DD \times 1.5
$$

Important implication:

- Capital requirement scales with hedge size.
- Hedge size scales with insured base.
- Insured base grows with fee plus accumulated hedge losses.
- So a cheap challenge can still be capital-heavy if its drawdown structure is hostile.
- Type C and Type D usually need more capital than Type A.

## 11. What Makes A Great Challenge To Hedge

The best hedgeable challenges usually have most of these traits:

- Static drawdown
- Fewer phases
- Lower fee
- Higher profit split
- Reasonable profit target
- Clean rules and no vague anti-hedging language
- Manageable capital requirement on the hedge side
- Low break-even percentage once funded

In practice, the strongest setups are usually not the cheapest and not the biggest. They are the ones where payout, friction, and capital required are balanced well.

## 12. What Makes A Bad Challenge To Hedge

Red flags:

- Explicit trailing drawdown
- Too many phases
- Tiny drawdown allowance with a high target
- Weak payout split
- Expensive fee relative to size
- Rules that ban hedging, mirrored trading, copy trading, or "off-the-shelf" automation
- Ambiguous rulebook language you cannot verify
- Margin requirement that is too large for your real bankroll

If the challenge looks good only when you ignore capital requirements, it is not actually good.

## 13. The Three Budget Questions

When someone says, "I have a $500 budget," that can mean three different things.

### 1. Fee budget

You only mean the upfront challenge purchase price.

This is the loosest interpretation and the most misleading one.

### 2. Total cost budget

You mean fee plus modeled hedge losses.

This is more realistic, but still ignores that your hedge side must carry margin and buffer while trades are live.

### 3. Real bankroll budget

You mean the maximum total money you can safely deploy.

This is the correct interpretation for most traders.

If your full bankroll is capped, you should care about:

- challenge fee
- modeled total cost
- capital required
- and ideally the combined stress of total cost plus capital buffer

## 14. Current Best Budget Logic From The Latest Model Snapshot

Based on the latest v3 compounding-hedge output in the PropFirmData folder, the practical recommendations are:

### If $500 means your true bankroll

Best fit:

- Blueberry Funded
- $25,000 account
- 1 step
- Drawdown classification: static
- Fee: $42.50
- Total modeled cost: $128.14
- Capital required: $74.38
- EV: $1,471.86
- Break-even percentage: 0.64%

Why it wins:

- It fits inside a strict budget easily.
- It has exceptional capital efficiency.
- It is simple to carry operationally.
- No trailing-style compounding problem under this budget cap.

### If $500 means fee only

Best premium option:

- FundingPips
- $100,000 account
- 1 step
- Drawdown classification: static
- Fee: $499.00
- Total modeled cost: $1,303.39
- Capital required: $848.30
- EV: $6,296.61
- Break-even percentage: 1.37%

Why it wins:

- Highest upside among the fee-capped premium options.
- One-step structure helps.
- Strong profit split drives funded payout.

Why it does not fit a true $500 bankroll:

- The fee alone nearly consumes the budget.
- The hedge still needs meaningful capital behind it.

## 15. Challenge Selection Framework

When comparing two challenges, use this order:

1. Eliminate rulebook conflicts first.
2. Prefer static over trailing.
3. Prefer fewer phases.
4. Decide which hedge type you are actually building.
5. Check break-even percentage.
6. Check capital required.
7. Check EV.
8. Check cost efficiency and capital efficiency.

This ordering matters.

A high-EV challenge that breaks the bankroll is worse than a lower-EV challenge you can actually execute.

## 16. Operating SOP For Traders

### Before buying a challenge

- Confirm hedging is not contractually prohibited.
- Confirm whether drawdown is static or explicitly trailing.
- Check the number of phases.
- Check the profit split.
- Check the real fee actually charged.
- Decide whether you are building Type A, B, C, or D.
- Estimate spread friction on the instruments you will trade.
- Verify your broker leverage and usable margin.
- Make sure the hedge side can absorb the structure you chose.

### Before going live

- Test on small size first.
- Confirm opposite-side execution is working correctly.
- Confirm symbol mapping and lot sizing are correct.
- Confirm both terminals remain connected.
- Confirm your broker spreads are acceptable during the hours you trade.

### During operation

- Monitor execution delays.
- Monitor margin usage.
- Avoid news spikes if spreads widen beyond plan.
- Recheck hedge size if the structure requires resizing.
- Keep a log of fee, hedge losses, spreads, and live capital usage.
- Recalculate the insured stack if you are running Type B or C.

### After passing

- Do not confuse funded status with immediate realised profit.
- Decide whether you are stopping at Type A or transitioning into Type B or C.
- Compare funded payout needed versus break-even payout.
- Decide whether the funded account economics are still attractive after split, rules, and payout timing.

## 17. Language Discipline And Compliance

Hedge Edge should always be described as a trade-management and risk-reduction tool.

Safe positioning:

- "Designed to help protect your capital"
- "Trade-management software"
- "Risk-managed hedging workflow"
- "Software that automates reverse-copy hedging between accounts"

Language to avoid:

- "Guaranteed profits"
- "Risk-free"
- "No-loss trading"
- "Make money for sure"
- "Financial advice"

Required mindset:

- We can model deterministic economics.
- We cannot market guaranteed trading outcomes.
- We can explain payoff structures and risk transfer.
- We cannot claim live outcomes are certain.

## 18. The Correct Mental Model

The cleanest way to think about prop firm hedging is this:

- You are buying the right to attempt a payout stream.
- The challenge fee is the seed cost.
- The hedge is the payoff-engine.
- The drawdown model changes the hedge cost curve.
- The prop rules are the legal and contractual boundary.
- The hedge type determines the correct EV formula.
- The only good structure is one that works across all six.

## 19. Quick Rules Of Thumb

- Static beats trailing for most traders.
- One-step beats multi-step when all else is equal.
- Low break-even percentage is a major edge.
- High EV is meaningless if capital required is too high.
- Fee is only the beginning of cost.
- Type A is the cleanest and easiest to model.
- Type B turns sunk costs into recoverable costs.
- Type C can monetise the failure event, but requires more size and discipline.
- Type D is not a simple challenge hedge, it is a funded-account portfolio strategy.
- A challenge that fits your bankroll cleanly is better than a larger challenge that forces fragility.
- Always read the rulebook before trusting the spreadsheet.

## 20. Internal References

- Strategy directive: `Business/STRATEGY/directives/Business/prop-firm-hedge-arbitrage.md`
- Model engine: `Business/STRATEGY/executions/hedge_arbitrage_model.py`
- Scraper: `Business/STRATEGY/executions/propmatch_scraper.py`
- Data outputs: `Business/STRATEGY/resources/PropFirmData/`
- Original notebook (all models): `Business/STRATEGY/resources/PropFirmData/hedge_arbitrage_model.ipynb`
- Type A notebook (challenge-only insurance): `Business/STRATEGY/resources/PropFirmData/type_a_challenge_insurance.ipynb`
- Type B notebook (funded-continuation recovery): `Business/STRATEGY/resources/PropFirmData/type_b_funded_recovery.ipynb`
- Type C notebook (funded-continuation surplus): `Business/STRATEGY/resources/PropFirmData/type_c_funded_surplus.ipynb`

## 21. Final Standard

Do not ask, "Which challenge pays the most?"

Ask:

"Which hedge type am I building, how does that change the EV formula, and which challenge gives me the best funded upside for the lowest total cost, lowest operational fragility, and lowest capital strain while staying inside the rules?"

That is how Hedge Edge should think about prop firm hedging.
