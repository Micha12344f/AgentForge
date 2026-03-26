# Hedge Edge — EA Installation Guide (MetaTrader 5)

Follow these steps to install and set up the Hedge Edge Expert Advisor on MetaTrader 5.

---

## What You Need

- A Windows PC (Windows 10 or newer)
- MetaTrader 5 installed and logged into your **prop firm** account
- A personal broker account (Vantage or BlackBull recommended)
- Your Hedge Edge license key (from your dashboard)

---

## Step 1: Download the Hedge Edge Desktop App

1. Log into your Hedge Edge dashboard at **hedgedge.info**
2. Download the Hedge Edge installer (.exe file)
3. Run the installer — if Windows Defender prompts you, click **"More info" → "Run anyway"**
4. Once installed, launch the Hedge Edge app

---

## Step 2: Log In to the Desktop App

1. Open the Hedge Edge desktop app
2. Enter your Hedge Edge email and password
3. Click **Sign In**

---

## Step 3: Open MetaTrader 5

1. Open your MetaTrader 5 terminal
2. Log in to your **prop firm evaluation/funded account**
3. Make sure the terminal is running and connected (you should see a live chart)

---

## Step 4: Install the Expert Advisor

1. In the Hedge Edge desktop app, click **"Install EA"**
2. The app will automatically copy the Hedge Edge EA file into your MT5's `MQL5/Experts` folder
3. If prompted, allow the app to access your MT5 data folder

**Manual install (if needed):**
1. Find the EA file in your Hedge Edge installation folder
2. Copy it to: `C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\`
3. Restart MT5

---

## Step 5: Attach the EA to a Chart

1. In MT5, go to **View → Navigator** (or press Ctrl+N)
2. Expand **Expert Advisors**
3. Find **HedgeEdgeLicense**
4. Drag and drop it onto any chart (the pair doesn't matter — the EA manages all hedging)
5. In the pop-up settings window:
   - Check **"Allow Algo Trading"**
   - Click **OK**

---

## Step 6: Enable Algo Trading

1. In MT5's top toolbar, click the **"AutoTrading"** button (it should turn green)
2. You should see a smiley face in the top-right corner of your chart — this means the EA is running

---

## Step 7: Enter Your License Key

1. In the Hedge Edge desktop app, go to **Settings**
2. Paste your license key
3. Click **Activate**
4. The app will confirm your license is active

---

## Step 8: Link Your Personal Broker Account

1. Open a second MT5 terminal for your **personal broker** (Vantage or BlackBull)
2. Log in to your personal trading account
3. Install and attach the Hedge Edge EA on this terminal too (repeat Steps 4-6)
4. In the Hedge Edge app, click **"Link Accounts"** and select both accounts

---

## Step 9: Verify the Hedge Connection

1. In the Hedge Edge app, you should see both accounts listed:
   - Your prop firm account
   - Your personal broker account
2. The status should show **"Connected"** for both
3. Open a small test trade on your prop firm account
4. The EA should automatically open a reverse (hedge) position on your personal broker account

---

## Troubleshooting

### EA not showing in Navigator
- Restart MT5 after installing the EA
- Check that the file is in the correct `MQL5/Experts` folder

### EA has a red "X" instead of smiley face
- Click **AutoTrading** in the toolbar to enable it
- Right-click the EA on the chart → **Properties** → check **"Allow Algo Trading"**

### "License invalid" error
- Double-check your license key in Settings
- Make sure you're logged into the Hedge Edge app with the correct account
- Contact support in the **#hedge-setup-help** Discord channel

### Hedge not executing
- Ensure both MT5 terminals are running and connected
- Check that the EA is attached to a chart on **both** terminals
- Make sure **AutoTrading** is enabled on **both** terminals
- Verify both accounts show "Connected" in the Hedge Edge app

### App won't start / crashes
- Try running as Administrator
- Check Windows Defender isn't blocking the app
- Reinstall from your dashboard

---

## Need Help?

- **Discord**: Join our community and post in **#hedge-setup-help**
- **Email**: hedgeedgebusiness@gmail.com
- **Dashboard**: hedgedge.info
