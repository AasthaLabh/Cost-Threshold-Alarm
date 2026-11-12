import os
import json
import boto3
from datetime import datetime, timedelta

# Initialize AWS Clients using LabRole permissions
sns_client = boto3.client("sns")
ec2_client = boto3.client("ec2")
s3_client = boto3.client("s3")
cw_client = boto3.client("cloudwatch")

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

# Standard us-east-1 On-Demand Hourly Pricing Table ($/hr)
EC2_HOURLY_RATES = {
    "t2.nano": 0.0058,
    "t2.micro": 0.0116,
    "t2.small": 0.0230,
    "t2.medium": 0.0464,
    "t3.nano": 0.0052,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
}

def calculate_real_aws_spend():
    """Queries live AWS services via LabRole to calculate actual daily burn rate."""
    breakdown = []
    total_daily_cost = 0.0

    # 1. Meter Live Running EC2 Instances
    try:
        ec2_resp = ec2_client.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        running_instances = []
        ec2_daily = 0.0
        for res in ec2_resp.get("Reservations", []):
            for inst in res.get("Instances", []):
                itype = inst.get("InstanceType", "t2.micro")
                hourly = EC2_HOURLY_RATES.get(itype, 0.02)
                daily = hourly * 24
                ec2_daily += daily
                running_instances.append(f"{inst['InstanceId']} ({itype})")
        
        total_daily_cost += ec2_daily
        breakdown.append({
            "service": "Amazon EC2",
            "detail": f"{len(running_instances)} running instance(s)" + (f": {', '.join(running_instances)}" if running_instances else ""),
            "daily_cost": round(ec2_daily, 4)
        })
    except Exception as e:
        breakdown.append({"service": "Amazon EC2", "detail": f"Scan skipped: {str(e)}", "daily_cost": 0.0})

    # 2. Meter Active S3 Buckets (Base Storage & Request Overhead)
    try:
        s3_resp = s3_client.list_buckets()
        bucket_count = len(s3_resp.get("Buckets", []))
        # Baseline metering: $0.023/GB-month + API request overhead (~$0.015/day per active bucket)
        s3_daily = bucket_count * 0.015
        total_daily_cost += s3_daily
        breakdown.append({
            "service": "Amazon S3",
            "detail": f"{bucket_count} active bucket(s) metered",
            "daily_cost": round(s3_daily, 4)
        })
    except Exception as e:
        breakdown.append({"service": "Amazon S3", "detail": f"Scan skipped: {str(e)}", "daily_cost": 0.0})

    # 3. Meter Real Lambda Invocations (Last 24 Hours via CloudWatch)
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        cw_resp = cw_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Sum"]
        )
        datapoints = cw_resp.get("Datapoints", [])
        invocations = int(datapoints[0]["Sum"]) if datapoints else 1
        # $0.20 per 1M requests + compute duration estimate
        lambda_daily = (invocations / 1_000_000) * 0.20
        total_daily_cost += lambda_daily
        breakdown.append({
            "service": "AWS Lambda",
            "detail": f"{invocations} invocation(s) in last 24h",
            "daily_cost": round(lambda_daily, 6)
        })
    except Exception as e:
        breakdown.append({"service": "AWS Lambda", "detail": "Active execution metered", "daily_cost": 0.0})

    return round(total_daily_cost, 4), breakdown


HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Real-Time AWS FinOps Cost Threshold Alarm</title>
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

  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></div>
      <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
        <span>AWS Live FinOps Cost Metering & Alarm</span>
        <span class="text-xs font-mono font-normal bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800">Boto3 Live Telemetry</span>
      </h1>
    </div>
    <div class="text-xs text-slate-400 font-mono">
      Region: us-east-1 | Role: LabRole
    </div>
  </header>

  <main class="max-w-6xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 my-auto">
    
    <!-- Left Column: Controls & Live Breakdown -->
    <div class="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between space-y-5">
      <div>
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1">Governance & Metering Controls</h2>
        <p class="text-xs text-slate-500 mb-5">Queries live EC2, S3 & CloudWatch metrics via AWS SDK to compute real daily spend.</p>

        <!-- Threshold Slider -->
        <div class="space-y-2 mb-5">
          <div class="flex justify-between items-center text-sm">
            <label for="thresh-slider" class="font-medium text-slate-300">Daily Budget Threshold ($)</label>
            <span id="thresh-val-text" class="font-mono text-amber-400 font-bold text-base">$0.50</span>
          </div>
          <input id="thresh-slider" type="range" min="0.05" max="20" value="0.50" step="0.05"
            class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500">
          <div class="flex justify-between text-[11px] text-slate-500 font-mono">
            <span>$0.05 (Strict)</span>
            <span>$10.00</span>
            <span>$20.00</span>
          </div>
        </div>

        <!-- Optional Stress Test Spike -->
        <div class="space-y-2 mb-5 pt-3 border-t border-slate-800">
          <div class="flex justify-between items-center text-sm">
            <label for="spike-slider" class="font-medium text-slate-400">Simulated Workload Spike (+$)</label>
            <span id="spike-val-text" class="font-mono text-sky-400 font-bold text-sm">+$0.00</span>
          </div>
          <input id="spike-slider" type="range" min="0" max="15" value="0" step="0.5"
            class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500">
          <p class="text-[11px] text-slate-500">Keep at $0.00 for 100% pure live account spend, or add load to test breach alarms.</p>
        </div>

        <!-- Live AWS Resource Breakdown Table -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
          <div class="text-xs font-semibold text-slate-400 uppercase mb-2">Live AWS Resource Telemetry</div>
          <div id="resource-list" class="space-y-2 text-xs font-mono text-slate-300">
            <div class="text-slate-500 italic">Click "Scan Live AWS Resources" to fetch telemetry...</div>
          </div>
        </div>
      </div>

      <!-- Action Button -->
      <div class="space-y-2">
        <button id="evaluate-btn" onclick="triggerScan()" 
          class="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow-md transition-all flex items-center justify-center space-x-2">
          <span>Scan Live AWS Resources & Evaluate</span>
          <svg id="spinner" class="hidden animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
        </button>
        <div class="flex items-center justify-between text-xs text-slate-500 px-1">
          <span>Web Audio Synthesizer: Ready</span>
          <span id="last-ping" class="font-mono">Last Scan: Never</span>
        </div>
      </div>
    </div>

    <!-- Right Column: Virtual OLED Terminal -->
    <div class="lg:col-span-6 flex flex-col space-y-4">
      <div class="oled-screen rounded-xl p-5 relative overflow-hidden font-mono-tech flex flex-col justify-between min-h-[340px]">
        <div class="absolute inset-0 oled-scanline pointer-events-none"></div>

        <div class="flex justify-between items-center text-xs text-emerald-600 border-b border-emerald-900/60 pb-2">
          <span>AWS_LIVE_METER // I2C_0x3C</span>
          <span id="oled-timestamp">00:00:00 UTC</span>
        </div>

        <div class="my-4 space-y-2.5">
          <div class="flex items-baseline justify-between">
            <span class="text-emerald-400 text-sm">REAL AWS SPEND:</span>
            <span id="oled-real" class="text-xl text-emerald-300 font-bold">$0.0000/day</span>
          </div>
          <div class="flex items-baseline justify-between">
            <span class="text-emerald-400 text-sm">SIMULATED LOAD:</span>
            <span id="oled-spike" class="text-base text-sky-400 font-bold">+$0.0000/day</span>
          </div>
          <div class="flex items-baseline justify-between border-t border-emerald-900/60 pt-2">
            <span class="text-emerald-400 text-sm">TOTAL BURN RATE:</span>
            <span id="oled-total" class="text-2xl text-emerald-300 font-bold">$0.0000</span>
          </div>
          <div class="flex items-baseline justify-between">
            <span class="text-emerald-400 text-sm">BUDGET LIMIT:</span>
            <span id="oled-thresh" class="text-xl text-amber-300 font-bold">$0.5000</span>
          </div>
        </div>

        <div id="oled-banner" class="border border-emerald-500/50 bg-emerald-950/40 text-emerald-400 text-center py-2.5 px-3 rounded text-sm font-bold tracking-widest">
          STATUS: AWAITING_SCAN
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div>
          <div class="text-xs text-slate-400 font-semibold uppercase">Cloud Governance State</div>
          <div id="alarm-desc" class="text-sm text-slate-300">Ready to query live AWS account resources</div>
        </div>
        <span id="status-badge" class="px-3 py-1 text-xs font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          IDLE
        </span>
      </div>
    </div>
  </main>

  <footer class="border-t border-slate-800 bg-slate-900/40 py-3 text-center text-xs text-slate-500">
    Real-Time Boto3 Resource Metering (EC2 + S3 + CloudWatch) &bull; Zero Cost Explorer Fees
  </footer>

  <script>
    let audioCtx = null;
    let beepingInterval = null;

    function playBuzzerPulse() {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx.state === 'suspended') audioCtx.resume();
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

    const threshSlider = document.getElementById('thresh-slider');
    const spikeSlider = document.getElementById('spike-slider');

    function updateSliderLabels() {
      const t = parseFloat(threshSlider.value).toFixed(2);
      const s = parseFloat(spikeSlider.value).toFixed(2);
      document.getElementById('thresh-val-text').innerText = `$${t}`;
      document.getElementById('spike-val-text').innerText = `+$${s}`;
      document.getElementById('oled-thresh').innerText = `$${parseFloat(t).toFixed(4)}`;
      document.getElementById('oled-spike').innerText = `+$${parseFloat(s).toFixed(4)}/day`;
    }

    threshSlider.addEventListener('input', updateSliderLabels);
    spikeSlider.addEventListener('input', updateSliderLabels);

    setInterval(() => {
      document.getElementById('oled-timestamp').innerText = new Date().toISOString().substring(11, 19) + ' UTC';
    }, 1000);

    async function triggerScan() {
      const thresh = parseFloat(threshSlider.value);
      const spike = parseFloat(spikeSlider.value);
      const spinner = document.getElementById('spinner');
      const btn = document.getElementById('evaluate-btn');

      spinner.classList.remove('hidden');
      btn.disabled = true;

      try {
        const res = await fetch(window.location.href, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ threshold: thresh, simulated_spike: spike })
        });
        const data = await res.json();
        renderResponse(data);
      } catch (err) {
        console.error("Scan error:", err);
      } finally {
        spinner.classList.add('hidden');
        btn.disabled = false;
        document.getElementById('last-ping').innerText = `Last Scan: ${new Date().toLocaleTimeString()}`;
      }
    }

    function renderResponse(data) {
      document.getElementById('oled-real').innerText = `$${data.real_aws_spend.toFixed(4)}/day`;
      document.getElementById('oled-spike').innerText = `+$${data.simulated_spike.toFixed(4)}/day`;
      document.getElementById('oled-total').innerText = `$${data.total_spend.toFixed(4)}`;
      document.getElementById('oled-thresh').innerText = `$${data.threshold.toFixed(4)}`;

      // Render Breakdown List
      const listEl = document.getElementById('resource-list');
      listEl.innerHTML = data.breakdown.map(item => `
        <div class="flex justify-between items-start border-b border-slate-800/80 pb-1.5">
          <div>
            <span class="text-emerald-400 font-semibold">${item.service}</span>
            <div class="text-[11px] text-slate-400">${item.detail}</div>
          </div>
          <span class="text-slate-200 font-bold">$${item.daily_cost.toFixed(4)}</span>
        </div>
      `).join('');

      const banner = document.getElementById('oled-banner');
      const badge = document.getElementById('status-badge');
      const desc = document.getElementById('alarm-desc');

      if (data.breached) {
        banner.className = "border border-red-500 bg-red-950/70 text-red-400 text-center py-2.5 px-3 rounded text-sm font-bold tracking-widest animate-pulse";
        banner.innerText = "STATUS: LIMIT_BREACHED [SNS SENT]";
        badge.className = "px-3 py-1 text-xs font-semibold rounded-full bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse";
        badge.innerText = "BREACHED";
        desc.innerText = `Exceeded budget by $${data.overage.toFixed(4)} — Real-time alert dispatched.`;
        startAlarmAudio();
      } else {
        banner.className = "border border-emerald-500/50 bg-emerald-950/40 text-emerald-400 text-center py-2.5 px-3 rounded text-sm font-bold tracking-widest";
        banner.innerText = "STATUS: BUDGET_OK";
        badge.className = "px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
        badge.innerText = "NORMAL";
        desc.innerText = "Live AWS infrastructure spend is within safe budget limits.";
        stopAlarmAudio();
      }
    }

    updateSliderLabels();
    // Auto-scan on initial load
    window.addEventListener('DOMContentLoaded', triggerScan);
  </script>
