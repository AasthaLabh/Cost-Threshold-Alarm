import os
import json
import boto3
from datetime import datetime

# Initialize SNS client via LabRole permissions
sns_client = boto3.client("sns")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cloud Cost Threshold Alarm & FinOps Simulator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    .font-mono-tech { font-family: 'Share Tech Mono', monospace; }
    .oled-screen {
      background: radial-gradient(circle at 50% 50%, #0d1e15 0%, #050a07 100%);
      box-shadow: inset 0 0 18px rgba(0, 255, 128, 0.2), 0 0 10px rgba(0, 0, 0, 0.8);
      border: 3px solid #1f2937;
    }
    .oled-scanline {
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                  linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      background-size: 100% 3px, 4px 100%;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between font-['Inter']">

  <!-- Header -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></div>
      <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
        <span>AWS FinOps Simulator</span>
        <span class="text-xs font-mono font-normal bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Learner Lab</span>
      </h1>
    </div>
    <div class="text-xs text-slate-400 font-mono">
      Single-Lambda Architecture (Function URL)
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-5xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 my-auto">
    
    <!-- Controls Column -->
    <div class="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between space-y-6">
      <div>
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1">FinOps Parameters</h2>
        <p class="text-xs text-slate-500 mb-6">Simulate daily burn rates against cloud governance thresholds.</p>

        <!-- Spend Slider -->
        <div class="space-y-3 mb-6">
          <div class="flex justify-between items-center text-sm">
            <label for="spend-slider" class="font-medium text-slate-300">Simulated Daily Spend</label>
            <span id="spend-val-text" class="font-mono text-emerald-400 font-bold text-base">$45.00</span>
          </div>
          <input id="spend-slider" type="range" min="0" max="200" value="45" step="1"
            class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500">
          <div class="flex justify-between text-[11px] text-slate-500 font-mono">
            <span>$0</span>
            <span>$100</span>
            <span>$200</span>
          </div>
        </div>

        <!-- Threshold Slider -->
        <div class="space-y-3 mb-6">
          <div class="flex justify-between items-center text-sm">
            <label for="thresh-slider" class="font-medium text-slate-300">Budget Threshold</label>
            <span id="thresh-val-text" class="font-mono text-amber-400 font-bold text-base">$100.00</span>
          </div>
          <input id="thresh-slider" type="range" min="10" max="150" value="100" step="1"
            class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500">
          <div class="flex justify-between text-[11px] text-slate-500 font-mono">
            <span>$10</span>
            <span>$75</span>
            <span>$150</span>
          </div>
        </div>
      </div>

      <!-- Action Button & Audio State -->
      <div class="space-y-3">
        <button id="evaluate-btn" onclick="triggerSimulation()" 
          class="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow-md transition-all flex items-center justify-center space-x-2">
          <span>Evaluate & Push Metrics</span>
          <svg id="spinner" class="hidden animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
        </button>
        <div class="flex items-center justify-between text-xs text-slate-500 px-1">
          <span id="audio-status" class="flex items-center gap-1.5">
            <span class="h-2 w-2 rounded-full bg-slate-600"></span> Synthesizer Buzzer Ready
          </span>
          <span id="last-ping" class="font-mono">Sync: Idle</span>
        </div>
      </div>
    </div>

    <!-- Virtual OLED Terminal & Telemetry Display -->
    <div class="lg:col-span-6 flex flex-col space-y-4">
      
      <!-- Retro Digital Twin Box -->
      <div class="oled-screen rounded-xl p-5 relative overflow-hidden font-mono-tech flex flex-col justify-between min-h-[300px]">
        <div class="absolute inset-0 oled-scanline pointer-events-none"></div>

        <!-- Terminal Header -->
        <div class="flex justify-between items-center text-xs text-emerald-600 border-b border-emerald-900/60 pb-2">
          <span>DEV_TWIN // I2C_ADDR 0x3C</span>
          <span id="oled-timestamp">00:00:00 UTC</span>
        </div>

        <!-- Terminal Center Data -->
        <div class="my-4 space-y-2">
          <div class="text-xs text-emerald-500/80">BURD_RATE TELEMETRY:</div>
          <div class="flex items-baseline justify-between">
            <span class="text-emerald-400 text-sm">SPEND:</span>
            <span id="oled-spend" class="text-2xl text-emerald-300 font-bold tracking-wider">$45.00</span>
          </div>
          <div class="flex items-baseline justify-between">
            <span class="text-emerald-400 text-sm">LIMIT:</span>
            <span id="oled-thresh" class="text-2xl text-emerald-300 font-bold tracking-wider">$100.00</span>
          </div>
          <div class="flex items-baseline justify-between border-t border-emerald-900/60 pt-2">
            <span class="text-emerald-400 text-sm">VARIANCE:</span>
            <span id="oled-diff" class="text-lg text-emerald-400 font-bold">-$55.00</span>
          </div>
        </div>

        <!-- Terminal Status Banner -->
        <div id="oled-banner" class="border border-emerald-500/50 bg-emerald-950/40 text-emerald-400 text-center py-2 px-3 rounded text-sm font-bold tracking-widest">
          STATUS: BUDGET_OK
        </div>
      </div>

      <!-- Cloud Status Badge Card -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div>
          <div class="text-xs text-slate-400 font-semibold uppercase">Cloud Alarm State</div>
          <div id="alarm-desc" class="text-sm text-slate-300">Within safe operating limits</div>
        </div>
        <span id="status-badge" class="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          NORMAL
        </span>
      </div>

    </div>
  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800 bg-slate-900/40 py-3 text-center text-xs text-slate-500">
    AWS Learner Lab Compliant &bull; Zero Standby Cost &bull; Serverless Event-Driven Pattern
  </footer>

  <!-- Client-Side Evaluation & Web Audio Engine -->
  <script>
    let audioCtx = null;
    let beepingInterval = null;

    function playBuzzerPulse() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(840, audioCtx.currentTime);
      gainNode.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.18);

      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.2);
    }

    function startAlarmAudio() {
      if (!beepingInterval) {
        playBuzzerPulse();
        beepingInterval = setInterval(playBuzzerPulse, 400);
      }
    }

    function stopAlarmAudio() {
      if (beepingInterval) {
        clearInterval(beepingInterval);
        beepingInterval = null;
      }
    }

    const spendSlider = document.getElementById('spend-slider');
    const threshSlider = document.getElementById('thresh-slider');
    const spendText = document.getElementById('spend-val-text');
    const threshText = document.getElementById('thresh-val-text');

    const oledSpend = document.getElementById('oled-spend');
    const oledThresh = document.getElementById('oled-thresh');
    const oledDiff = document.getElementById('oled-diff');

    function updateLocalPreview() {
      const s = parseFloat(spendSlider.value).toFixed(2);
      const t = parseFloat(threshSlider.value).toFixed(2);
      const diff = (s - t).toFixed(2);

      spendText.innerText = `$${s}`;
      threshText.innerText = `$${t}`;
      oledSpend.innerText = `$${s}`;
      oledThresh.innerText = `$${t}`;
      oledDiff.innerText = diff > 0 ? `+$${diff}` : `-$${Math.abs(diff).toFixed(2)}`;
    }

    spendSlider.addEventListener('input', updateLocalPreview);
    threshSlider.addEventListener('input', updateLocalPreview);

    setInterval(() => {
      document.getElementById('oled-timestamp').innerText = new Date().toISOString().substring(11, 19) + ' UTC';
    }, 1000);

    async function triggerSimulation() {
      const spend = parseFloat(spendSlider.value);
      const thresh = parseFloat(threshSlider.value);
      const spinner = document.getElementById('spinner');
      const btn = document.getElementById('evaluate-btn');

      spinner.classList.remove('hidden');
      btn.disabled = true;

      try {
        const res = await fetch(window.location.href, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ current_spend: spend, threshold: thresh })
        });
        
        const data = await res.json();
        renderServerResponse(data);
      } catch (err) {
        console.error("Evaluation error:", err);
      } finally {
        spinner.classList.add('hidden');
        btn.disabled = false;
        document.getElementById('last-ping').innerText = `Sync: ${new Date().toLocaleTimeString()}`;
      }
    }

    function renderServerResponse(data) {
      const banner = document.getElementById('oled-banner');
      const badge = document.getElementById('status-badge');
      const desc = document.getElementById('alarm-desc');

      if (data.breached) {
        banner.className = "border border-red-500 bg-red-950/70 text-red-400 text-center py-2 px-3 rounded text-sm font-bold tracking-widest animate-pulse";
        banner.innerText = "STATUS: LIMIT_BREACHED [ALERT SENT]";

        badge.className = "px-3 py-1 text-xs font-semibold rounded-full bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse";
        badge.innerText = "BREACHED";

        desc.innerText = data.sns_dispatched 
          ? `Over budget by $${data.overage.toFixed(2)} - SNS notification delivered.` 
          : `Over budget by $${data.overage.toFixed(2)} - (SNS topic unconfigured).`;

        startAlarmAudio();
      } else {
        banner.className = "border border-emerald-500/50 bg-emerald-950/40 text-emerald-400 text-center py-2 px-3 rounded text-sm font-bold tracking-widest";
        banner.innerText = "STATUS: BUDGET_OK";

        badge.className = "px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
        badge.innerText = "NORMAL";

        desc.innerText = "Spend is within threshold limits.";
        stopAlarmAudio();
      }
    }

    updateLocalPreview();
  </script>
