<div align="center">

<img src="assets/hero.svg" width="100%" alt="Lourdu Raju. Machine Learning Engineer at Sujanix. I own computer-vision systems end to end: training runs, TensorRT engines, Triton serving, and the benchmarks that keep them honest.">

<a href="https://www.linkedin.com/in/lourdhu"><img src="assets/btn-linkedin.svg" height="44" alt="LinkedIn"></a>&nbsp;
<a href="mailto:b.lourdhuraju1234@gmail.com"><img src="assets/btn-email.svg" height="44" alt="Email"></a>&nbsp;
<a href="https://www.kaggle.com/blourdhuraju"><img src="assets/btn-kaggle.svg" height="44" alt="Kaggle"></a>

</div>

<br>

<img src="assets/impact.svg" width="100%" alt="By the numbers. Accuracy: 79% to 91% on live traffic, measured over 40M production readings. Latency: 9x lower end-to-end p50, 1,415 ms to 156 ms. Capacity: 181 images per second sustained on one L4 GPU, 12.6x the production peak. Optimization: 94x classifier speed-up, ONNX Runtime 309.5 ms to TensorRT 3.3 ms.">

<img src="assets/pipeline.svg" width="100%" alt="Production at Sujanix: meter-reading OCR for a state electricity utility. Photo, then meter presence (MobileViTv2), dial detection (YOLO26n-OBB), digital or analog (MobileViTv2), OCR (SVTRv2 + CTC), reading. Served on Triton with 9 TensorRT FP16 engines on an NVIDIA L4, behind a canary router with automatic fallback to serverless. 330K requests on the busiest day.">

<img src="assets/card-models.svg" width="100%" alt="01, Models and MLOps: five vision models, one release process.">

- Retrained the SVTRv2 reader for digital displays on production crops (96-px input, re-fit resize buckets, edge-replicated padding). Accuracy went **87.7% → 90.1%** on the full 3,965-image set, and **+8.7 pp** on low-quality photos.
- Every release records the git SHA, DVC revision, config, checkpoint and target runtime. PyTorch → ONNX parity is checked (max difference **1.2e-5**), and promotion is gated on p50/p95/p99 benchmarks and an A/B comparison.
- Made training **3.8× faster** on a DGX Spark (GB10): fused SDPA attention plus a static `torch.compile` took SVTRv2 from **80 → 305 img/s** and cut peak memory from **50.5 → 14.7 GB**.

<img src="assets/card-inference.svg" width="100%" alt="02, GPU inference: Triton and TensorRT on a single L4.">

- Moved the meter classifier from ONNX Runtime to TensorRT, after patching a `Transpose` on a UINT8 input that TensorRT rejects. Compute went **309.5 → 3.3 ms**, single-image p50 at 16 concurrent went **873 → 47 ms**, and throughput went **19 → 321 img/s**. That removed a cliff where throughput *fell* as load rose.
- Load-tested one L4 with 67,719 requests: **181 img/s** sustained at p95 340 ms with zero errors, **12.6×** the production peak. Traced the ceiling to the host CPU (85–92% busy) while the GPU sat at ~45%.
- Replaced fire-and-forget archiving, which dropped **475** objects under burst load, with an on-disk spool that retries S3 and DynamoDB writes. Also added JSON error codes, request IDs and a Triton watchdog.

<img src="assets/card-serving.svg" width="100%" alt="03, Production serving: serverless in production, GPU on canary.">

- Shipped frozen, checksummed releases of the production service. Exact match went **83.4% → 87.8%** on 2,950 labelled meter photos, and analog reads went **67.2% → 79.6%**.
- Root-caused a release regression to a CTC decoding bug: blank frames didn't reset the repeat check, so `4777.1` decoded as `47.1`. Accuracy had fallen to **64.2%**. The fix restored **84.0%**, and tests now pin it.
- Cut the container image from **4.43 → 2.2 GB**, and model loads for non-meter photos from **7 → 1**. Sized ONNX Runtime threads to the function's real vCPUs, and added SSRF-safe URL fetching, upload limits and CloudWatch EMF metrics.
- Built the router that exposes the GPU path to real traffic safely: a hash-based canary split, automatic fallback on any non-2xx response or 3-second timeout, and one response shape for both paths.

<details>
<summary><b>How these numbers were measured</b></summary>
<br>

