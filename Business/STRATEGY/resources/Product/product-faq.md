# Hedge Edge — Product FAQ

Frequently asked questions about the Hedge Edge desktop app.

---

## General

### What is Hedge Edge?
Hedge Edge is a desktop application that automatically hedges your prop firm trades. When you open a position on a prop firm account, the app instantly opens a reverse position on your personal broker account — protecting your capital whether the challenge passes or fails.

### How does hedging work?
When you enter a BUY on your prop firm account, Hedge Edge automatically places a SELL of the same size on your personal broker account (and vice versa). This means:
- If the prop firm trade wins → you profit on the prop account, lose on personal (but keep the funded account)
- If the prop firm trade loses → you lose on the prop account, profit on personal (capital preserved)

Either way, your total risk is minimized.

### Is this legal?
Hedging on a personal account is perfectly legal. You're trading your own money on your own broker. However, some prop firms have rules against certain hedging strategies. **Always check your prop firm's rules before using any hedging tool.**

### What platforms are supported?
- **MetaTrader 5 (MT5)** — Fully supported and live
- **MetaTrader 4 (MT4)** — Coming soon
- **cTrader** — Coming soon

### What operating systems are supported?
- **Windows 10/11** — Fully supported
- **macOS** — Planned for future release

---

## Pricing

### How much does Hedge Edge cost?

| Plan | Price | Accounts |
|------|-------|----------|
| **Hedge Guide** | Free | 1 account |
| **Challenge Shield** | $29/month or $249/year | Up to 3 accounts |
| **Multi-Challenge** | $59/month or $499/year | Up to 5 accounts (coming soon) |
| **Unlimited** | $99/month or $849/year | Unlimited accounts (coming soon) |

### What's included in the free plan?
- 1 funded/evaluation account connection
- Interactive hedge tutorial
- Discord community access
- Broker setup walkthrough

### What extra features do paid plans include?
- **Challenge Shield ($29/mo)**: Up to 3 accounts, automated hedge execution, basic analytics, P/L tracking, hedge calculation, email notifications, email support
- **Multi-Challenge ($59/mo)**: Up to 5 accounts, full analytics dashboard, per-challenge P/L attribution, hedge efficiency scoring, visual hedge map
- **Unlimited ($99/mo)**: Unlimited accounts, MT4/MT5/cTrader support, optimal hedge sizing, spread cost analysis, challenge ROI calculator, premium Discord access

### Can I cancel anytime?
Yes. All subscriptions are monthly with no lock-in. Cancel anytime from your dashboard.

---

## Brokers

### Which brokers work with Hedge Edge?
We recommend two partner brokers for your personal (hedge) account:

- **Vantage** — Fast execution, tight spreads on major forex pairs
- **BlackBull** — Deep liquidity, great for larger lot sizes

### Do I have to use a partner broker?
Our partner brokers are recommended because they're tested and verified with the app. Support for additional brokers may be added in the future.

### How do I set up a broker account?
1. Sign up for a **Vantage** or **BlackBull** account through the links in your Hedge Edge dashboard
2. Complete their verification process
3. Fund your account (minimum deposit varies by broker)
4. Download MT5 from your broker's website
5. Log in to MT5 with your broker credentials

---

## Accounts & Setup

### How many accounts can I connect?
Depends on your plan:
- **Free**: 1 prop firm account
- **Challenge Shield**: Up to 3 prop firm accounts
- **Multi-Challenge**: Up to 5
- **Unlimited**: No limit

### Can I hedge multiple prop firms at once?
Yes, if your plan supports multiple accounts. Each prop firm account is linked to a hedge position on your personal broker account.

### Do I need a VPS?
A VPS (Virtual Private Server) is **optional but recommended** if you want the hedge to run 24/7 without keeping your PC on. A Windows VPS costs roughly $10-20/month.

If you only trade during specific hours and your PC is on, you don't need a VPS.

### What's the minimum deposit for the hedge account?
This depends on your broker and the size of your prop firm challenges. As a general guideline:
- **$500-1,000** for challenges up to $25K
- **$1,000-2,500** for challenges up to $100K
- **$2,500+** for challenges above $100K

The exact amount depends on the instruments you trade, lot sizes, and leverage offered by your broker.

---

## Troubleshooting

### The EA isn't connecting
1. Make sure MT5 is running and logged in
2. Check that **AutoTrading** is enabled (green button in MT5 toolbar)
3. Verify the EA shows a smiley face (not a red X) on the chart
4. Restart MT5 and the Hedge Edge app

### Hedge isn't executing
1. Ensure both MT5 terminals are running (prop firm + personal broker)
2. Check that the EA is attached on **both** terminals
3. Verify both accounts show "Connected" in the Hedge Edge app
4. Check your personal broker account has sufficient margin

### License key not working
1. Copy-paste the key from your dashboard (don't type it manually)
2. Make sure there are no extra spaces
3. Check you're on the correct Hedge Edge account
4. Contact support in **#hedge-setup-help** on Discord

### App crashing or not starting
1. Try running as Administrator (right-click → Run as administrator)
2. Check Windows Defender or antivirus isn't blocking the app
3. Reinstall the latest version from your dashboard
4. If the issue persists, post in **#hedge-setup-help** with your Windows version

---

## Contact & Support

- **Discord Community**: Join for real-time help — post in **#hedge-setup-help**
- **Email**: hedgeedgebusiness@gmail.com
- **Website**: hedgedge.info
