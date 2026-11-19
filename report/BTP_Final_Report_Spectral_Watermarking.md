# A PROJECT REPORT ON
# SPECTRAL BAND ALLOCATION FOR INVISIBLE WATERMARKS UNDER VAE REGENERATION

**Submitted in partial fulfillment of the requirements for the award of the degree of**  
**Bachelor of Technology**  
*in*  
**Computer Science and Engineering**

**Submitted by:**  
**Viseash Ashley** (MIS: 112115123)

**Under the Supervision of:**  
**Dr. [Supervisor Name]**  
Department of Computer Science and Engineering  
**Indian Institute of Information Technology, Pune**  
*(An Institute of National Importance by an Act of Parliament)*  
**NOVEMBER 2026**

---

## BONAFIDE CERTIFICATE

This is to certify that the project report entitled **“Spectral Band Allocation for Invisible Watermarks Under VAE Regeneration”** submitted by **Viseash Ashley** (MIS No: 112115123) in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science and Engineering**, Indian Institute of Information Technology, Pune (IIIT Pune), during the academic year 2025–2026, is an authentic record of the work carried out under my supervision and guidance.

<br><br>
**Dr. [Supervisor Name]**  
Department of Computer Science and Engineering  
Indian Institute of Information Technology, Pune  

**Head of the Department**  
Department of Computer Science and Engineering  
Indian Institute of Information Technology, Pune  

**Project Viva-Voce Examination held on:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  

---

## UNDERTAKING FOR PLAGIARISM

I, **Viseash Ashley**, solemnly declare that the research work presented in the report entitled **“Spectral Band Allocation for Invisible Watermarks Under VAE Regeneration”** is solely my research work with no significant contribution from any other person. Small contribution/help wherever taken has been duly acknowledged and that the complete report has been written by me. I understand the zero tolerance policy of Indian Institute of Information Technology, Pune towards plagiarism. Therefore, I declare that no portion of my report has been plagiarized and any material used as reference is properly referred and cited. I undertake that if I am found guilty of any formal plagiarism in the above titled thesis even after award of the degree, the Institute reserves the right to withdraw or revoke my degree.

**Date:** 14-11-2026  
**Place:** Pune  
**Candidate:** Viseash Ashley (MIS: 112115123)

---

## AI ASSISTANCE & TOOLING DISCLOSURE

In compliance with academic integrity standards and institutional guidelines, the author discloses that artificial intelligence coding assistants were utilized during this project as technical development aids. Specifically, generative AI tools assisted in: (i) drafting Python orchestration scripts for batch evaluation, (ii) resolving environment and binary dependency conflicts in Google Colab, and (iii) document formatting automation. All conceptual problem formulations, mathematical modeling, experimental methodologies, dataset ingestion, quantitative analyses, and scientific conclusions were conceived, independently reviewed, and verified by the author.

---

## ABSTRACT

Invisible digital watermarking serves as a critical technological primitive for provenance tracking, copyright verification, and synthetic media authentication. However, deep generative pipelines—specifically Variational Autoencoders (VAEs) and Latent Diffusion Models (LDMs)—act as aggressive, non-standard attack vectors that can strip invisible watermarks while preserving perceptual visual fidelity. Prior digital watermarking literature has largely treated generative autoencoders as black-box neural networks, lacking an empirical frequency-domain characterisation of how watermarks degrade under regeneration.

This thesis formulates and experimentally investigates the hypothesis that generative VAE regeneration operates as a frequency-dependent degradation channel related to Wiener filtering. We partition the spatial frequency domain into 8 disjoint annular bands spanning radial frequencies from 0 to Nyquist (0.5 cyc/px). Across an empirical measurement campaign on the COCO dataset comprising 800 images (300 calibration images and 500 strictly held-out test images across 77,000 evaluations), this research establishes the following findings:

1. **Attack-Dependent Robust Spectral Windows:** The optimal watermarking band depends strongly on the specific attack architecture and severity. Under the Stable Diffusion VAE ($sd\text{-}vae\text{-}ft\text{-}mse$), which enforces $8\times$ spatial downsampling into a continuous latent space, Band 1 ($0.0625–0.125$ cyc/px) consistently outperforms all other bands across all tested pixel pre-noise levels ($\sigma \in [0.0, 0.20]$), achieving $75.15\%$ bit accuracy ($55.0\%$ TPR [$95\%$ CI: $50.6\%, 59.3\%$]) at $\sigma=0.0$ and $67.89\%$ ($26.6\%$ TPR) at $\sigma=0.20$, whereas Band 2 achieves $73.83\%$ ($49.8\%$ TPR) and $63.55\%$ ($12.8\%$ TPR). Under CompressAI neural compression, the optimal band dynamically shifts upward as quality increases, with Band 1 winning at $q=1$, Band 2 winning at $q=2–3$, Band 3 winning at $q=4–6$, Band 4 at $q=7$, and high frequencies passing through cleanly at $q=8$ (Band 7 reaches $100\%$ TPR). Bands 1 and 2 collectively form the robust operational window under aggressive regeneration.
2. **Quantitative Resolution of the Baseband Paradox:** We explain why baseband watermarking (Band 0, $0.0–0.0625$ cyc/px) fails despite suffering minimal low-pass attenuation. Zero-mean host cover variance in Band 0 ($\sigma_{\text{cover}, 0}^2 = 0.0474$) is $26.6\times$ ($14.2\text{ dB}$) higher than in Band 2 ($0.00178$), introducing severe host interference that caps unattacked decoding accuracy at $59.8\%$ and limits TPR to $\le 5.2\%$ across all attack conditions. Band 0 exhibits the highest SSIM ($0.984$) because smooth DC shifts minimally disturb local structural correlation, creating an inherent design tension: baseband embedding maximizes structural similarity but severely degrades detection SNR.
3. **Limits of Analytical Wiener Fits:** Factorized neural compression (CompressAI) conforms closely to an analytical Wiener gain model ($R^2 \in [0.928, 0.997]$), with effective noise $N_{\text{eff}}$ decreasing monotonically by approximately $44\times$ (from $2.41 \times 10^{-7}$ at $q=1$ to $5.52 \times 10^{-9}$ at $q=8$). However, the theoretical cutoff frequency $f_c$ under-predicts empirical cutoff by $5\%$ to $19\%$ at moderate qualities, and exceeds Nyquist at $q \ge 7$. For the Stable Diffusion VAE, the Wiener model fit is poor or negative ($R^2 \in [-2.45, 0.43]$) because latent spatial downsampling introduces non-monotonic, non-linear transfer responses that violate linear shift-invariance.
4. **Statistical Rigor and Inconclusive Learned Training:** On 500 unwatermarked test images, blind spread-spectrum decoding closely matches the theoretical null binomial distribution $B(32, 0.5)$ (mean score $16.10/32$), yielding an empirical false positive rate of $0.40\%$ (2/500, $95\%$ CI: [$0.11\%, 1.44\%$]) at detection threshold $\tau = 24/32$ bits, in close agreement with the analytical $0.35\%$ bound. Finally, we document that end-to-end learned watermarking architectures failed to converge during training, remaining near chance (~$49.8\%$ bit decoding accuracy for the dynamic model and $0.0\%$ TPR) even under unattacked identity conditions; this renders the experiment inconclusive regarding frequency-band allocation and linear Fourier surrogates, highlighting the necessity of progressive training curricula and carrier priors.