- **Headline accuracy (79% → 91%):** measured on live production traffic over 40M meter readings, not on a test set.
- **Test-set accuracy** (the release and retraining figures): exact match of the whole reading, leading zeros ignored, on a fixed labelled set of 3,965 photos. The set has 2,950 meter photos (1,000 digital, 450 digital with decimals, 1,000 low-quality, 500 analog) and 1,015 non-meter photos, where the correct answer is "no reading". Every version is scored on the same images. The serverless release figures use only the 2,950 meter photos.
- **Latency:** end to end from an office network, with all 3,965 photos sent through each path. GPU path: p50 156 ms, p95 205 ms. Serverless: p50 1,415 ms, p95 1,714 ms.
- **Capacity:** a stepped load test of 67,719 requests against one g6.2xlarge (NVIDIA L4). "Sustained" means p95 ≤ 1 s with ≤ 0.5% errors. The production peak (14.4 requests/s) and the busiest day (330,707 requests) come from CloudWatch.
- **TensorRT:** the timings are model compute inside Triton. The p50 and throughput figures are single-image requests at 16 concurrent on a GB10.

The source repositories belong to my employer and are private. These figures are taken from their benchmark reports.

</details>

<br>

<a href="https://github.com/Lourdhu02/svtrv2"><img src="assets/card-research.svg" width="100%" alt="Research: SVTRv2, reproduced and extended. Public repository."></a>

- Checked the architecture against the official OpenOCR implementation: two 3×3 grouped-conv local mixing, W/4 timesteps, no positional embedding. There are 49 tests, including an end-to-end CPU training run.
- **ARD, part 1:** a small learned router replaces MSR's hand-set aspect-ratio buckets. It is trained with a Bradley–Terry preference loss on which canvas the recognizer reads best.
- **ARD, part 2:** the train-only semantic guidance module becomes a soft teacher for the CTC head, with uniform or Viterbi alignment (checked against brute force). The exported model stays byte-identical to the baseline.
- Status: implemented and tested. Benchmark runs are in progress, so there are no accuracy claims yet.

<a href="https://github.com/Lourdhu02/echome"><img src="assets/card-echome.svg" width="100%" alt="Side project: ECHOME, local-first agent memory. Public repository."></a>

<a href="https://github.com/Lourdhu02/fin-sentinal.ai"><img src="assets/card-finsentinel.svg" width="100%" alt="Side project: FinSentinelAI, private document RAG. Public repository."></a>

<img src="assets/stack.svg" width="100%" alt="Stack. Modeling: PyTorch, YOLO OBB, OpenCV, NumPy, scikit-learn, Hugging Face. Inference: TensorRT, Triton, ONNX Runtime, TFLite, NGINX, Flask. Platform: AWS EC2, Lambda, S3, DynamoDB, Docker, Helm, Kubernetes. MLOps: DVC, uv, GitHub Actions, pytest, Ruff, pre-commit. GenAI: LangGraph, Ollama, Qdrant, ChromaDB, FastAPI, React.">

<img src="assets/experience.svg" width="100%" alt="Experience. Machine Learning Engineer, Sujanix, January 2026 to present. Founder, SpaceDrift, August 2024 to December 2025. Data Science Intern, BrainOvision Solutions, February to April 2024. Recognition: Kaggle Notebooks Expert; Machine Learning Specialization (DeepLearning.AI, Stanford); Data Science with Python (NPTEL, IIT Madras).">

<img src="assets/footer.svg" width="100%" alt="Open to ML engineering roles: production computer vision, inference optimization, applied GenAI. Email b.lourdhuraju1234@gmail.com, LinkedIn linkedin.com/in/lourdhu. Bengaluru, India.">

<div align="center">

<a href="https://www.linkedin.com/in/lourdhu"><img src="assets/btn-linkedin.svg" height="44" alt="LinkedIn"></a>&nbsp;
<a href="mailto:b.lourdhuraju1234@gmail.com"><img src="assets/btn-email.svg" height="44" alt="Email"></a>&nbsp;
<a href="https://www.kaggle.com/blourdhuraju"><img src="assets/btn-kaggle.svg" height="44" alt="Kaggle"></a>

<sub>Every card and 3D render on this page is generated from code in <a href="assets/_build">assets/_build</a>.</sub>

</div>
