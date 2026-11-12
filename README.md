# Cloud Cost Threshold Alarm & Real-Time FinOps Metering System

A 100% serverless, zero-overhead FinOps governance tool and real-time cloud cost metering system built on **AWS Lambda**, **Boto3**, and **Amazon SNS**. Engineered specifically for **AWS Learner Lab** / Free-Tier environments with zero standby cost and zero physical hardware dependencies.

---

## Architecture Overview
+---------------------------------------+
                  |       Web Browser (Client UI)         |
                  | - Budget Limit & Stress Spike Sliders |
                  | - Retro Digital Twin OLED Display     |
                  | - Live Resource Cost Breakdown Table  |
                  | - Web Audio API Synthesizer (Buzzer)  |
                  +-------------------+-------------------+
                                      |
                    HTTP GET (UI)     |   HTTP POST (Live Scan)
                                      v
                  +---------------------------------------+
                  |     AWS Lambda (Function URL)         |
                  | - Serves Embedded HTML/JS/CSS         |
                  | - Queries Live EC2, S3 & CloudWatch   |
                  | - Computes Real Daily Burn Rate       |
                  | - Execution Role: LabRole             |
                  +---------+-------------------+---------+
                            |                   |
       Boto3 Describe/      |                   | Trigger on Breach
       GetMetric Calls      |                   |
                            v                   v
       +-------------------------+   +-----------------------+
       | Live AWS Infrastructure |   |   Amazon SNS Topic    |
       | - EC2 Running Instances |   | - Dispatches Itemized |
       | - S3 Buckets            |   |   Breach Alert Email  |
       | - CloudWatch Metrics    |   +-----------+-----------+
       +-------------------------+               |
                                                 v
                                     +-----------------------+
                                     | Subscribed User Inbox |
                                     +-----------------------+

### Key Technical Highlights
- **Real-Time Boto3 Resource Metering:** Bypasses restricted/fee-based AWS Cost Explorer APIs by querying live account resources (`ec2:DescribeInstances`, `s3:ListBuckets`, and `cloudwatch:GetMetricStatistics`) under `LabRole` and mapping usage to official `us-east-1` On-Demand rates.
- **Hybrid Live + Stress-Test Governance:** Combines real-time daily AWS resource spend with an optional simulated workload spike slider (`+$0.00` to `+$15.00`) for safe threshold breach testing.
- **Dual-Routing Single Lambda:** A single Python 3.12 function serves both the static Tailwind CSS dashboard (`HTTP GET`) and the live resource metering & alerting engine (`HTTP POST`) via an **AWS Lambda Function URL** (`AuthType: NONE`).
- **Hardware-Free Digital Twin:** Replaces physical IoT components (ESP32, I2C OLED, piezo buzzer) with an in-browser retro CRT terminal (`I2C_0x3C`) and a Web Audio API 840 Hz sawtooth alarm synthesizer.

---

## Project Structure

```text
├── src/
│   └── lambda_function.py                          # Unified Lambda backend, Boto3 metering & UI
├── docs/
│   ├── CC_product2Report_Updated.docx              # Course Product Report (SR University)
│   └── Cost_Threshold_Alarm_Product_Review_SRU.pptx # Product Review Presentation Slides
├── .gitignore
├── LICENSE
└── README.md
Deployment Guide (AWS Learner Lab)
Step 1: Create Amazon SNS Topic
Open the AWS Management Console and navigate to Amazon SNS -> Topics -> Create topic.

Select Standard, name it FinOps-Cost-Threshold-Alerts, and click Create topic.

Create an Email subscription with your email address and click Confirm subscription in the verification email received.

Copy the Topic ARN.

Step 2: Deploy AWS Lambda Function
Navigate to AWS Lambda -> Create function -> Author from scratch.

Configure:

Function name: FinOps-Simulator-Engine

Runtime: Python 3.12

Execution role: Use an existing role -> LabRole

Copy the code from src/lambda_function.py, paste it into the Lambda code editor, and click Deploy.

Under Configuration -> Environment variables, add:

Key: SNS_TOPIC_ARN

Value: <Your copied SNS Topic ARN>

Under Configuration -> Function URL:

Click Create function URL

Auth type: NONE

Enable CORS (Allow origin: *, Allow methods: GET, POST, Allow headers: content-type)

Academic Metadata
Course: 25CAI102PC205 - Cloud Computing

Institution: SR University, Warangal, Telangana

Author: Aastha Labh (Roll No: 2503A520P5)

Faculty Supervisor: Mr. Bediga Sharan

Academic Year: 2026–2027

License
This project is licensed under the MIT License - see the LICENSE file for details.