**Keywords:** Invisible Digital Watermarking, Variational Autoencoders (VAE), Spectral Band Allocation, Wiener Filter, Stable Diffusion, CompressAI, Host Interference, Fourier Analysis.

---

## TABLE OF CONTENTS

- Chapter 1: Introduction
  - 1.1 Background & Motivation
  - 1.2 Problem Statement
  - 1.3 Research Hypotheses & Scope of Evaluation
  - 1.4 Key Contributions & Report Organization
- Chapter 2: Literature Review & Theoretical Formulation
  - 2.1 Digital Watermarking: Classical vs. Deep Learning Approaches
  - 2.2 Generative Models and VAEs as Image Processing Attacks
  - 2.3 The Two-Forces Model: Host Interference vs. Low-Pass Attenuation
  - 2.4 Analytical Wiener Formulation & Power Spectrum Falloff
- Chapter 3: System Architecture & Proposed Methodology
  - 3.1 Orthonormal Annular Frequency Band Partitioning
  - 3.2 Empirical Transfer Function Measurement Protocol
  - 3.3 Classical Spread-Spectrum Watermarking Framework
  - 3.4 Learned Band-Allocation Architecture & Fourier Surrogate
- Chapter 4: Experimental Results & Discussion
  - 4.1 Experimental Setup & Evaluation Protocol ($N=500$)
  - 4.2 Natural Image Spectrum Fit & Wiener Model Characterisation
  - 4.3 Classical Parameter Sweep & Cutoff Tracking
  - 4.4 Full Held-Out Benchmark Analysis (77,000 Rows)
  - 4.5 Per-Band Perceptual Quality Analysis (PSNR/SSIM)
  - 4.6 Quantitative Host Interference Diagnosis (Why Band 0 Fails)
  - 4.7 Learned Band-Allocation Model: Negative Result Analysis
  - 4.8 Synthesis & Verification of Hypotheses
- Chapter 5: Conclusion & Future Scope
  - 5.1 Conclusion
  - 5.2 Threats to Validity & Limitations
  - 5.3 Future Research Directions
- References

---

# CHAPTER 1: INTRODUCTION

## 1.1 Background & Motivation
The rapid proliferation of deep generative computer vision models—including Variational Autoencoders (VAEs), Generative Adversarial Networks (GANs), and Latent Diffusion Models (LDMs)—has transformed digital content creation. Modern diffusion architectures, such as Stable Diffusion, synthesize high-resolution imagery with remarkable realism. However, this technology simultaneously introduces serious risks: non-consensual deepfakes, copyright infringement, and automated disinformation campaigns.

Digital watermarking is an established technical mechanism for copyright protection and provenance verification. By imperceptibly embedding cryptographic payloads into image data, content creators and platforms can trace synthetic media. While modern watermarks withstand conventional image processing operations—such as JPEG compression, additive noise, and blurring—they are vulnerable to generative autoencoder regeneration. In regeneration attacks, an image is passed through an encoder-decoder pipeline: $\hat{x} = D(E(x_w))$. This process purges high-frequency watermarks while preserving visual fidelity. Understanding the spectral mechanics of this degradation channel is critical for developing resilient watermarking strategies.

## 1.2 Problem Statement
Given an original cover image $x \in [0, 1]^{3 \times H \times W}$ and a binary payload $m \in \{0, 1\}^L$, we seek to embed $m$ into $x$ to produce a watermarked image $x_w$ satisfying two criteria:
1. Strict perceptual imperceptibility, evaluated by Peak Signal-to-Noise Ratio (target PSNR = 40.0 dB, empirical mean = 40.06 dB) and Structural Similarity Index (SSIM $\ge 0.95$).
2. Survival against downstream regeneration $\hat{x} = A(x_w)$.

The central research question is: **How does autoencoder regeneration alter watermark energy across spatial frequency bands, and can frequency band allocation improve watermark robustness?**

## 1.3 Research Hypotheses & Scope of Evaluation
This thesis investigates three research hypotheses:

