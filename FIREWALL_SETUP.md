# Windows Firewall Configuration for Green Wall Server

## Problem
The Raspberry Pi cannot connect to the server because Windows Firewall is blocking port 5000.

Error: `Connection refused` when trying to connect to `192.168.0.38:5000`

## Solution: Add Firewall Rule

### Option 1: Using Command Prompt (Administrator)

1. **Open Command Prompt as Administrator**:
   - Press `Win + X`
   - Click "Command Prompt (Admin)" or "Windows PowerShell (Admin)"

2. **Run this command**:
   ```cmd
   netsh advfirewall firewall add rule name="Green Wall Server Port 5000" dir=in action=allow protocol=TCP localport=5000
   ```

3. **Verify the rule was added**:
   ```cmd
   netsh advfirewall firewall show rule name="Green Wall Server Port 5000"
   ```

### Option 2: Using Windows Defender Firewall GUI

1. **Open Windows Defender Firewall**:
   - Press `Win + R`
   - Type: `wf.msc`
   - Press Enter

2. **Create Inbound Rule**:
   - Click "Inbound Rules" in left panel
   - Click "New Rule..." in right panel
   - Select "Port" → Click Next
   - Select "TCP"
   - Enter "5000" in "Specific local ports"
   - Click Next
   - Select "Allow the connection"
   - Click Next
   - Check all profiles (Domain, Private, Public)
   - Click Next
   - Name: "Green Wall Server Port 5000"
   - Click Finish

## Test the Connection

After adding the firewall rule, test from your Raspberry Pi:

```bash
nc -zv 192.168.0.38 5000
```

**Expected output:**
```
Connection to 192.168.0.38 5000 port [tcp/*] succeeded!
```

## Then Restart the Client

Once the firewall rule is added and the connection test succeeds:

```bash
python3 pi_greenwall_client.py
```

The client should now connect successfully!