</body>
</html>
"""

def lambda_handler(event, context):
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    # Serve Single-File UI Dashboard
    if http_method == "GET":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-cache"
            },
            "body": HTML_DASHBOARD
        }

    # Evaluate FinOps Simulation & Send Alert
    elif http_method == "POST":
        try:
            body_str = event.get("body", "{}")
            payload = json.loads(body_str) if body_str else {}

            spend = float(payload.get("current_spend", 0.0))
            threshold = float(payload.get("threshold", 0.0))
            breached = spend > threshold
            overage = round(spend - threshold, 2) if breached else 0.0

            sns_sent = False
            if breached and SNS_TOPIC_ARN:
                timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                alert_subject = f"CRITICAL: AWS Cloud Budget Breach Alert (${spend} > ${threshold})"
                alert_message = (
                    "========================================\n"
                    "   FINOPS CLOUD BUDGET BREACH DETECTED   \n"
                    "========================================\n\n"
                    f"Timestamp        : {timestamp_str}\n"
                    f"Threshold Limit  : ${threshold:.2f}\n"
                    f"Evaluated Spend  : ${spend:.2f}\n"
                    f"Total Overage    : ${overage:.2f}\n"
                    "Risk Factor      : HIGH\n\n"
                    "Automated Action : Notification pushed to subscribers.\n"
                    "Recommended Next : Review provisioning of compute resources & idle NAT Gateways.\n\n"
                    "Architecture: AWS Lambda Function URL (Python 3.12) -> Amazon SNS"
                )

                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=alert_subject[:100],
                    Message=alert_message
                )
                sns_sent = True

            response_data = {
                "current_spend": spend,
                "threshold": threshold,
                "breached": breached,
                "overage": overage,
                "sns_dispatched": sns_sent
            }

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(response_data)
            }

        except Exception as e:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": str(e)})
            }

    return {
        "statusCode": 405,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Method Not Allowed"})
    }