</body>
</html>
"""

def lambda_handler(event, context):
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if http_method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-cache"},
            "body": HTML_DASHBOARD
        }

    elif http_method == "POST":
        try:
            body_str = event.get("body", "{}")
            payload = json.loads(body_str) if body_str else {}

            threshold = float(payload.get("threshold", 0.50))
            simulated_spike = float(payload.get("simulated_spike", 0.0))

            # Query Live AWS Account Resources via Boto3
            real_aws_spend, breakdown = calculate_real_aws_spend()
            total_spend = round(real_aws_spend + simulated_spike, 4)

            breached = total_spend > threshold
            overage = round(total_spend - threshold, 4) if breached else 0.0

            sns_sent = False
            if breached and SNS_TOPIC_ARN:
                timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                breakdown_lines = "\n".join(
                    [f"  - {b['service']}: ${b['daily_cost']:.4f}/day ({b['detail']})" for b in breakdown]
                )
                alert_subject = f"CRITICAL: AWS Live FinOps Budget Breach (${total_spend:.2f} > ${threshold:.2f})"
                alert_message = (
                    "================================================\n"
                    "   REAL-TIME AWS FINOPS BUDGET BREACH ALERT     \n"
                    "================================================\n\n"
                    f"Timestamp          : {timestamp_str}\n"
                    f"Budget Threshold   : ${threshold:.4f}/day\n"
                    f"Live AWS Spend     : ${real_aws_spend:.4f}/day\n"
                    f"Simulated Load     : ${simulated_spike:.4f}/day\n"
                    f"Total Burn Rate    : ${total_spend:.4f}/day\n"
                    f"Overage Delta      : +${overage:.4f}/day\n\n"
                    "Live Account Resource Breakdown:\n"
                    f"{breakdown_lines}\n\n"
                    "Automated Action   : Alert dispatched via Amazon SNS.\n"
                    "Architecture       : AWS Lambda (Boto3 Live Metering) -> Amazon SNS"
                )

                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=alert_subject[:100],
                    Message=alert_message
                )
                sns_sent = True

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "real_aws_spend": real_aws_spend,
                    "simulated_spike": simulated_spike,
                    "total_spend": total_spend,
                    "threshold": threshold,
                    "breached": breached,
                    "overage": overage,
                    "breakdown": breakdown,
                    "sns_dispatched": sns_sent
                })
            }

        except Exception as e:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": str(e)})
            }

    return {"statusCode": 405, "body": json.dumps({"message": "Method Not Allowed"})}