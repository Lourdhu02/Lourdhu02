<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <img src="assets/hero-light.svg" width="100%" alt="Lourdu Raju, machine learning engineer at Sujanix, Bengaluru. An ink ensō around the kanji 侍 with an LR seal, and the vertical motto 七転八起: fall seven times, rise eight.">
</picture>

[linkedin](https://www.linkedin.com/in/lourdhu) · [email](mailto:b.lourdhuraju1234@gmail.com) · [kaggle](https://www.kaggle.com/blourdhuraju)

I build computer-vision systems that hold up in production. Right now that means an OCR platform that reads electricity meters for a state utility: I train the models, compile them to TensorRT, serve them on Triton, and put a canary router in front. I keep production disciplined and leave the Jinx-style chaos in the notebook.

```json
{
  "name": "Lourdu Raju",
  "role": "Machine Learning Engineer @ Sujanix",
  "base": "Bengaluru, India",
  "now": "meter-reading OCR for a state utility, 40M readings in production",
  "craft": ["computer vision", "gpu inference", "mlops", "agents"],
  "weapons": ["pytorch", "tensorrt", "triton", "onnx runtime", "aws", "langgraph"],
  "code": "measure first, ship second, talk last",
  "crew": ["Miyamoto Musashi", "Jinx", "Monkey D. Luffy"],
  "open_to": "ml engineering roles"
}
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/katana-dark.svg">
  <img src="assets/katana-light.svg" width="100%" alt="">
</picture>

## 壱 · the work

At **Sujanix** I own the meter-reading OCR platform for a state electricity utility. One photo goes in and one reading comes out. On the busiest day that was 330K requests.

```text
photo ───────> meter? ──────> dials ───────> type ────────> read ────────> "005269" · 0.97
               mobilevitv2    yolo26n-obb    mobilevitv2    svtrv2 + ctc
               └───── triton · 9 tensorrt fp16 engines · nvidia l4 ─────┘

router ── canary slice ──> gpu path   ·   any error or 3 s timeout ──> serverless
```

```text
                          before      after
reading accuracy          79%         91%         live traffic · 40M readings
end-to-end latency, p50   1,415 ms    156 ms      serverless → gpu path
classifier compute        309.5 ms    3.3 ms      onnx runtime → tensorrt fp16
throughput                19 img/s    321 img/s   single image · 16 concurrent
capacity, one l4 gpu      -           181 img/s   p95 340 ms · 0 errors · 12.6× prod peak
container image           4.43 GB     2.2 GB      slimmed layers, then arm64
svtrv2 training           80 img/s    305 img/s   fused sdpa + static torch.compile
```

### 戦 · battle log

- **The decoder that ate digits.** A release fell to 64.2% exact match. The CTC decoder didn't reset its repeat check on blank frames, so `4777.1` came out as `47.1`. A one-line fix brought it back to 84.0%, and tests now pin it.
- **The cliff.** Throughput *dropped* as load rose. One classifier was still on ONNX Runtime. I moved it to TensorRT, after patching a `Transpose` on a UINT8 input that TensorRT rejects, and compute went from 309.5 ms to 3.3 ms.
- **The missing 475.** Fire-and-forget archiving lost 475 objects under burst load. I replaced it with an on-disk spool that retries S3 and DynamoDB until every write lands.
- **The wrong suspect.** At 181 img/s on one L4, the GPU sat at ~45% while the host CPU ran at 85–92%. Profile before you buy hardware.
- **The hardest photos.** I retrained the SVTRv2 reader on production crops (96-px input, re-fit resize buckets, edge-replicated padding). Low-quality photos gained +8.7 pp, and the test set went from 87.7% to 90.1% overall.

### 道 · how it ships

- **One monorepo:** five models in a single uv + DVC repo. Every release records its git SHA, data version, config, checkpoint and runtime. PyTorch → ONNX parity is checked to 1.2e-5, and promotion is gated on p50/p95/p99 latency and an A/B run.
- **Frozen releases:** the serverless service ships as frozen, checksummed releases. Exact match went 83.4% → 87.8% on 2,950 labelled photos, and analog reads went 67.2% → 79.6%.
- **Canary router:** the router puts the GPU path in front of real traffic with a deterministic hash split. It falls back to serverless on any error or 3-second timeout, and both paths return one response shape.

<details>
<summary>how these numbers were measured</summary>
<br>

- **79% → 91%:** measured on live production traffic, over 40M readings.
- **Test-set figures:** exact match of the full reading, leading zeros ignored. The set holds 2,950 meter photos (1,000 digital, 450 with decimals, 1,000 low-quality, 500 analog) and 1,015 non-meter photos, where the correct answer is "no reading". Every version is scored on the same images.
- **Latency:** end to end from an office network, with all 3,965 test photos sent through each path. GPU path: p50 156 ms, p95 205 ms. Serverless: p50 1,415 ms, p95 1,714 ms.
- **Capacity:** a stepped load test of 67,719 requests on one g6.2xlarge (NVIDIA L4). "Sustained" means p95 ≤ 1 s with ≤ 0.5% errors. The production peak (14.4 req/s) and the busiest day (330,707 requests) come from CloudWatch.
- **TensorRT:** the timings are model compute inside Triton. Throughput is single-image requests at 16 concurrent on a GB10.
- **Sources:** the work repos belong to my employer and are private. These figures come from their benchmark reports.

</details>

## 弐 · research

**[svtrv2](https://github.com/Lourdhu02/svtrv2):** a paper-faithful SVTRv2 (ICCV 2025), checked against the official OpenOCR implementation, plus my extension **ARD**:

- **Adaptive resizing:** a small learned router replaces MSR's hand-set aspect-ratio buckets. It is trained with a Bradley–Terry preference loss on which canvas the recognizer reads best.
- **SGM → CTC distillation:** the train-only semantic module teaches the CTC head, using uniform or Viterbi alignment (checked against brute force). The exported model stays byte-identical to the baseline.
- **Status:** 49 tests pass. Benchmarks are still running, so there are no accuracy claims until they finish.

## 参 · side quests

- **[echome](https://github.com/Lourdhu02/echome):** a local-first agent with CoALA-style memory: episodic vectors in Qdrant, consolidated facts and mined procedures, all orchestrated by LangGraph. It also has a CAT/IRT assessment engine (GRM, Fisher-information item selection). It runs fully on-device with Ollama.
- **[finsentinel.ai](https://github.com/Lourdhu02/fin-sentinal.ai):** private RAG over invoices, receipts and bank statements. It uses ChromaDB with per-user isolation, SentenceTransformers, Ollama, and a local VLM for scans. Nothing leaves the machine.

## 肆 · arsenal

```text
vision      pytorch · ultralytics yolo (obb) · svtrv2 · mobilevit · opencv · numpy
inference   tensorrt · triton · onnx runtime · tflite · nginx · flask · gunicorn
cloud       aws ec2 · lambda · s3 · dynamodb · cloudwatch · docker · helm
mlops       dvc · uv · github actions · pytest · ruff · pre-commit
genai       langgraph · ollama · qdrant · chromadb · fastapi · react
```

## 伍 · path

```text
2026 ─ now    ml engineer   sujanix        meter-reading ocr: models → tensorrt → production
2024 ─ 2025   founder       spacedrift     ml builds, data annotation, research support
2024          ds intern     brainovision   forecasting with gbm ensembles, +15% accuracy
```

kaggle notebooks expert · machine learning specialization (deeplearning.ai, stanford) · data science with python (nptel, iit madras)

## 陸 · my dokkōdō

Musashi left 21 precepts. These are mine, so far:

1. Measure before you claim.
2. A model isn't done until it survives production.
3. Read the decoder before you blame the model.
4. Profile before you buy hardware.
5. Never drop data silently.
6. Ship behind a canary, and keep a fallback.
7. Delete more than you add.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/katana-dark.svg">
  <img src="assets/katana-light.svg" width="100%" alt="">
</picture>

<p align="center">
  <sub>The One Piece is real: it's a model that still works in production.</sub><br>
  <sub><a href="https://www.linkedin.com/in/lourdhu">linkedin</a> · <a href="mailto:b.lourdhuraju1234@gmail.com">email</a> · <a href="https://www.kaggle.com/blourdhuraju">kaggle</a></sub>
</p>