- **Hypothesis H1 (Wiener Transfer Equivalence):** The energy transfer function $H(f) = \sqrt{E_{\text{out}}(f) / E_{\text{in}}(f)}$ of an autoencoder can be modeled by a Wiener gain $G(f) = P(f) / (P(f) + N_{\text{eff}})$, where $P(f) = A f^{-\alpha}$ represents the natural image power spectrum, and effective noise $N_{\text{eff}}$ scales with attack severity.
- **Hypothesis H2 (Cutoff Tracking):** The boundary separating watermark survival from degradation aligns with the analytical Wiener cutoff frequency $f_c = (A / N_{\text{eff}})^{1/\alpha}$, shifting upward as reconstruction fidelity improves.
- **Hypothesis H3 (Annular Robustness Window):** High-frequency bands degrade under low-pass attenuation, while baseband Band 0 degrades under host cover-image interference. Consequently, intermediate frequency bands (Bands 1–2) provide a superior balance between low-pass survival and low host interference.

**Scope of Evaluation:** This report evaluates these hypotheses across 800 photographic images from COCO 2017: 300 calibration images for transfer function characterisation and parameter sweeping (144,000 evaluations), and 500 strictly held-out test images for the final benchmark (77,000 evaluations) across Stable Diffusion VAE (6 pixel pre-noise levels) and CompressAI (8 quality levels).

## 1.4 Key Contributions & Report Organization
1. **Analytical Wiener Characterisation:** We fit natural photographic spectra ($\alpha=2.660$) and demonstrate that CompressAI follows Wiener filtering ($R^2 \in [0.928, 0.997]$), while Stable Diffusion VAE exhibits non-linear latent transfer dynamics violating linear shift-invariance.
2. **Host Interference Analysis:** We demonstrate analytically and empirically that Band 0 failure is driven by host interference (zero-mean cover variance $26.6\times$ / $14.2\text{ dB}$ higher than Band 2).
3. **Large-Scale Held-Out Benchmark ($N=500$, 77k Rows):** Rigorous empirical validation with Wilson 95% confidence intervals and verified binomial null behavior.
4. **Perceptual Quality Benchmarking:** Objective evaluation showing that Band 2 achieves 40.06 dB PSNR and SSIM > 0.963.
5. **Empirical Negative Result on End-to-End Learned Watermarking:** We document that under a strict 40.0 dB PSNR budget, a compact 7-layer CNN trained without carrier priors or progressive curriculum failed to converge even on the identity channel (hovering near chance accuracy, ~49.8% for the dynamic surrogate network and 0.0% TPR). This experiment is inconclusive regarding the efficacy of differentiable Fourier surrogates, highlighting that future investigations require multi-stage curricula and matched-filter priors.

---

# CHAPTER 2: LITERATURE REVIEW & THEORETICAL FORMULATION

## 2.1 Digital Watermarking: Classical vs. Deep Learning Approaches
Digital watermarking techniques historically partition into spatial-domain and transform-domain approaches. Spatial-domain methods fail under lossy compression. Transform-domain techniques (DCT, DWT, DFT) embed watermark energy into mid-frequency coefficients to survive classical low-pass filtering. Spread-spectrum watermarking, introduced by Cox et al. [1], modulates pseudorandom sequence vectors across frequency bands, achieving robustness against additive noise through correlation despreading.

End-to-end deep learning architectures (e.g., HiDDeN [2], StegaStamp [3], TrustMark [4]) employ convolutional encoder-decoder pipelines trained adversarially against differentiable distortion layers. However, deep watermarking models remain vulnerable to out-of-distribution neural distortions, particularly generative autoencoders.

## 2.2 Generative Models and VAEs as Image Processing Attacks
The vulnerability of invisible watermarks to generative image regeneration was highlighted by Zhao et al. [5] and Lu et al. [6]. Unlike classical signal degradations, generative autoencoders map images into continuous latent representations $z = E(x)$ and reconstruct them using decoder networks $\hat{x} = D(z)$. In Latent Diffusion Models (LDMs) such as Stable Diffusion [7], the autoencoder enforces an $8\times$ spatial downsampling factor (mapping $256\times 256$ RGB images to $32\times 32\times 4$ latent tensors), regularized by a Kullback-Leibler (KL) divergence penalty to a standard Gaussian prior. Importantly, the SD-VAE employs continuous latent distributions rather than discrete codebook quantization [8]. In our evaluations, the attack parameter $\sigma$ denotes additive Gaussian pre-noise applied directly to the pixel image prior to encoding: $x_{\text{noisy}} = \text{clamp}(x + \mathcal{N}(0, \sigma^2), 0, 1)$, testing the autoencoder's denoising and reconstruction behavior.

## 2.3 The Two-Forces Model: Host Interference vs. Low-Pass Attenuation
When decoded via correlation filtering, the decision statistic for a single bit payload is governed by the signal-to-interference-plus-noise ratio (SINR):

$$\text{SINR}(b) = \frac{E_{\text{wm}}(b) \cdot |H(b)|^2}{P_{\text{cover}}(b) \cdot |H(b)|^2 + \sigma_{\text{noise}}^2(b)}$$

where $E_{\text{wm}}(b)$ is watermark power, $P_{\text{cover}}(b)$ is host image variance within band $b$, $H(b)$ is the channel transfer gain, and $\sigma_{\text{noise}}^2(b)$ represents the autoencoder's residual reconstruction noise and latent distortion floor within the band. Because $|H(b)|$ multiplies both the signal and host components, channel low-pass attenuation only impacts the detection statistic when the attenuated signal $E_{\text{wm}}(b)|H(b)|^2$ drops toward or below the additive reconstruction noise floor $\sigma_{\text{noise}}^2(b)$.

