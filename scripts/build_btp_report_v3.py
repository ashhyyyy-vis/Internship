"""
scripts/build_btp_report_v3.py - Fully corrected, academically rigorous BTP Project Report
in .docx format conforming strictly to IIIT Pune guidelines and address all critique points.
"""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

DOCX_OUT = Path("BTP_Final_Report_Spectral_Watermarking.docx")

doc = Document()

# Page Setup: Standard A4 margins (Left: 1.25", Top/Right/Bottom: 1.0")
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1.0)

# Base Style: Times New Roman, 12pt, 1.15 line spacing, 6pt space after
normal_style = doc.styles['Normal']
normal_style.font.name = 'Times New Roman'
normal_style.font.size = Pt(12)
normal_style.font.color.rgb = RGBColor(0, 0, 0)
normal_style.paragraph_format.line_spacing = 1.15
normal_style.paragraph_format.space_after = Pt(6)


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def add_title_p(text, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.bold = bold
    return p


def add_heading_1(text):
    """Chapter heading: 16pt, Bold, Centered, ALL CAPS."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text.upper())
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.bold = True
    return p


def add_heading_2(text):
    """Section heading: 14pt, Bold, Left-aligned."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    return p


def add_heading_3(text):
    """Subsection heading: 12pt, Bold, Left-aligned."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = True
    return p


def add_body_p(text, bold_prefix=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(6)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.bold = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    return p


def add_figure(img_path, caption, width_in=5.8):
    path_obj = Path(img_path)
    if path_obj.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        doc.add_picture(str(path_obj), width=Inches(width_in))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r = p_cap.add_run(caption)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10.0)
        r.italic = True
    else:
        print(f"Warning: Figure {img_path} not found.")


print("[build_report_v3] Generating corrected BTP Project Report...")

# ==========================================
# 1. TITLE PAGE
# ==========================================
add_title_p("A PROJECT REPORT ON", size=14, bold=True, space_after=8)
add_title_p("SPECTRAL BAND ALLOCATION FOR INVISIBLE WATERMARKS UNDER VAE REGENERATION", size=18, bold=True, space_after=18)

add_title_p("Submitted in partial fulfillment of the requirements for the award of the degree of", size=12, bold=False, space_after=4)
add_title_p("Bachelor of Technology", size=14, bold=True, space_after=2)
add_title_p("in", size=12, bold=False, space_after=2)
add_title_p("Computer Science and Engineering", size=14, bold=True, space_after=24)

add_title_p("Submitted by:", size=12, bold=False, space_after=2)
add_title_p("Viseash Ashley (MIS: 112115123)", size=13, bold=True, space_after=24)

add_title_p("Under the Supervision of:", size=12, bold=False, space_after=2)
add_title_p("Dr. [Supervisor Name]", size=13, bold=True, space_after=4)
add_title_p("Department of Computer Science and Engineering", size=12, bold=False, space_after=24)

add_title_p("INDIAN INSTITUTE OF INFORMATION TECHNOLOGY, PUNE", size=14, bold=True, space_after=2)
add_title_p("(An Institute of National Importance by an Act of Parliament)", size=11, bold=False, space_after=8)
add_title_p("NOVEMBER 2026", size=12, bold=True, space_after=0)

doc.add_page_break()

# ==========================================
# 2. BONAFIDE CERTIFICATE
# ==========================================
add_title_p("BONAFIDE CERTIFICATE", size=16, bold=True, space_after=18)
add_body_p(
    "This is to certify that the project report entitled “Spectral Band Allocation for Invisible Watermarks Under VAE Regeneration” "
    "submitted by Viseash Ashley bearing the MIS No: 112115123, in partial fulfillment of the requirements for the award of the "
    "degree of Bachelor of Technology in Computer Science and Engineering, Indian Institute of Information Technology, Pune (IIIT Pune), "
    "during the academic year 2025–2026, is an authentic record of the work carried out under my supervision and guidance."
)

p_space = doc.add_paragraph()
p_space.paragraph_format.space_before = Pt(36)

p_sig = doc.add_paragraph()
r1 = p_sig.add_run("Dr. [Supervisor Name]\t\t\t\t\tHead of the Department\n")
r1.bold = True
r2 = p_sig.add_run("Department of CSE\t\t\t\t\tDepartment of CSE\n")
r3 = p_sig.add_run("IIIT Pune\t\t\t\t\t\tIIIT Pune\n")

p_viva = doc.add_paragraph()
p_viva.paragraph_format.space_before = Pt(24)
p_viva.add_run("Project Viva-voce Examination held on: ________________________").bold = True

doc.add_page_break()

# ==========================================
# 3. UNDERTAKING & AI DISCLOSURE
# ==========================================
add_title_p("UNDERTAKING FOR PLAGIARISM", size=16, bold=True, space_after=14)
add_body_p(
    "I, Viseash Ashley, solemnly declare that the research work presented in the report entitled “Spectral Band Allocation for Invisible "
    "Watermarks Under VAE Regeneration” is solely my research work with no significant contribution from any other person. Small contribution/help "
    "wherever taken has been duly acknowledged and that the complete report has been written by me. I understand the zero tolerance policy of "
    "Indian Institute of Information Technology, Pune towards plagiarism. Therefore, I declare that no portion of my report has been plagiarized and "
    "any material used as reference is properly referred and cited. I undertake that if I am found guilty of any formal plagiarism in the above titled "
    "thesis even after award of the degree, the Institute reserves the right to withdraw or revoke my degree."
)

p_space2 = doc.add_paragraph()
p_space2.paragraph_format.space_before = Pt(20)
p_cand = doc.add_paragraph()
p_cand.add_run("Date: 14-11-2026\nPlace: Pune\t\t\t\t\t\tViseash Ashley (MIS: 112115123)")

doc.add_paragraph().paragraph_format.space_before = Pt(16)
add_title_p("AI ASSISTANCE & TOOLING DISCLOSURE", size=14, bold=True, space_after=10)
add_body_p(
    "In compliance with academic integrity standards and institutional guidelines, the author discloses that artificial intelligence coding "
    "assistants were utilized during this project as technical development aids. Specifically, generative AI tools assisted in: (i) drafting "
    "Python orchestration scripts for batch evaluation, (ii) resolving environment and binary dependency conflicts in Google Colab, and (iii) document "
    "formatting automation. All conceptual problem formulations, mathematical modeling, experimental methodologies, dataset ingestion, quantitative "
    "analyses, and scientific conclusions were conceived, independently reviewed, and verified by the author."
)

doc.add_page_break()

# ==========================================
# 4. ABSTRACT
# ==========================================
add_title_p("ABSTRACT", size=16, bold=True, space_after=14)
add_body_p(
    "Invisible digital watermarking serves as a critical technological primitive for provenance tracking, copyright verification, and "
    "synthetic media authentication. However, deep generative pipelines—specifically Variational Autoencoders (VAEs) and Latent Diffusion Models (LDMs)—"
    "act as aggressive, non-standard attack vectors that can strip invisible watermarks while preserving perceptual visual fidelity. "
    "Prior digital watermarking literature has largely treated generative autoencoders as black-box neural networks, lacking an empirical frequency-domain characterisation "
    "of how watermarks degrade under regeneration.\n\n"
    "This thesis formulates and experimentally investigates the hypothesis that generative VAE regeneration operates as a frequency-dependent "
    "degradation channel related to Wiener filtering. We partition the spatial frequency domain into 8 disjoint annular bands spanning radial frequencies "
    "from 0 to Nyquist (0.5 cyc/px). Across an empirical measurement campaign on the COCO dataset comprising 800 images (300 calibration images and "
    "500 strictly held-out test images across 77,000 evaluations), this research establishes the following findings:\n\n"
    "1. Attack-Dependent Robust Spectral Windows: The optimal watermarking band depends strongly on the specific attack architecture and severity. "
    "Under the Stable Diffusion VAE (sd-vae-ft-mse), which enforces 8x spatial downsampling into a continuous latent space, Band 1 (0.0625–0.125 cyc/px) "
    "consistently outperforms all other bands across all tested pixel pre-noise levels (sigma in [0.0, 0.20]), achieving 75.15% bit accuracy (55.0% TPR "
    "[95% CI: 50.6%, 59.3%]) at sigma=0.0 and 67.89% (26.6% TPR) at sigma=0.20, whereas Band 2 achieves 73.83% (49.8% TPR) and 63.55% (12.8% TPR). "
    "Under CompressAI neural compression, the optimal band dynamically shifts upward as quality increases, with Band 1 winning at q=1, Band 2 winning at q=2–3, "
    "Band 3 winning at q=4–6, Band 4 at q=7, and high frequencies passing through cleanly at q=8 (Band 7 reaches 100% TPR). Bands 1 and 2 collectively form "
    "the robust operational window under aggressive regeneration.\n\n"
    "2. Quantitative Resolution of the Baseband Paradox: We explain why baseband watermarking (Band 0, 0.0–0.0625 cyc/px) fails despite suffering minimal "
    "low-pass attenuation. Zero-mean host cover variance in Band 0 (sigma_cover^2 = 0.0474) is 26.6x (14.2 dB) higher than in Band 2 (0.00178), introducing severe host interference that caps "
    "unattacked decoding accuracy at 59.8% and limits TPR to <= 5.2% across all attack conditions. Band 0 exhibits the highest SSIM (0.984) because smooth DC "
    "shifts minimally disturb local structural correlation, creating an inherent design tension: baseband embedding maximizes structural similarity but severely "
    "degrades detection SNR.\n\n"
    "3. Limits of Analytical Wiener Fits: Factorized neural compression (CompressAI) conforms closely to an analytical Wiener gain model (R^2 in [0.928, 0.997]), "
    "with effective noise N_eff decreasing monotonically by approximately 44x (from 2.41 x 10^-7 at q=1 to 5.52 x 10^-9 at q=8). However, the theoretical cutoff frequency f_c under-predicts empirical cutoff "
    "by 5% to 19% at moderate qualities, and exceeds Nyquist at q >= 7. For the Stable Diffusion VAE, the Wiener model fit is poor or negative (R^2 in [-2.45, 0.43]) because latent "
    "spatial downsampling introduces non-monotonic, non-linear transfer responses that violate linear shift-invariance.\n\n"
    "4. Statistical Rigor and Inconclusive Learned Training: On 500 unwatermarked test images, blind spread-spectrum decoding closely matches the theoretical null binomial "
    "distribution B(32, 0.5) (mean score 16.10/32), yielding an empirical false positive rate of 0.40% (2/500, 95% CI: [0.11%, 1.44%]) at detection threshold "
    "tau = 24/32 bits, in close agreement with the analytical 0.35% bound. Finally, we document that end-to-end learned watermarking architectures failed to converge "
    "during training, remaining near chance (~49.8% bit decoding accuracy for the dynamic model and 0.0% TPR) even under unattacked identity conditions; this renders the experiment "
    "inconclusive regarding frequency-band allocation and linear Fourier surrogates, highlighting the necessity of progressive training curricula and carrier priors."
)

add_body_p(
    "Invisible Digital Watermarking, Variational Autoencoders (VAE), Spectral Band Allocation, Wiener Filter, Stable Diffusion, "
    "CompressAI, Host Interference, Fourier Analysis.",
    bold_prefix="Keywords: "
)

doc.add_page_break()

# ==========================================
# 5. TABLE OF CONTENTS
# ==========================================
add_title_p("TABLE OF CONTENTS", size=16, bold=True, space_after=14)
toc_items = [
    ("Chapter 1: Introduction", "1"),
    ("    1.1 Background & Motivation", "1"),
    ("    1.2 Problem Statement", "2"),
    ("    1.3 Research Hypotheses & Scope of Evaluation", "3"),
    ("    1.4 Key Contributions & Report Organization", "4"),
    ("Chapter 2: Literature Review & Theoretical Formulation", "6"),
    ("    2.1 Digital Watermarking: Classical vs. Deep Learning Approaches", "6"),
    ("    2.2 Generative Models and VAEs as Image Processing Attacks", "7"),
    ("    2.3 The Two-Forces Model: Host Interference vs. Low-Pass Attenuation", "8"),
    ("    2.4 Analytical Wiener Formulation & Power Spectrum Falloff", "10"),
    ("Chapter 3: System Architecture & Proposed Methodology", "12"),
    ("    3.1 Orthonormal Annular Frequency Band Partitioning", "12"),
    ("    3.2 Empirical Transfer Function Measurement Protocol", "13"),
    ("    3.3 Classical Spread-Spectrum Watermarking Framework", "15"),
    ("    3.4 Learned Band-Allocation Architecture & Fourier Surrogate", "16"),
    ("Chapter 4: Experimental Results & Discussion", "18"),
    ("    4.1 Experimental Setup & Evaluation Protocol (N=500)", "18"),
    ("    4.2 Natural Image Spectrum Fit & Wiener Model Characterisation", "19"),
    ("    4.3 Classical Parameter Sweep & Cutoff Tracking", "22"),
    ("    4.4 Full Held-Out Benchmark Analysis (77,000 Rows)", "24"),
    ("    4.5 Per-Band Perceptual Quality Analysis (PSNR/SSIM)", "28"),
    ("    4.6 Quantitative Host Interference Diagnosis (Why Band 0 Fails)", "30"),
    ("    4.7 Learned Band-Allocation Model: Negative Result Analysis", "32"),
    ("    4.8 Synthesis & Verification of Hypotheses", "34"),
    ("Chapter 5: Conclusion & Future Scope", "36"),
    ("    5.1 Conclusion", "36"),
    ("    5.2 Threats to Validity & Limitations", "37"),
    ("    5.3 Future Research Directions", "38"),
    ("References", "39"),
]
for item, page in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2.5)
    dots = "." * max(5, 78 - len(item) - len(page))
    p.add_run(f"{item} {dots} {page}")

doc.add_page_break()

# ==========================================
# CHAPTER 1: INTRODUCTION
# ==========================================
add_heading_1("CHAPTER 1: INTRODUCTION")

add_heading_2("1.1 Background & Motivation")
add_body_p(
    "The rapid proliferation of deep generative computer vision models—including Variational Autoencoders (VAEs), "
    "Generative Adversarial Networks (GANs), and Latent Diffusion Models (LDMs)—has transformed digital content creation. "
    "Modern diffusion architectures, such as Stable Diffusion, synthesize high-resolution imagery with remarkable realism. "
    "However, this technology simultaneously introduces serious risks: non-consensual deepfakes, copyright infringement, "
    "and automated disinformation campaigns."
)
add_body_p(
    "Digital watermarking is an established technical mechanism for copyright protection and provenance verification. "
    "By imperceptibly embedding cryptographic payloads into image data, content creators and platforms can trace synthetic media. "
    "While modern watermarks withstand conventional image processing operations—such as JPEG compression, additive noise, and blurring—"
    "they are vulnerable to generative autoencoder regeneration. In regeneration attacks, an image is passed through an encoder-decoder "
    "pipeline: x_hat = D(E(x_w)). This process purges high-frequency watermarks while preserving visual fidelity. Understanding the spectral "
    "mechanics of this degradation channel is critical for developing resilient watermarking strategies."
)

add_heading_2("1.2 Problem Statement")
add_body_p(
    "Given an original cover image x in [0, 1]^(3 x H x W) and a binary payload m in {0, 1}^L, we seek to embed m into x to produce a watermarked image "
    "x_w satisfying two criteria: (i) strict perceptual imperceptibility, evaluated by Peak Signal-to-Noise Ratio (target PSNR = 40.0 dB, empirical mean = 40.06 dB) "
    "and Structural Similarity Index (SSIM >= 0.95), and (ii) survival against downstream regeneration x_hat = A(x_w). The central research question is: "
    "How does autoencoder regeneration alter watermark energy across spatial frequency bands, and can frequency band allocation improve watermark robustness?"
)

add_heading_2("1.3 Research Hypotheses & Scope of Evaluation")
add_body_p("This thesis investigates three research hypotheses:")
add_body_p(
    "Hypothesis H1 (Wiener Transfer Equivalence): The energy transfer function H(f) = sqrt(E_out(f) / E_in(f)) of an autoencoder can be modeled by a "
    "Wiener gain G(f) = P(f) / (P(f) + N_eff), where P(f) = A * f^(-alpha) represents the natural image power spectrum, and effective noise N_eff scales with attack severity."
)
add_body_p(
    "Hypothesis H2 (Cutoff Tracking): The boundary separating watermark survival from degradation aligns with the analytical Wiener cutoff frequency "
    "f_c = (A / N_eff)^(1/alpha), shifting upward as reconstruction fidelity improves."
)
add_body_p(
    "Hypothesis H3 (Annular Robustness Window): High-frequency bands degrade under low-pass attenuation, while baseband Band 0 degrades under host cover-image "
    "interference. Consequently, intermediate frequency bands (Bands 1–2) provide a superior balance between low-pass survival and low host interference."
)
add_body_p(
    "Scope of Evaluation: This report evaluates these hypotheses across 800 photographic images from COCO 2017: 300 calibration images for transfer function "
    "characterisation and parameter sweeping (144,000 evaluations), and 500 strictly held-out test images for the final benchmark (77,000 evaluations) "
    "across Stable Diffusion VAE (6 pixel pre-noise levels) and CompressAI (8 quality levels)."
)

add_heading_2("1.4 Key Contributions & Report Organization")
add_body_p(
    "1. Analytical Wiener Characterisation: We fit natural photographic spectra (alpha=2.660) and demonstrate that CompressAI follows Wiener filtering "
    "(R^2 in [0.928, 0.997]), while Stable Diffusion VAE exhibits non-linear latent transfer dynamics violating linear shift-invariance.\n"
    "2. Host Interference Analysis: We demonstrate analytically and empirically that Band 0 failure is driven by host interference (zero-mean cover variance 26.6x / 14.2 dB higher than Band 2).\n"
    "3. Large-Scale Held-Out Benchmark (N=500, 77k Rows): Rigorous empirical validation with Wilson 95% confidence intervals and verified binomial null behavior.\n"
    "4. Perceptual Quality Benchmarking: Objective evaluation showing that Band 2 achieves 40.06 dB PSNR and SSIM > 0.963.\n"
    "5. Empirical Negative Result on End-to-End Learned Watermarking: We document that under a strict 40.0 dB PSNR budget, a compact 7-layer CNN trained without carrier priors or progressive curriculum failed to converge even on the identity channel (hovering near chance accuracy, ~49.8% for the dynamic surrogate network and 0.0% TPR). This experiment is inconclusive regarding the efficacy of differentiable Fourier surrogates, highlighting that future investigations require multi-stage curricula and matched-filter priors."
)

doc.add_page_break()

# ==========================================
# CHAPTER 2: LITERATURE REVIEW & THEORY
# ==========================================
add_heading_1("CHAPTER 2: LITERATURE REVIEW & THEORETICAL FORMULATION")

add_heading_2("2.1 Digital Watermarking: Classical vs. Deep Learning Approaches")
add_body_p(
    "Digital watermarking techniques historically partition into spatial-domain and transform-domain approaches. Spatial-domain methods "
    "(such as LSB substitution) fail under lossy compression. Transform-domain techniques (DCT, DWT, DFT) embed watermark energy into mid-frequency "
    "coefficients to survive classical low-pass filtering. Spread-spectrum watermarking, introduced by Cox et al. [1], modulates pseudorandom sequence vectors "
    "across frequency bands, achieving robustness against additive noise through correlation despreading."
)
add_body_p(
    "End-to-end deep learning architectures (e.g., HiDDeN [2], StegaStamp [3], TrustMark [4]) employ convolutional encoder-decoder pipelines trained "
    "adversarially against differentiable distortion layers. However, deep watermarking models remain vulnerable to out-of-distribution neural distortions, "
    "particularly generative autoencoders."
)

add_heading_2("2.2 Generative Models and VAEs as Image Processing Attacks")
add_body_p(
    "The vulnerability of invisible watermarks to generative image regeneration was highlighted by Zhao et al. [5] and Lu et al. [6]. "
    "Unlike classical signal degradations, generative autoencoders map images into continuous latent representations z = E(x) and reconstruct them using "
    "decoder networks x_hat = D(z). In Latent Diffusion Models (LDMs) such as Stable Diffusion [7], the autoencoder enforces an 8x spatial downsampling "
    "factor (mapping 256x256 RGB images to 32x32x4 latent tensors), regularized by a Kullback-Leibler (KL) divergence penalty to a standard Gaussian prior. "
    "Importantly, the SD-VAE employs continuous latent distributions rather than discrete codebook quantization [8]. In our evaluations, the attack parameter "
    "sigma denotes additive Gaussian pre-noise applied directly to the pixel image prior to encoding: x_noisy = clamp(x + N(0, sigma^2), 0, 1), testing "
    "the autoencoder's denoising and reconstruction behavior."
)

add_heading_2("2.3 The Two-Forces Model: Host Interference vs. Low-Pass Attenuation")
add_body_p(
    "When decoded via correlation filtering, the decision statistic for a single bit payload is governed by the signal-to-interference-plus-noise ratio (SINR):"
)
add_body_p(
    "SINR(b) = ( E_wm(b) * |H(b)|^2 ) / ( P_cover(b) * |H(b)|^2 + sigma_noise^2(b) )",
    bold_prefix="Equation 2.1: "
)
add_body_p(
    "where E_wm(b) is watermark energy in band b, H(b) is channel transfer gain, P_cover(b) is host image variance within band b, "
    "and sigma_noise^2(b) represents the autoencoder's residual reconstruction noise and latent distortion floor within the band. "
    "Because |H(b)| multiplies both the signal and host components, channel low-pass attenuation only impacts the detection statistic "
    "when the attenuated signal E_wm(b)|H(b)|^2 drops toward or below the additive reconstruction noise floor sigma_noise^2(b).\n\n"
    "Two physical forces govern detection accuracy:\n\n"
    "Force 1: Host Cover Interference (Destroys Low Frequencies): Natural photographic scenes exhibit a steep power-law spectral density P_cover(f) ~ A * f^(-alpha) [9]. "
    "In baseband Band 0, zero-mean host cover variance (sigma_cover,0^2 = 0.0474) is 26.6x (14.2 dB) higher than in Band 2 (0.00178), creating severe self-interference that overwhelms watermark detection.\n\n"
    "Force 2: VAE Low-Pass Attenuation (Destroys High Frequencies): Autoencoder spatial bottlenecks attenuate high spatial frequencies (H(f) -> 0 as f -> 0.5), "
    "degrading watermark signals in Bands 4–7 under aggressive compression as the signal drops below sigma_noise^2(b).\n\n"
    "This creates an inherent trade-off. Robust watermarking under aggressive regeneration requires operating in the intermediate spectral window—primarily "
    "Bands 1 and 2—where host power has decayed substantially while transfer gain remains sufficient."
)

add_heading_2("2.4 Analytical Wiener Formulation & Power Spectrum Falloff")
add_body_p(
    "Assuming power spectral density P(f) = A * f^(-alpha) and effective noise N_eff, the Wiener transfer gain is defined as:"
)
add_body_p(
    "G(f) = P(f) / ( P(f) + N_eff ) = 1 / ( 1 + (N_eff / A) * f^alpha )",
    bold_prefix="Equation 2.2: "
)
add_body_p(
    "The theoretical cutoff frequency f_c (where G(f_c) = 0.5) is given by:"
)
add_body_p(
    "f_c = ( A / N_eff )^( 1 / alpha )",
    bold_prefix="Equation 2.3: "
)

doc.add_page_break()

# ==========================================
# CHAPTER 3: SYSTEM ARCHITECTURE
# ==========================================
add_heading_1("CHAPTER 3: SYSTEM ARCHITECTURE & PROPOSED METHODOLOGY")

add_heading_2("3.1 Orthonormal Annular Frequency Band Partitioning")
add_body_p(
    "To isolate spatial frequencies, we establish an orthonormal Fourier partitioning that divides the centered 2D spatial frequency plane "
    "into 8 disjoint concentric annular bands spanning radial frequencies from 0 to Nyquist (f_Nyq = 0.5 cycles/pixel)."
)

add_figure("figures/v2/fig10_1_band_map.png", "Figure 3.1: Orthonormal 2D Fourier annular band partitioning into 8 disjoint spectral rings spanning [0, 0.5] cyc/px.")

add_body_p(
    "Each annular band mask M_b(u, v) is defined over normalized radial frequencies r = sqrt(u^2 + v^2) / N as: "
    "M_b(u, v) = 1 if r in [b * 0.0625, (b + 1) * 0.0625) else 0, for b in {0, 1, ..., 7}. "
    "The masks are mutually orthogonal, ensuring zero spectral overlap."
)

add_figure("figures/v2/fig10_5_pipeline_diagram.png", "Figure 3.2: Experimental system architecture encompassing Transfer Characterisation, Classical Sweep, and Learned Allocation.")

add_heading_2("3.2 Empirical Transfer Function Measurement Protocol")
add_body_p(
    "To measure channel transfer gain H(b), we inject calibrated narrowband noise probes into each band b across 300 photographic images. "
    "The empirical transfer gain is measured as H(b) = sqrt( E_out(b) / E_in(b) ). Model parameters are fitted using non-linear least squares optimization."
)

add_figure("figures/v2/fig10_2_wiener_intuition.png", "Figure 3.3: Wiener filter intuition showing the interplay between host spectrum P(f), noise floor N_eff, and transfer gain G(f).")

add_heading_2("3.3 Classical Spread-Spectrum Watermarking Framework")
add_body_p(
    "The classical baseline embeds a 32-bit pseudorandom payload m in {0, 1}^32 using antipodal spread-spectrum modulation. "
    "For each bit m_k, a cryptographically seeded carrier pattern c_k is modulated by annular band mask M_b, and scaled to maintain target fidelity (PSNR = 40.0 dB):"
)
add_body_p(
    "delta_x = gamma * sum_k [ (2 * m_k - 1) * F^-1( F(c_k) * M_b ) ]",
    bold_prefix="Equation 3.1: "
)
add_body_p(
    "where gamma is an amplitude scaling factor calibrated to meet the exact target PSNR (40.0 dB), and c_k represents the pseudo-random carrier sequence for bit k. "
    "Decoding is blind. The attacked image x_hat is projected onto band M_b, and normalized inner products with carrier c_k determine detected bits."
)

add_heading_2("3.4 Learned Band-Allocation Architecture & Fourier Surrogate")
add_body_p(
    "We investigate an end-to-end architecture comprising an Encoder CNN, a differentiable Fourier Surrogate filter layer implementing G(f), "
    "and a Decoder CNN. By approximating autoencoder attenuation with an analytical filter during training, the network is trained with gradient descent."
)

doc.add_page_break()

# ==========================================
# CHAPTER 4: EXPERIMENTAL RESULTS
# ==========================================
add_heading_1("CHAPTER 4: EXPERIMENTAL RESULTS & DISCUSSION")

add_heading_2("4.1 Experimental Setup & Evaluation Protocol (N=500)")
add_body_p(
    "Evaluations were conducted on 800 COCO 2017 images [10] (300 calibration images and 500 strictly held-out unseen test images). "
    "All images were resized to 256x256 RGB. Target embedding fidelity was strictly maintained at target PSNR = 40.0 dB (empirical mean = 40.06 dB) across all bands.\n\n"
    "Attacks evaluated:\n"
    "1. Stability AI's Stable Diffusion VAE (sd-vae-ft-mse) across 6 pixel pre-noise levels: sigma in {0.00, 0.02, 0.05, 0.10, 0.15, 0.20}.\n"
    "2. CompressAI Factorised Prior (bmshj2018, Ballé et al. [11]) across 8 quality levels: q in {1, 2, 3, 4, 5, 6, 7, 8}.\n"
    "Detection is evaluated at threshold tau = 24/32 bits (75.0%), corresponding to an analytical false positive rate FPR = 0.35% under the binomial null B(32, 0.5). "
    "All True Positive Rates (TPRs) report exact Wilson 95% score confidence intervals [12]."
)

add_heading_2("4.2 Natural Image Spectrum Fit & Wiener Model Characterisation")
add_body_p(
    "Fitting the radial power spectrum across 300 natural images yielded power-law parameters alpha = 2.660 +/- 0.296 and ln A = -8.737 (A = 1.605 x 10^-4), "
    "confirming natural image power-law spectral decay [9]."
)

add_figure("figures/v2/fig_wiener_fit_quality.png", "Figure 4.1: Wiener fit quality across attacks: Empirical vs. Predicted cutoff f_c (Left) and Effective noise floor N_eff vs. attack strength (Right).")

# Table 4.1: Wiener fits
add_heading_3("Table 4.1: Comprehensive Analytical Wiener Model Fits Across Attacks")
t_w_data = [
    ["Attack Family", "Strength", "Fitted N_eff", "R^2 Score", "RMSE", "Pred f_c (cyc/px)", "Meas f_c (cyc/px)", "f_c Error (%)"],
    ["CompressAI", "q = 1", "2.41e-07", "0.992", "0.043", "0.160", "0.198", "-19.2%"],
    ["CompressAI", "q = 2", "1.40e-07", "0.983", "0.058", "0.196", "0.228", "-14.0%"],
    ["CompressAI", "q = 3", "8.63e-08", "0.963", "0.078", "0.235", "0.261", "-10.0%"],
    ["CompressAI", "q = 4", "5.35e-08", "0.948", "0.082", "0.281", "0.304", "-7.6%"],
    ["CompressAI", "q = 5", "3.51e-08", "0.928", "0.085", "0.330", "0.349", "-5.4%"],
    ["CompressAI", "q = 6", "1.76e-08", "0.947", "0.049", "0.428", "0.425", "+0.7%"],
    ["CompressAI", "q = 7", "9.89e-09", "0.988", "0.016", "0.531*", "0.469", "N/A (Exceeds Nyquist)"],
    ["CompressAI", "q = 8", "5.52e-09", "0.997", "0.005", "0.661*", "0.469", "N/A (Exceeds Nyquist)"],
    ["SD VAE", "sigma = 0.00", "1.21e-09", "-0.396", "0.044", "1.168*", "0.469", "N/A (Out of domain)"],
    ["SD VAE", "sigma = 0.02", "1.24e-09", "0.433", "0.016", "1.157*", "0.469", "N/A (Out of domain)"],
    ["SD VAE", "sigma = 0.05", "1.00e-09", "-2.447", "0.082", "1.254*", "0.469", "N/A (Out of domain)"],
    ["SD VAE", "sigma = 0.10", "1.63e-09", "-2.089", "0.211", "1.044*", "0.469", "N/A (Out of domain)"],
    ["SD VAE", "sigma = 0.15", "2.46e-09", "-2.209", "0.284", "0.895*", "0.469", "N/A (Out of domain)"],
    ["SD VAE", "sigma = 0.20", "3.11e-09", "-2.374", "0.296", "0.820*", "0.469", "N/A (Out of domain)"],
]

t1 = doc.add_table(rows=len(t_w_data), cols=8)
t1.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_i, row in enumerate(t_w_data):
    for c_i, val in enumerate(row):
        c = t1.cell(r_i, c_i)
        c.text = val
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(8.5)
        if r_i == 0:
            set_cell_background(c, "D9D9D9")
            p.runs[0].bold = True
        elif c_i == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

add_body_p(
    "Discussion of Fit Dynamics: The analytical Wiener model achieves high goodness of fit for CompressAI (R^2 in [0.928, 0.997] across q in [1, 8]). "
    "The theoretical cutoff f_c under-predicts the measured cutoff by 5.4% to 19.2% for q in [1, 5]. At q=7 and q=8, the predicted cutoff "
    "exceeds the spatial Nyquist frequency (0.531 and 0.661 cyc/px) while the measured value is capped at the highest band center (0.469 cyc/px). "
    "For the Stable Diffusion VAE, the Wiener model fit is poor or negative (R^2 in [-2.45, 0.43]), yielding predicted cutoffs above 0.8 cyc/px that are outside the digital frequency domain. "
    "This confirms that latent autoencoders introduce non-monotonic, non-linear transfer behaviors that violate linear shift-invariance."
)

add_heading_2("4.3 Classical Parameter Sweep & Cutoff Tracking")
add_body_p(
    "Definition of Optimal Band: We define the optimal frequency band for a given attack condition as the band achieving the highest mean bit decoding accuracy "
    "across the 500 test images. In the event of saturation where multiple bands reach 100% True Positive Rate, ties are broken by highest mean bit accuracy. "
    "Under Stable Diffusion VAE, Band 1 is optimal across all tested sigma levels."
)

add_figure("figures/v2/fig_best_band_vs_fc.png", "Figure 4.2: Optimal watermark frequency band vs. theoretical cutoff f_c across attack strengths.")
add_body_p(
    "Figure 4.2 illustrates that for CompressAI, the optimal watermark band tracks the Wiener cutoff f_c upward as quality increases. "
    "For Stable Diffusion VAE, latent downsampling restricts the optimal band to Band 1 across all noise levels."
)

add_figure("figures/v2/fig10_6_band_survival_story.png", "Figure 4.3: Empirical bit accuracy survival comparing unattacked, CompressAI (q=3), and SD VAE (sigma=0.05).")

add_heading_2("4.4 Full Held-Out Benchmark Analysis (77,000 Rows)")
add_body_p(
    "The full held-out benchmark evaluates 500 unseen images across all 8 frequency bands (77,000 empirical rows). "
    "Figure 4.4 displays the comprehensive evaluation across SD-VAE and CompressAI."
)

add_figure("figures/v2/fig_heldout_benchmark_full.png", "Figure 4.4: Complete Held-Out Benchmark on 500 Unseen Test Images (77,000 Evaluations): Bit accuracy and detection rate (TPR @ tau=24) with Wilson 95% confidence intervals.", width_in=6.0)

# Table 4.2: SD-VAE Full 8 Bands
add_heading_3("Table 4.2: Robustness Under Stable Diffusion VAE Across All 8 Bands (N=500, Target PSNR = 40.0 dB, Empirical Mean = 40.06 dB)")
t_sd_data = [
    ["Watermarking Band", "Metric", "sigma = 0.00", "sigma = 0.02", "sigma = 0.05", "sigma = 0.10", "sigma = 0.15", "sigma = 0.20"],
    ["Band 0", "Bit Acc (%)\nTPR [95% CI]", "57.93%\n3.0% [1.8, 4.9]", "57.69%\n2.6% [1.5, 4.4]", "57.61%\n2.0% [1.1, 3.6]", "57.47%\n2.4% [1.4, 4.1]", "57.39%\n2.6% [1.5, 4.4]", "57.49%\n2.8% [1.7, 4.6]"],
    ["Band 1 (Optimal)", "Bit Acc (%)\nTPR [95% CI]", "75.15%\n55.0% [50.6, 59.3]", "73.72%\n52.0% [47.6, 56.3]", "70.81%\n40.0% [35.8, 44.4]", "68.80%\n32.8% [28.8, 37.0]", "68.04%\n27.6% [23.9, 31.7]", "67.89%\n26.6% [22.9, 30.6]"],
    ["Band 2", "Bit Acc (%)\nTPR [95% CI]", "73.83%\n49.8% [45.4, 54.2]", "72.12%\n42.6% [38.3, 47.0]", "68.64%\n30.8% [26.9, 35.0]", "65.69%\n19.4% [16.2, 23.1]", "64.74%\n14.8% [12.0, 18.2]", "63.55%\n12.8% [10.2, 16.0]"],
    ["Band 3", "Bit Acc (%)\nTPR [95% CI]", "66.83%\n25.4% [21.8, 29.4]", "63.89%\n16.8% [13.8, 20.3]", "61.49%\n9.0% [6.8, 11.9]", "59.66%\n4.2% [2.7, 6.4]", "58.27%\n3.6% [2.2, 5.6]", "57.04%\n2.2% [1.2, 3.9]"],
    ["Band 4", "Bit Acc (%)\nTPR [95% CI]", "58.98%\n5.6% [3.9, 8.0]", "58.46%\n4.2% [2.7, 6.4]", "57.40%\n3.8% [2.4, 5.9]", "55.44%\n1.4% [0.7, 2.9]", "53.93%\n1.0% [0.4, 2.3]", "53.67%\n0.4% [0.1, 1.4]"],
    ["Band 5", "Bit Acc (%)\nTPR [95% CI]", "55.17%\n1.8% [0.9, 3.4]", "54.64%\n1.6% [0.8, 3.1]", "53.62%\n1.0% [0.4, 2.3]", "51.36%\n1.4% [0.7, 2.9]", "51.01%\n1.0% [0.4, 2.3]", "50.50%\n0.8% [0.3, 2.0]"],
    ["Band 6", "Bit Acc (%)\nTPR [95% CI]", "53.64%\n1.0% [0.4, 2.3]", "52.79%\n1.0% [0.4, 2.3]", "52.09%\n0.8% [0.3, 2.0]", "50.44%\n0.8% [0.3, 2.0]", "49.00%\n0.0% [0.0, 0.7]", "49.24%\n0.0% [0.0, 0.7]"],
    ["Band 7", "Bit Acc (%)\nTPR [95% CI]", "51.21%\n0.8% [0.3, 2.0]", "51.58%\n0.2% [0.0, 1.1]", "50.82%\n0.4% [0.1, 1.4]", "50.50%\n0.4% [0.1, 1.4]", "49.93%\n0.0% [0.0, 0.7]", "49.18%\n0.2% [0.0, 1.1]"],
]

t2 = doc.add_table(rows=len(t_sd_data), cols=8)
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_i, row in enumerate(t_sd_data):
    for c_i, val in enumerate(row):
        c = t2.cell(r_i, c_i)
        c.text = val
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(8.0)
        if r_i == 0:
            set_cell_background(c, "D9D9D9")
            p.runs[0].bold = True
        elif c_i == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

add_body_p(
    "Observation on Table 4.2: Table 4.2 demonstrates that Band 1 "
    "strictly outperforms Band 2 across all noise strengths sigma under SD-VAE (TPR 55.0% vs. 49.8% at sigma=0.00, and 26.6% vs. 12.8% at sigma=0.20). "
    "The 95% confidence intervals do not overlap for sigma >= 0.02. This occurs because the aggressive spatial bottleneck of SD-VAE penalizes Band 2 "
    "attenuation more heavily than the host interference penalty of Band 1. Bands 1 and 2 collectively form the survivable low-frequency window."
)

# Table 4.3: CompressAI Full 8 Bands
add_heading_3("Table 4.3: Robustness Under CompressAI Across All 8 Bands (N=500, Target PSNR = 40.0 dB, Empirical Mean = 40.06 dB)")
t_ca_data = [
    ["Band", "Metric", "q=1", "q=2", "q=3", "q=4", "q=5", "q=6", "q=7", "q=8"],
    ["Band 0", "Bit Acc (%)\nTPR (%)", "57.31%\n2.8%", "57.88%\n3.0%", "58.61%\n4.0%", "58.83%\n4.0%", "59.16%\n4.4%", "59.41%\n5.0%", "59.56%\n5.0%", "59.60%\n5.2%"],
    ["Band 1", "Bit Acc (%)\nTPR (%)", "67.81%\n29.4%*", "72.85%\n48.4%", "78.64%\n72.8%", "83.35%\n85.6%", "86.80%\n94.6%", "89.11%\n97.8%", "90.37%\n98.4%", "90.96%\n98.6%"],
    ["Band 2", "Bit Acc (%)\nTPR (%)", "65.04%\n18.4%", "73.29%\n50.0%*", "80.79%\n78.6%*", "87.30%\n92.0%", "93.83%\n99.2%", "96.88%\n99.8%", "98.40%\n100.0%", "98.77%\n100.0%"],
    ["Band 3", "Bit Acc (%)\nTPR (%)", "58.17%\n3.2%", "65.62%\n20.0%", "77.26%\n63.0%", "87.52%\n89.0%*", "94.37%\n98.0%*", "97.92%\n99.6%*", "99.56%\n100.0%", "99.79%\n100.0%"],
    ["Band 4", "Bit Acc (%)\nTPR (%)", "55.28%\n1.2%", "59.21%\n4.6%", "67.39%\n27.0%", "81.47%\n77.6%", "92.88%\n95.6%", "97.48%\n98.8%", "99.78%\n100.0%*", "99.96%\n100.0%"],
    ["Band 5", "Bit Acc (%)\nTPR (%)", "51.37%\n0.2%", "54.20%\n0.2%", "59.75%\n5.8%", "70.58%\n40.4%", "86.90%\n87.8%", "97.14%\n98.4%", "99.73%\n99.8%", "99.98%\n100.0%"],
    ["Band 6", "Bit Acc (%)\nTPR (%)", "50.59%\n0.4%", "51.61%\n1.4%", "53.85%\n1.0%", "61.37%\n8.4%", "72.72%\n49.8%", "93.97%\n95.0%", "99.36%\n99.6%", "99.97%\n100.0%"],
    ["Band 7", "Bit Acc (%)\nTPR (%)", "50.17%\n0.2%", "50.26%\n0.4%", "51.12%\n1.0%", "54.34%\n0.6%", "60.69%\n7.8%", "81.29%\n75.4%", "97.31%\n99.0%", "100.0%\n100.0%*"],
]

t3 = doc.add_table(rows=len(t_ca_data), cols=10)
t3.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_i, row in enumerate(t_ca_data):
    for c_i, val in enumerate(row):
        c = t3.cell(r_i, c_i)
        c.text = val
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(8.0)
        if r_i == 0:
            set_cell_background(c, "D9D9D9")
            p.runs[0].bold = True
        elif c_i == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

add_body_p(
    "Observation on Table 4.3: Asterisks (*) denote the optimal band per quality level. The optimal band shifts systematically from Band 1 (q=1) "
    "to Band 2 (q=2, 3), Band 3 (q=4, 5, 6), Band 4 (q=7), and Band 7 (q=8). From q >= 4 upward, the differences among top-performing active bands are within approximately 1 percentage point. Crucially, the assertion that 'Bands 4–7 collapse' holds only under aggressive "
    "compression (q <= 3). At higher qualities (q >= 6), high-frequency details are preserved, with Band 7 achieving 97.31% bit accuracy (99.0% TPR) at q=7 "
    "and 100.0% bit accuracy (100.0% TPR) at q=8."
)

add_figure("figures/v2/fig_null_distribution.png", "Figure 4.5: Score distribution of 500 unwatermarked images under blind spread-spectrum decoding vs. theoretical Binomial(32, 0.5) null distribution.", width_in=5.2)

add_body_p(
    "Analysis of False Positive Rate (FPR): Under the analytical null distribution B(32, 0.5), the probability of randomly achieving >= 24 matching bits "
    "is P(X >= 24) = 0.003506 (0.35%). Evaluating 500 actual unwatermarked images through the spread-spectrum decoder (Figure 4.5) yielded a mean score of "
    "16.10 / 32 bits (std = 2.78) and exactly 2 false alarms (FPR = 0.40%, 95% Wilson CI [12]: [0.11%, 1.44%]), closely matching the theoretical bound. "
    "The operational false alarm rate is governed by the binomial statistic (~0.35%–0.40%)."
)

add_heading_2("4.5 Per-Band Perceptual Quality Analysis (PSNR/SSIM)")
add_body_p(
    "Perceptual fidelity was evaluated using Peak Signal-to-Noise Ratio (PSNR) and Structural Similarity Index (SSIM) between original images x "
    "and watermarked images x_w at strictly matched target PSNR = 40.0 dB (empirical mean = 40.06 dB). LPIPS was omitted from the quantitative evaluation "
    "due to environment constraints."
)

add_figure("figures/v2/fig_perceptual_per_band.png", "Figure 4.6: Structural similarity (SSIM) across spatial frequency bands at calibrated PSNR = 40.0 dB.")

# Table 4.4: Perceptual Metrics
add_heading_3("Table 4.4: Objective Perceptual Metrics Across Frequency Bands (Target PSNR = 40.0 dB, Empirical Mean = 40.06 dB)")
t_p_data = [
    ["Band Index", "Radial Frequency Range (cyc/px)", "Band Center (cyc/px)", "Empirical PSNR (dB)", "Structural Similarity (SSIM)"],
    ["Band 0", "[0.0000, 0.0625)", "0.03125", "40.059 dB", "0.9842"],
    ["Band 1", "[0.0625, 0.1250)", "0.09375", "40.057 dB", "0.9685"],
    ["Band 2", "[0.1250, 0.1875)", "0.15625", "40.058 dB", "0.9631"],
    ["Band 3", "[0.1875, 0.2500)", "0.21875", "40.059 dB", "0.9632"],
    ["Band 4", "[0.2500, 0.3125)", "0.28125", "40.061 dB", "0.9626"],
    ["Band 5", "[0.3125, 0.3750)", "0.34375", "40.060 dB", "0.9626"],
    ["Band 6", "[0.3750, 0.4375)", "0.40625", "40.062 dB", "0.9625"],
    ["Band 7", "[0.4375, 0.5000)", "0.46875", "40.063 dB", "0.9625"],
]

t4 = doc.add_table(rows=len(t_p_data), cols=5)
t4.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_i, row in enumerate(t_p_data):
    for c_i, val in enumerate(row):
        c = t4.cell(r_i, c_i)
        c.text = val
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(9.0)
        if r_i == 0:
            set_cell_background(c, "D9D9D9")
            p.runs[0].bold = True
        elif c_i == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

add_figure("figures/v2/fig10_4_watermark_residuals.png", "Figure 4.7: Watermark spatial residuals (amplified 10x) across representative frequency bands.")

add_heading_2("4.6 Quantitative Host Interference Diagnosis (Why Band 0 Fails)")
add_body_p(
    "The SSIM Paradox and Host Interference: As shown in Table 4.4, Band 0 exhibits the highest structural similarity (SSIM = 0.9842), "
    "compared to 0.9631 in Band 2. This occurs because SSIM computes structural correlation over local 11x11 Gaussian windows; low-frequency energy "
    "corresponds to smooth, nearly constant luminance shifts that leave local cross-correlations virtually undisturbed. Conversely, higher-frequency "
    "bands introduce fine texture variations that slightly reduce local correlation."
)
add_body_p(
    "However, this high perceptual fidelity in Band 0 is coupled with severe detection degradation. An analytical signal-to-interference ratio (SIR) "
    "calculation on zero-mean luminance demonstrates why: measured host cover variance in Band 0 is sigma_cover,0^2 = 0.0474, whereas in Band 2 it is "
    "sigma_cover,2^2 = 0.00178 (26.6x lower, a 14.2 dB reduction in host interference), and in Band 7 it is sigma_cover,7^2 = 0.000255 (186x lower). "
    "At 40.0 dB PSNR (sigma_wm^2 = 1.00 x 10^-4), the raw signal-to-interference ratio before correlation is SIR_0 = 1.0e-4 / 0.0474 = -26.8 dB in Band 0, "
    "compared to SIR_2 = 1.0e-4 / 0.00178 = -12.5 dB in Band 2—a 14.3 dB advantage for Band 2. "
    "Consequently, despreading correlation gain is sufficient to decode Band 2 reliably (98.9% unattacked accuracy), whereas Band 0 decoding is heavily corrupted by host energy (59.8% unattacked accuracy)."
)

add_figure("figures/v2/fig_two_forces.png", "Figure 4.8: The Two Forces trade-off: VAE transfer gain H(f) vs. normalized host interference (1/SNR_b).")

add_heading_2("4.7 Learned Band-Allocation Model: Negative Result Analysis")
add_body_p(
    "Four learned watermarking models were trained: three fixed-regime control networks (Low: Bands 0–2, Mid: Bands 3–5, High: Bands 6–7) "
    "and a dynamic model employing a learnable frequency-band allocation layer trained against a differentiable Fourier surrogate filter G(f)."
)
add_body_p(
    "When evaluated on a pilot set of 64 images across 14 attack conditions (896 evaluations per model), the learned models failed to establish robust payload transmission:\n"
    "• The dynamic surrogate network achieved an overall mean bit decoding accuracy of 49.83% ± 8.49% (SD-VAE sigma=0.0: 49.95% ± 8.43%; CompressAI q=8: 49.90% ± 8.44%) and 0.0% True Positive Rate at the tau = 24/32 threshold.\n"
    "• The mid-band control network reached an overall mean bit accuracy of 49.36% ± 8.51% (0.0% TPR).\n"
    "• The high-band control network achieved 52.18% ± 8.31% mean bit accuracy (0.78% TPR under SD-VAE, 0.0% under CompressAI).\n"
    "• The low-band control network achieved 58.68% ± 12.11% overall bit accuracy, remaining near chance under SD-VAE (55.76% bit accuracy, 2.08% TPR at sigma=0.0) but reaching 77.10% bit accuracy (22.85% TPR) under mild compression (CompressAI q=8)."
)
add_body_p(
    "All learned models stayed at chance even with no attack (identity channel accuracy remained near 50%), so training did not converge and this experiment is inconclusive about band allocation and Fourier surrogates. Likely contributing factors (untested in this study) include:\n"
    "1. Very Low Perturbation Budget at 40 dB: Enforcing a 40 dB target PSNR constrains watermark RMS to 0.01, which corresponds to an average shift of only ~2.55 intensity levels on an 8-bit scale [0, 255].\n"
    "2. Aggressive Training Curriculum: The training schedule switched from identity passthrough to noise after only 3 epochs in a 30-epoch budget, introducing distortion before the identity channel converged.\n"
    "3. Blind Decoding Without Carrier Priors: The decoder was an unguided 7-layer CNN with global average pooling tasked with extracting 32 arbitrary bits from natural textures without a shared carrier key or matched-filter prior.\n\n"
    "Under the same 40 dB constraint, the classical spread-spectrum watermark, which has a shared pseudo-random key and matched-filter decoding, did decode reliably under mild regeneration (e.g., 100% TPR at CompressAI q=8, and 55.0% TPR at SD-VAE sigma=0.0, though SD-VAE remains a very challenging attack even for the classical method where peak accuracy caps at 75.15%). The theoretical processing gain (G_proc ~ 10 log10(256^2 / 32) ~ 33.1 dB) represents an upper bound on degrees of freedom for full-image carriers, whereas annular band-filtering restricts spatial degrees of freedom."
)

add_heading_2("4.8 Synthesis & Verification of Hypotheses")
add_body_p(
    "Hypothesis H1 (Wiener Transfer Equivalence): PARTIALLY SUPPORTED. Supported with high precision on CompressAI (R^2 in [0.928, 0.997]), "
    "where effective noise N_eff scales monotonically (decreasing by ~44x from q=1 to q=8). Poor or negative on Stable Diffusion VAE (R^2 in [-2.45, 0.43]), "
    "where 8x latent spatial downsampling introduces non-monotonic, non-linear frequency responses.\n\n"
    "Hypothesis H2 (Cutoff Tracking): PARTIALLY SUPPORTED. The survival boundary (where watermarks remain above the collapse floor) aligns with f_c "
    "(e.g., at q=6, f_c = 0.428 cyc/px falls in Band 6, where Band 6 achieves 94.0% accuracy while Band 7 drops to 81.3%). However, the optimal band lags well "
    "below f_c (optimal at Band 3 for q=6) due to the trade-off between transfer gain and host interference. Furthermore, for q >= 4, the top-performing bands "
    "differ by within approximately 1 percentage point.\n\n"
    "Hypothesis H3 (Annular Robustness Window): PARTIALLY SUPPORTED. The claim that Band 2 is universally optimal is contradicted by the data. "
    "Under SD-VAE, Band 1 strictly outperforms Band 2 across all noise levels (TPR 55.0% vs. 49.8% at sigma=0.0). Under CompressAI, higher bands outperform "
    "Band 2 at high qualities (q >= 4). Bands 1 and 2 collectively form the robust operational window under aggressive regeneration, with the specific optimum "
    "depending on the attack architecture."
)

doc.add_page_break()

# ==========================================
# CHAPTER 5: CONCLUSION & FUTURE SCOPE
# ==========================================
add_heading_1("CHAPTER 5: CONCLUSION & FUTURE SCOPE")

add_heading_2("5.1 Conclusion")
add_body_p(
    "This project report has presented an analytical and empirical investigation into spectral band allocation for invisible digital watermarking "
    "under generative autoencoder regeneration. The key conclusions of this work are:\n\n"
    "1. Transfer Mechanics Depend on Architecture: Factorized neural compression conforms closely to analytical Wiener filtering (R^2 up to 0.997), "
    "whereas continuous latent autoencoders (SD-VAE) violate linear shift-invariance due to spatial downsampling.\n"
    "2. Host Interference Constrains Baseband: Band 0 watermarking fails due to high host cover variance (26.6x / 14.2 dB higher than Band 2), despite achieving the "
    "highest structural similarity (SSIM = 0.984). Low frequencies represent a fundamental trade-off between structural preservation and detection SNR.\n"
    "3. Attack-Dependent Robust Windows: Under aggressive regeneration (SD-VAE), Bands 1 and 2 form the robust operational window, with Band 1 providing "
    "the highest TPR (55.0% at sigma=0.0). Under variable-rate compression, optimal bands shift dynamically toward higher frequencies.\n"
    "4. Inconclusive Learned Model Training: Under a strict 40 dB PSNR budget, a compact 7-layer CNN trained without carrier priors or progressive "
    "curriculum failed to converge even on the identity channel (hovering near chance accuracy, ~49.8% for the dynamic surrogate network and 0.0% TPR). "
    "Consequently, this experiment remains inconclusive regarding the efficacy of differentiable Fourier surrogates, highlighting that future "
    "investigations require multi-stage curricula and matched-filter priors."
)

add_heading_2("5.2 Threats to Validity & Limitations")
add_body_p(
    "1. Domain Specificity: Natural photographic images (COCO) follow a 1/f^2.66 power law [9]. Synthetic artwork, diagrams, or cartoons possess different "
    "spectral characteristics that will shift the interference landscape.\n"
    "2. Payload Capacity: Evaluated on a fixed 32-bit payload. Higher capacities reduce per-bit correlation gain, altering threshold behavior.\n"
    "3. Geometric Synchronization: The spread-spectrum scheme requires spatial alignment; rotational or cropping attacks require pre-registration."
)

add_heading_2("5.3 Future Research Directions")
add_body_p(
    "1. Progressive Curriculum for Learned Watermarking: To prevent optimization stalls at 40 dB, training should initialize at higher perturbation budgets (e.g., 30 dB PSNR) until the identity channel reaches >98% accuracy, before annealing to strict imperceptibility.\n"
    "2. Carrier-Conditioned Decoding: Providing learned decoders with structured carrier priors or matched-filter projections rather than forcing blind extraction from scratch.\n"
    "3. Direct Latent Watermarking: Injecting watermarks directly into the continuous latent space of diffusion autoencoders.\n"
    "4. Adaptive Frequency Allocation: Dynamic bit allocation that analyzes local image spectra to embed energy into bands with minimal host interference."
)

add_heading_1("REFERENCES")
refs = [
    "[1] I. J. Cox, J. Kilian, F. T. Leighton, and T. Shamoon, “Secure spread spectrum watermarking for multimedia,” IEEE Transactions on Image Processing, vol. 6, no. 12, pp. 1673–1687, 1997.",
    "[2] J. Zhu, R. Kaplan, A. Johnson, and L. Fei-Fei, “HiDDeN: Hiding images with deep networks,” in Proceedings of the European Conference on Computer Vision (ECCV), 2018, pp. 657–672.",
    "[3] M. Tancik, B. Mildenhall, and R. Ng, “StegaStamp: Invisible hyperlinks in physical photographs,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2020, pp. 2117–2126.",
    "[4] T. Bui, S. Agarwal, and J. Collomosse, “TrustMark: Universal watermarking for arbitrary resolution images,” arXiv preprint arXiv:2311.18297, 2023.",
    "[5] X. Zhao, K. Zhang, H. Su, S. Zhang, and X. Hu, “Invisible image watermarks are provably removable using generative AI,” in Advances in Neural Information Processing Systems (NeurIPS), vol. 37, 2024, arXiv:2306.01953.",
    "[6] S. Lu, Z. Ren, Y. Ding, and M. Sun, “Robust watermarking using generative priors against image editing: From benchmarking to advances,” in International Conference on Learning Representations (ICLR), 2025, arXiv:2410.18775.",
    "[7] R. Rombach, A. Blattmann, D. Lorenz, P. Esser, and B. Ommer, “High-resolution image synthesis with latent diffusion models,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2022, pp. 10684–10695.",
    "[8] A. van den Oord, O. Vinyals, and K. Kavukcuoglu, “Neural discrete representation learning,” in Advances in Neural Information Processing Systems (NeurIPS), vol. 30, 2017.",
    "[9] D. L. Ruderman, “The statistics of natural images,” Network: Computation in Neural Systems, vol. 5, no. 4, pp. 517–548, 1994.",
    "[10] T. Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Dollár, and C. L. Zitnick, “Microsoft COCO: Common objects in context,” in European Conference on Computer Vision (ECCV), 2014, pp. 740–755.",
    "[11] J. Ballé, D. Minnen, S. Singh, S. J. Hwang, and N. Johnston, “Variational image compression with a scale hyperprior,” in International Conference on Learning Representations (ICLR), 2018.",
    "[12] E. B. Wilson, “Probable inference, the law of succession, and statistical inference,” Journal of the American Statistical Association, vol. 22, no. 158, pp. 209–212, 1927.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.first_line_indent = Inches(-0.4)
    p.paragraph_format.space_after = Pt(4)
    p.add_run(ref)

# Save document
doc.save(DOCX_OUT)
print(f"[build_report_v3] Successfully generated corrected: {DOCX_OUT} ({DOCX_OUT.stat().st_size / 1024:.1f} KB)")
