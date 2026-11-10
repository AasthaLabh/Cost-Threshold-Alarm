# Cloud Cost Threshold Alarm & FinOps Simulator

A 100% serverless, zero-overhead FinOps governance tool and real-time threshold alert simulator running on AWS Lambda and Amazon SNS. Engineered for **AWS Learner Lab** / Free-Tier environments with zero standby cost and zero physical hardware dependencies.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       Web Browser (Client UI)         |
                      | - Sliders (Spend & Threshold)         |
                      | - Retro Digital Twin OLED Display     |
                      | - Web Audio API Synthesizer (Buzzer)  |
                      +-------------------+-------------------+
                                          |
                        HTTP GET (UI)     |   HTTP POST (Simulate)
                                          v
                      +---------------------------------------+
                      |       AWS Lambda (Function URL)       |
                      | - Serves Embedded HTML/JS/CSS         |
                      | - Evaluates FinOps Budget Math        |
                      | - Execution Role: LabRole             |
                      +-------------------+-------------------+
                                          |
                                          | Trigger on Breach
                                          v
                      +---------------------------------------+
                      |           Amazon SNS Topic            |
                      | - Dispatches Instant Alert Email      |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |          Subscribed User Inbox        |
                      +---------------------------------------+
```

### Key Technical Highlights
- **Dual-Routing Single Lambda:** A single Python 3.12 function handles both static frontend asset streaming (GET) and compute/alert evaluation (POST) via an **AWS Lambda Function URL** (`AuthType: NONE`).
- **Hardware-Free Digital Twin:** Replaces physical IoT components (ESP32, I2C OLED, piezo buzzer) with an in-browser CSS terminal and Web Audio API 840 Hz sawtooth oscillator tone.
- **Learner Lab Compliant:** Runs entirely under the pre-existing `LabRole` in `us-east-1` without incurring billable AWS Cost Explorer API fees or API Gateway charges.

---

## Project Structure

```
├── src/
│   └── lambda_function.py     # Unified Lambda backend & embedded frontend
├── docs/
│   ├── Cost_Threshold_Alarm_Product_Report.docx  # Academic product report
│   └── Cost_Threshold_Alarm_Product_Review_SRU.pptx # Review presentation slides
├── .gitignore
├── LICENSE
└── README.md
```

---

## Deployment Guide (AWS Learner Lab)

### Step 1: Create Amazon SNS Topic
1. Open the AWS Console and go to **Amazon SNS** -> **Topics** -> **Create topic**.
2. Type: **Standard**, Name: `FinOps-Cost-Threshold-Alerts`.
3. Create an **Email** subscription with your email address and click **Confirm subscription** from the verification email.
4. Copy the **Topic ARN**.

### Step 2: Deploy AWS Lambda Function
1. Go to **AWS Lambda** -> **Create function**.
2. Function Name: `FinOps-Simulator-Engine`, Runtime: `Python 3.12`.
3. Under **Permissions**, select **Use an existing role** -> `LabRole`.
4. Paste the contents of `src/lambda_function.py` and click **Deploy**.
5. In **Configuration** -> **Environment variables**, add:
   - `SNS_TOPIC_ARN`: `<Your copied SNS Topic ARN>`
6. In **Configuration** -> **Function URL**:
   - Auth Type: `NONE`
   - Enable CORS: Allow origin `*`, Methods `GET, POST`.

---

## Academic Metadata

- **Course:** 25CAI102PC205 - Cloud Computing
- **Institution:** SR University, Warangal, Telangana
- **Author:** Aastha Labh (Roll No: 2503AA520P5)
- **Faculty Supervisor:** Mr. Bediga Sharan
- **Academic Year:** 2026-2027

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