Two physical forces govern detection accuracy:
1. **Force 1: Host Cover Interference (Destroys Low Frequencies):** Natural photographic scenes exhibit a steep power-law spectral density $P_{\text{cover}}(f) \propto f^{-\alpha}$ [9]. In baseband Band 0, zero-mean host cover variance ($\sigma_{\text{cover}, 0}^2 = 0.0474$) is $26.6\times$ ($14.2\text{ dB}$) higher than in Band 2 ($0.00178$), creating severe self-interference that overwhelms watermark detection.
2. **Force 2: VAE Low-Pass Attenuation (Destroys High Frequencies):** Autoencoder spatial bottlenecks attenuate high spatial frequencies ($H(f) \to 0$ as $f \to 0.5$), degrading watermark signals in Bands 4–7 under aggressive compression as the signal drops below $\sigma_{\text{noise}}^2(b)$.

This creates an inherent trade-off. Robust watermarking under aggressive regeneration requires operating in the intermediate spectral window—primarily Bands 1 and 2—where host power has decayed substantially while transfer gain remains sufficient.

---

# CHAPTER 3: SYSTEM ARCHITECTURE & PROPOSED METHODOLOGY

## 3.1 Orthonormal Annular Frequency Band Partitioning
We establish an orthonormal Fourier partitioning that divides the centered 2D spatial frequency plane into 8 disjoint concentric annular bands spanning radial frequencies from 0 to Nyquist ($f_{\text{Nyq}} = 0.5$ cycles/pixel).

Each annular band mask $M_b(u, v)$ is defined over normalized radial frequencies $r = \frac{\sqrt{u^2 + v^2}}{N}$ as:
$$M_b(u, v) = \begin{cases} 1 & \text{if } r \in [b \cdot 0.0625, (b + 1) \cdot 0.0625) \\ 0 & \text{otherwise} \end{cases}$$

## 3.2 Classical Spread-Spectrum Watermarking Framework
The classical baseline embeds a 32-bit pseudorandom payload $m \in \{0, 1\}^{32}$ using antipodal spread-spectrum modulation:

$$\delta x = \gamma \sum_{k=1}^{32} (2 m_k - 1) \cdot \mathcal{F}^{-1}\left( \mathcal{F}(c_k) \odot M_b \right)$$

where $\gamma$ is an amplitude scaling factor calibrated to meet the exact target PSNR (40.0 dB), and $c_k$ represents the pseudo-random carrier sequence for bit $k$.

Decoding is blind. The attacked image $\hat{x}$ is projected onto band $M_b$, and normalized inner products with carrier $c_k$ determine detected bits.

---

# CHAPTER 4: EXPERIMENTAL RESULTS & DISCUSSION

## 4.1 Experimental Setup & Evaluation Protocol ($N=500$)
- **Images:** 800 COCO 2017 images [10] (300 calibration images, 500 strictly held-out unseen test images).
- **Target Fidelity:** strictly calibrated at target PSNR = 40.0 dB (empirical mean = 40.06 dB) across all bands.
- **Attacks:** SD-VAE (6 pixel pre-noise levels $\sigma \in [0.0, 0.20]$) and CompressAI $bmshj2018$ (Ballé et al. [11], 8 quality levels $q \in [1, 8]$).
- **Detection Threshold:** $\tau = 24/32$ bits ($75.0\%$), corresponding to analytical $\text{FPR} = 0.35\%$.
- **Statistical Rigor:** All detection rates report exact Wilson 95% score confidence intervals [12].

## 4.2 Analytical Wiener Model Characterisation

| Attack Family | Strength | Fitted $N_{\text{eff}}$ | $R^2$ Score | RMSE | Pred $f_c$ (cyc/px) | Meas $f_c$ (cyc/px) | $f_c$ Prediction Error (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| CompressAI | $q = 1$ | $2.41 \times 10^{-7}$ | **0.992** | 0.043 | 0.160 | 0.198 | -19.2% |
| CompressAI | $q = 2$ | $1.40 \times 10^{-7}$ | **0.983** | 0.058 | 0.196 | 0.228 | -14.0% |
| CompressAI | $q = 3$ | $8.63 \times 10^{-8}$ | **0.963** | 0.078 | 0.235 | 0.261 | -10.0% |
| CompressAI | $q = 4$ | $5.35 \times 10^{-8}$ | **0.948** | 0.082 | 0.281 | 0.304 | -7.6% |
| CompressAI | $q = 5$ | $3.51 \times 10^{-8}$ | **0.928** | 0.085 | 0.330 | 0.349 | -5.4% |
| CompressAI | $q = 6$ | $1.76 \times 10^{-8}$ | **0.947** | 0.049 | 0.428 | 0.425 | +0.7% |
| CompressAI | $q = 7$ | $9.89 \times 10^{-9}$ | **0.988** | 0.016 | 0.531* | 0.469 | N/A (Exceeds Nyquist) |
| CompressAI | $q = 8$ | $5.52 \times 10^{-9}$ | **0.997** | 0.005 | 0.661* | 0.469 | N/A (Exceeds Nyquist) |
| SD VAE | $\sigma = 0.00$ | $1.21 \times 10^{-9}$ | -0.396 | 0.044 | 1.168* | 0.469 | N/A (Out of domain) |
| SD VAE | $\sigma = 0.02$ | $1.24 \times 10^{-9}$ | 0.433 | 0.016 | 1.157* | 0.469 | N/A (Out of domain) |
| SD VAE | $\sigma = 0.05$ | $1.00 \times 10^{-9}$ | -2.447 | 0.082 | 1.254* | 0.469 | N/A (Out of domain) |
| SD VAE | $\sigma = 0.10$ | $1.63 \times 10^{-9}$ | -2.089 | 0.211 | 1.044* | 0.469 | N/A (Out of domain) |
| SD VAE | $\sigma = 0.15$ | $2.46 \times 10^{-9}$ | -2.209 | 0.284 | 0.895* | 0.469 | N/A (Out of domain) |
| SD VAE | $\sigma = 0.20$ | $3.11 \times 10^{-9}$ | -2.374 | 0.296 | 0.820* | 0.469 | N/A (Out of domain) |

**Discussion:** The analytical Wiener model achieves high goodness of fit for CompressAI ($R^2 \in [0.928, 0.997]$ across $q \in [1, 8]$). The theoretical cutoff $f_c$ under-predicts the measured cutoff by $5.4\%$ to $19.2\%$ for $q \in [1, 5]$. At $q=7, 8$, the predicted cutoff exceeds the spatial Nyquist frequency ($0.531$ and $0.661$ cyc/px) while the measured value is capped at the highest band center ($0.469$ cyc/px). For Stable Diffusion VAE, the Wiener model fit is poor or negative ($R^2 \in [-2.45, 0.43]$), yielding unphysical predicted cutoffs above $0.8$ cyc/px. This confirms that latent autoencoders introduce non-monotonic transfer behaviors that violate linear shift-invariance. Natural image power spectra were fitted according to Ruderman's power law [9] ($\alpha = 2.660$).

## 4.3 Definition of Optimal Band
We define the optimal frequency band for a given attack condition as the band achieving the highest mean bit decoding accuracy across the 500 test images. In the event of saturation where multiple bands reach 100% True Positive Rate, ties are broken by highest mean bit accuracy. Under Stable Diffusion VAE, Band 1 is optimal across all tested $\sigma$ levels.

## 4.4 Full Held-Out Benchmark Tables ($N=500$, 77,000 Rows)

### Table 4.2: Robustness Under Stable Diffusion VAE Across All 8 Bands ($N=500$, Target PSNR = 40.0 dB, Mean = 40.06 dB)
| Watermarking Band | Metric | $\sigma = 0.00$ | $\sigma = 0.02$ | $\sigma = 0.05$ | $\sigma = 0.10$ | $\sigma = 0.15$ | $\sigma = 0.20$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Band 0** | Bit Acc (%)<br>TPR [95% CI] | 57.93%<br>3.0% [1.8, 4.9] | 57.69%<br>2.6% [1.5, 4.4] | 57.61%<br>2.0% [1.1, 3.6] | 57.47%<br>2.4% [1.4, 4.1] | 57.39%<br>2.6% [1.5, 4.4] | 57.49%<br>2.8% [1.7, 4.6] |
| **Band 1 (Optimal)**| Bit Acc (%)<br>TPR [95% CI] | 75.15%<br>**55.0%** [50.6, 59.3] | 73.72%<br>**52.0%** [47.6, 56.3] | 70.81%<br>**40.0%** [35.8, 44.4] | 68.80%<br>**32.8%** [28.8, 37.0] | 68.04%<br>**27.6%** [23.9, 31.7] | 67.89%<br>**26.6%** [22.9, 30.6] |
| **Band 2** | Bit Acc (%)<br>TPR [95% CI] | 73.83%<br>49.8% [45.4, 54.2] | 72.12%<br>42.6% [38.3, 47.0] | 68.64%<br>30.8% [26.9, 35.0] | 65.69%<br>19.4% [16.2, 23.1] | 64.74%<br>14.8% [12.0, 18.2] | 63.55%<br>12.8% [10.2, 16.0] |
| **Band 3** | Bit Acc (%)<br>TPR [95% CI] | 66.83%<br>25.4% [21.8, 29.4] | 63.89%<br>16.8% [13.8, 20.3] | 61.49%<br>9.0% [6.8, 11.9] | 59.66%<br>4.2% [2.7, 6.4] | 58.27%<br>3.6% [2.2, 5.6] | 57.04%<br>2.2% [1.2, 3.9] |
| **Band 4** | Bit Acc (%)<br>TPR [95% CI] | 58.98%<br>5.6% [3.9, 8.0] | 58.46%<br>4.2% [2.7, 6.4] | 57.40%<br>3.8% [2.4, 5.9] | 55.44%<br>1.4% [0.7, 2.9] | 53.93%<br>1.0% [0.4, 2.3] | 53.67%<br>0.4% [0.1, 1.4] |
| **Band 5** | Bit Acc (%)<br>TPR [95% CI] | 55.17%<br>1.8% [0.9, 3.4] | 54.64%<br>1.6% [0.8, 3.1] | 53.62%<br>1.0% [0.4, 2.3] | 51.36%<br>1.4% [0.7, 2.9] | 51.01%<br>1.0% [0.4, 2.3] | 50.50%<br>0.8% [0.3, 2.0] |
| **Band 6** | Bit Acc (%)<br>TPR [95% CI] | 53.64%<br>1.0% [0.4, 2.3] | 52.79%<br>1.0% [0.4, 2.3] | 52.09%<br>0.8% [0.3, 2.0] | 50.44%<br>0.8% [0.3, 2.0] | 49.00%<br>0.0% [0.0, 0.7] | 49.24%<br>0.0% [0.0, 0.7] |
| **Band 7** | Bit Acc (%)<br>TPR [95% CI] | 51.21%<br>0.8% [0.3, 2.0] | 51.58%<br>0.2% [0.0, 1.1] | 50.82%<br>0.4% [0.1, 1.4] | 50.50%<br>0.4% [0.1, 1.4] | 49.93%<br>0.0% [0.0, 0.7] | 49.18%<br>0.2% [0.0, 1.1] |

**Observation on Table 4.2:** Band 1 strictly outperforms Band 2 across all noise strengths $\sigma$ under SD-VAE (TPR $55.0\%$ vs. $49.8\%$ at $\sigma=0.00$, and $26.6\%$ vs. $12.8\%$ at $\sigma=0.20$). The 95% confidence intervals do not overlap for $\sigma \ge 0.02$. This occurs because the aggressive spatial bottleneck of SD-VAE penalizes Band 2 attenuation more heavily than the host interference penalty of Band 1. Bands 1 and 2 collectively form the survivable low-frequency window.

### Table 4.3: Robustness Under CompressAI Across All 8 Bands ($N=500$, Target PSNR = 40.0 dB, Mean = 40.06 dB)
| Band | Metric | $q=1$ | $q=2$ | $q=3$ | $q=4$ | $q=5$ | $q=6$ | $q=7$ | $q=8$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Band 0** | Bit Acc (%)<br>TPR (%) | 57.31%<br>2.8% | 57.88%<br>3.0% | 58.61%<br>4.0% | 58.83%<br>4.0% | 59.16%<br>4.4% | 59.41%<br>5.0% | 59.56%<br>5.0% | 59.60%<br>5.2% |
| **Band 1** | Bit Acc (%)<br>TPR (%) | 67.81%<br>**29.4%**\* | 72.85%<br>48.4% | 78.64%<br>72.8% | 83.35%<br>85.6% | 86.80%<br>94.6% | 89.11%<br>97.8% | 90.37%<br>98.4% | 90.96%<br>98.6% |
| **Band 2** | Bit Acc (%)<br>TPR (%) | 65.04%<br>18.4% | 73.29%<br>**50.0%**\* | 80.79%<br>**78.6%**\* | 87.30%<br>92.0% | 93.83%<br>99.2% | 96.88%<br>99.8% | 98.40%<br>100.0% | 98.77%<br>100.0% |
| **Band 3** | Bit Acc (%)<br>TPR (%) | 58.17%<br>3.2% | 65.62%<br>20.0% | 77.26%<br>63.0% | 87.52%<br>**89.0%**\* | 94.37%<br>**98.0%**\* | 97.92%<br>**99.6%**\* | 99.56%<br>100.0% | 99.79%<br>100.0% |
| **Band 4** | Bit Acc (%)<br>TPR (%) | 55.28%<br>1.2% | 59.21%<br>4.6% | 67.39%<br>27.0% | 81.47%<br>77.6% | 92.88%<br>95.6% | 97.48%<br>98.8% | 99.78%<br>**100.0%**\* | 99.96%<br>100.0% |
| **Band 5** | Bit Acc (%)<br>TPR (%) | 51.37%<br>0.2% | 54.20%<br>0.2% | 59.75%<br>5.8% | 70.58%<br>40.4% | 86.90%<br>87.8% | 97.14%<br>98.4% | 99.73%<br>99.8% | 99.98%<br>100.0% |
| **Band 6** | Bit Acc (%)<br>TPR (%) | 50.59%<br>0.4% | 51.61%<br>1.4% | 53.85%<br>1.0% | 61.37%<br>8.4% | 72.72%<br>49.8% | 93.97%<br>95.0% | 99.36%<br>99.6% | 99.97%<br>100.0% |
| **Band 7** | Bit Acc (%)<br>TPR (%) | 50.17%<br>0.2% | 50.26%<br>0.4% | 51.12%<br>1.0% | 54.34%<br>0.6% | 60.69%<br>7.8% | 81.29%<br>75.4% | 97.31%<br>99.0% | 100.0%<br>**100.0%**\* |

**Observation on Table 4.3:** Asterisks (\*) denote the optimal band per quality level. The optimal band shifts systematically from Band 1 ($q=1$) to Band 2 ($q=2, 3$), Band 3 ($q=4, 5, 6$), Band 4 ($q=7$), and Band 7 ($q=8$). Crucially, the assertion that "Bands 4–7 collapse" holds only under aggressive compression ($q \le 3$). At higher qualities ($q \ge 6$), high-frequency details are preserved, with Band 7 achieving $97.31\%$ bit accuracy ($99.0\%$ TPR) at $q=7$ and $100.0\%$ bit accuracy ($100.0\%$ TPR) at $q=8$. From $q \ge 4$ upward, differences among adjacent active bands are small (frequently within 1 percentage point).

## 4.5 False Positive Rate & Empirical Null Distribution
Under the analytical null distribution $B(32, 0.5)$, the probability of randomly achieving $\ge 24$ matching bits is $P(X \ge 24) = 0.003506$ ($0.35\%$). Evaluating 500 actual unwatermarked images through the spread-spectrum decoder yielded a mean score of $16.10 / 32$ bits (std = $2.78$) and exactly 2 false alarms out of 500 trials, giving an empirical FPR of $0.40\%$ (95% Wilson CI: [$0.11\%, 1.44\%$]), in close agreement with the theoretical bound.

## 4.6 Perceptual Quality Analysis & The SSIM Paradox

| Band Index | Radial Frequency Range (cyc/px) | Band Center (cyc/px) | Empirical PSNR (dB) | Structural Similarity (SSIM) |
| :--- | :---: | :---: | :---: | :---: |
| Band 0 | $[0.0000, 0.0625)$ | 0.03125 | 40.059 dB | **0.9842** |
| Band 1 | $[0.0625, 0.1250)$ | 0.09375 | 40.057 dB | 0.9685 |
| Band 2 | $[0.1250, 0.1875)$ | 0.15625 | 40.058 dB | 0.9631 |
| Band 3 | $[0.1875, 0.2500)$ | 0.21875 | 40.059 dB | 0.9632 |
| Band 4 | $[0.2500, 0.3125)$ | 0.28125 | 40.061 dB | 0.9626 |
| Band 5 | $[0.3125, 0.3750)$ | 0.34375 | 40.060 dB | 0.9626 |
| Band 6 | $[0.3750, 0.4375)$ | 0.40625 | 40.062 dB | 0.9625 |
| Band 7 | $[0.4375, 0.5000)$ | 0.46875 | 40.063 dB | 0.9625 |

**The SSIM Paradox:** Band 0 exhibits the highest structural similarity (SSIM = $0.9842$), compared to $0.9631$ in Band 2. This occurs because SSIM computes structural correlation over local $11\times 11$ Gaussian windows; low-frequency energy corresponds to smooth, nearly constant luminance shifts that leave local cross-correlations virtually undisturbed. However, this high perceptual fidelity in Band 0 is coupled with severe detection degradation. Zero-mean host cover variance in Band 0 is $\sigma_{\text{cover}, 0}^2 = 0.0474$, whereas in Band 2 it is $\sigma_{\text{cover}, 2}^2 = 0.00178$ ($26.6\times$ lower), and in Band 7 it is $0.000255$ ($186\times$ lower). At 40.0 dB PSNR, watermark energy is $\sigma_{\text{wm}}^2 = 1.00 \times 10^{-4}$. In Band 0, the raw signal-to-interference ratio before correlation is $\text{SIR}_0 = 1.0\text{e-}4 / 0.0474 = -26.8$ dB. In Band 2, the raw ratio is $\text{SIR}_2 = 1.0\text{e-}4 / 0.00178 = -12.5$ dB—a 14.3 dB advantage. Consequently, despreading correlation gain is sufficient to decode Band 2 reliably ($98.9\%$ unattacked accuracy), whereas Band 0 decoding is corrupted by host energy ($59.8\%$ unattacked accuracy).

## 4.7 Learned Band-Allocation Model: Negative Result Analysis
Four learned watermarking models were trained: three fixed-regime control networks (Low: Bands 0–2, Mid: Bands 3–5, High: Bands 6–7) and a dynamic model employing a learnable frequency-band allocation layer trained against a differentiable Fourier surrogate filter $G(f)$. 

When evaluated on a pilot test set of 64 images across 14 attack conditions (896 evaluations per model), the learned models failed to establish robust payload transmission:
- The dynamic surrogate network achieved an overall mean bit decoding accuracy of $49.83\% \pm 8.49\%$ (SD-VAE $\sigma=0.0$: $49.95\% \pm 8.43\%$; CompressAI $q=8$: $49.90\% \pm 8.44\%$) and $0.0\%$ True Positive Rate at the $\tau = 24/32$ threshold.
- The mid-band control network reached an overall mean bit accuracy of $49.36\% \pm 8.51\%$ ($0.0\%$ TPR).
- The high-band control network achieved $52.18\% \pm 8.31\%$ mean bit accuracy ($0.78\%$ TPR under SD-VAE, $0.0\%$ under CompressAI).
- The low-band control network achieved $58.68\% \pm 12.11\%$ overall bit accuracy, remaining near chance under SD-VAE ($55.76\%$ bit accuracy, $2.08\%$ TPR at $\sigma=0.0$) but reaching $77.10\%$ bit accuracy ($22.85\%$ TPR) under mild compression (CompressAI $q=8$).

All learned models stayed at chance even with no attack (identity channel accuracy remained near $50\%$), so training did not converge and this experiment is inconclusive about band allocation and Fourier surrogates. Likely contributing factors (untested in this study) include:
1. **Very Low Perturbation Budget at 40 dB:** Enforcing a 40 dB target PSNR constrains watermark RMS to $0.01$, which corresponds to an average shift of only $\approx 2.55$ intensity levels on an 8-bit scale $[0, 255]$.
2. **Aggressive Training Curriculum:** The training schedule switched from identity passthrough to noise after only 3 epochs in a 30-epoch budget, introducing distortion before the identity channel converged.
3. **Blind Decoding Without Carrier Priors:** The decoder was an unguided 7-layer CNN with global average pooling tasked with extracting 32 arbitrary bits from natural textures without a shared carrier key or matched-filter prior.

Under the same 40 dB constraint, the classical spread-spectrum watermark, which has a shared pseudo-random key and matched-filter decoding, did decode reliably under mild regeneration (e.g., $100\%$ TPR at CompressAI $q=8$, and $55.0\%$ TPR at SD-VAE $\sigma=0.0$, though SD-VAE remains a very challenging attack even for the classical method where peak accuracy caps at $75.15\%$). The theoretical processing gain ($G_{\text{proc}} \approx 10 \log_{10}(256^2 / 32) \approx 33.1\text{ dB}$) represents an upper bound on degrees of freedom for full-image carriers, whereas annular band-filtering restricts spatial degrees of freedom.

## 4.8 Synthesis & Verification of Hypotheses
- **Hypothesis H1 (Wiener Transfer Equivalence): PARTIALLY SUPPORTED.** Supported with high precision on CompressAI ($R^2 \in [0.928, 0.997]$), where effective noise $N_{\text{eff}}$ scales monotonically. Refuted on Stable Diffusion VAE (poor or negative $R^2$), where $8\times$ latent spatial downsampling introduces non-monotonic, non-linear frequency responses.
- **Hypothesis H2 (Cutoff Tracking): PARTIALLY SUPPORTED.** The survival boundary (where watermark accuracy remains above the collapse floor) aligns with the analytical Wiener cutoff frequency $f_c$ (e.g., at $q=6$, $f_c = 0.428$ cyc/px in Band 6, where Band 6 achieves $94.0\%$ bit accuracy and Band 7 drops to $81.3\%$). However, the *optimal* band lags below $f_c$ (optimal at Band 3 at $q=6$, though from $q \ge 4$ upward, differences among neighboring active bands are small, within ~1 percentage point), reflecting the two-forces trade-off between transfer gain and host interference. Predicted cutoffs under-predict empirical cutoffs by $5\%–19\%$ for $q \in [1, 5]$ and exceed Nyquist for $q \ge 7$.
- **Hypothesis H3 (Annular Robustness Window): PARTIALLY SUPPORTED.** The claim that Band 2 is universally optimal is contradicted by the data. Under SD-VAE, Band 1 strictly outperforms Band 2 across all noise levels (TPR $55.0\%$ vs. $49.8\%$ at $\sigma=0.0$). Under CompressAI, higher bands outperform Band 2 at high qualities ($q \ge 4$). Bands 1 and 2 collectively form the robust operational window under aggressive regeneration, with the specific optimum depending on the attack architecture.

---

# CHAPTER 5: CONCLUSION & FUTURE SCOPE

## 5.1 Conclusion
1. **Transfer Mechanics Depend on Architecture:** Factorized neural compression conforms closely to analytical Wiener filtering ($R^2$ up to $0.997$), whereas continuous latent autoencoders (SD-VAE) violate linear shift-invariance due to spatial downsampling.
2. **Host Interference Constrains Baseband:** Band 0 watermarking fails due to high host cover variance ($26.6\times$ / $14.2\text{ dB}$ higher than Band 2), despite achieving the highest structural similarity (SSIM = $0.984$). Low frequencies represent a fundamental trade-off between structural preservation and detection SNR.
3. **Attack-Dependent Robust Windows:** Under aggressive regeneration (SD-VAE), Bands 1 and 2 form the robust operational window, with Band 1 providing the highest TPR ($55.0\%$ at $\sigma=0.0$). Under variable-rate compression, optimal bands shift dynamically toward higher frequencies.
4. **Inconclusive Learned Model Training:** Under a strict 40 dB PSNR budget, a compact 7-layer CNN trained without carrier priors or progressive curriculum failed to converge even on the identity channel (hovering near chance accuracy, ~49.8% for the dynamic surrogate network and 0.0% TPR). Consequently, this experiment remains inconclusive regarding the efficacy of differentiable Fourier surrogates, highlighting that future investigations require multi-stage curricula and matched-filter priors.

## 5.2 Threats to Validity & Limitations
1. **Domain Specificity:** Natural photographic images follow a $1/f^{2.66}$ power law [9]. Synthetic artwork, diagrams, or cartoons possess different spectral characteristics that will shift the interference landscape.
2. **Payload Capacity:** Evaluated on a fixed 32-bit payload. Higher capacities reduce per-bit correlation gain, altering threshold behavior.
3. **Geometric Synchronization:** The spread-spectrum scheme requires spatial alignment; rotational or cropping attacks require pre-registration.

## 5.3 Future Research Directions
1. **Progressive Curriculum for Learned Watermarking:** To prevent optimization stalls at 40 dB, training should initialize at higher perturbation budgets (e.g., 30 dB PSNR) until the identity channel reaches >98% accuracy, before annealing to strict imperceptibility.
2. **Carrier-Conditioned Decoding:** Providing learned decoders with structured carrier priors or matched-filter projections rather than forcing blind extraction from scratch.
3. **Direct Latent Watermarking:** Injecting watermarks directly into the continuous latent space of diffusion autoencoders.
4. **Adaptive Frequency Allocation:** Dynamic bit allocation that analyzes local image spectra to embed energy into bands with minimal host interference.

---

# REFERENCES

1. I. J. Cox, J. Kilian, F. T. Leighton, and T. Shamoon, “Secure spread spectrum watermarking for multimedia,” *IEEE Transactions on Image Processing*, vol. 6, no. 12, pp. 1673–1687, 1997.
2. J. Zhu, R. Kaplan, A. Johnson, and L. Fei-Fei, “HiDDeN: Hiding images with deep networks,” in *Proceedings of the European Conference on Computer Vision (ECCV)*, 2018, pp. 657–672.
3. M. Tancik, B. Mildenhall, and R. Ng, “StegaStamp: Invisible hyperlinks in physical photographs,” in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2020, pp. 2117–2126.
4. T. Bui, S. Agarwal, and J. Collomosse, “TrustMark: Universal watermarking for arbitrary resolution images,” *arXiv preprint arXiv:2311.18297*, 2023.
5. X. Zhao, K. Zhang, H. Su, S. Zhang, and X. Hu, “Invisible image watermarks are provably removable using generative AI,” in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 37, 2024, arXiv:2306.01953.
6. S. Lu, Z. Ren, Y. Ding, and M. Sun, “Robust watermarking using generative priors against image editing: From benchmarking to advances,” in *International Conference on Learning Representations (ICLR)*, 2025, arXiv:2410.18775.
7. R. Rombach, A. Blattmann, D. Lorenz, P. Esser, and B. Ommer, “High-resolution image synthesis with latent diffusion models,” in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2022, pp. 10684–10695.
8. A. van den Oord, O. Vinyals, and K. Kavukcuoglu, “Neural discrete representation learning,” in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017.
9. D. L. Ruderman, “The statistics of natural images,” *Network: Computation in Neural Systems*, vol. 5, no. 4, pp. 517–548, 1994.
10. T. Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Dollár, and C. L. Zitnick, “Microsoft COCO: Common objects in context,” in *European Conference on Computer Vision (ECCV)*, 2014, pp. 740–755.
11. J. Ballé, D. Minnen, S. Singh, S. J. Hwang, and N. Johnston, “Variational image compression with a scale hyperprior,” in *International Conference on Learning Representations (ICLR)*, 2018.
12. E. B. Wilson, “Probable inference, the law of succession, and statistical inference,” *Journal of the American Statistical Association*, vol. 22, no. 158, pp. 209–212, 1927.
