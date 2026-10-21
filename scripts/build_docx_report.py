"""
scripts/build_docx_report.py - Generate formatted BTP Project Report in .docx format
Conforming to IIIT Pune BTP guidelines and sample report template.

Changes from v1 (fixes applied after examiner critique):
  - Corrected held-out benchmark to 64 images (not 500); added sampling-error caveat
  - Fixed R^2 claim: "0.877-0.910" not ">0.88"
  - Clarified 144,000-row count includes unattacked baselines
  - Changed tau to 24 (FPR=0.35%); all TPR values recomputed
  - Replaced "prove/proved" with "demonstrate/show"
  - Fixed high/mid band collapse claim (49.3% is mid, 52% is high)
  - Added explicit negative-result section for learned model
  - Removed unsupported "without visible artifacts" claim from H3
  - Softened H2 to "collapse boundary aligns with f_c"
  - Fixed TrustMark citation to arXiv:2311.18297, Bui et al.
  - Added W-Bench and VINE references
  - Replaced Track A/B/C and Merge 2 jargon with descriptive section names
  - Fixed "Keywords: Keywords:" duplication
  - Fixed garbled abstract opening sentence
  - Added learned_main_surrogate row to Tables 1 & 2
"""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_OUT = Path("BTP_Final_Report_Spectral_Watermarking.docx")
FIG_DIR = Path("figures")

doc = Document()

# Set standard margins: 1 inch (72 pt)
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1.0)

# Set base style to Times New Roman, 12pt, 1.15 line spacing
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


def add_title_p(text, size=17, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.bold = bold
    return p


def add_heading_1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.bold = True
    return p


def add_heading_2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True
    return p


def add_heading_3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
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


def add_figure(img_path, caption):
    if Path(img_path).exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        doc.add_picture(str(img_path), width=Inches(5.8))
        # Center image
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r = p_cap.add_run(caption)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10.5)
        r.italic = True


print("[build_docx] Generating BTP Report...")

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
add_title_p("[Supervisor Name]", size=13, bold=True, space_after=4)
add_title_p("Department of Computer Science and Engineering", size=12, bold=False, space_after=24)

add_title_p("INDIAN INSTITUTE OF INFORMATION TECHNOLOGY, PUNE", size=14, bold=True, space_after=2)
add_title_p("(An Institute of National Importance by an Act of Parliament)", size=11, bold=False, space_after=8)
add_title_p("OCTOBER 2026", size=12, bold=True, space_after=0)

doc.add_page_break()

# ==========================================
# 2. BONAFIDE CERTIFICATE
# ==========================================
add_title_p("BONAFIDE CERTIFICATE", size=16, bold=True, space_after=18)
add_body_p(
    "This is to certify that the project report entitled \u201cSpectral Band Allocation for Invisible Watermarks Under VAE Regeneration\u201d "
    "submitted by Viseash Ashley bearing the MIS No: 112115123, in partial fulfillment of the requirements for the award of the "
    "degree of Bachelor of Technology in Computer Science and Engineering, Indian Institute of Information Technology, Pune (IIIT Pune), "
    "during the academic year 2025\u20132026, is an authentic record of the work carried out under my supervision and guidance."
)

p_space = doc.add_paragraph()
p_space.paragraph_format.space_before = Pt(36)

p_sig = doc.add_paragraph()
r1 = p_sig.add_run("[Supervisor Name]\t\t\t\t\tHead of the Department\n")
r1.bold = True
r2 = p_sig.add_run("Department of CSE\t\t\t\t\tDepartment of CSE\n")
r3 = p_sig.add_run("IIIT Pune\t\t\t\t\t\tIIIT Pune\n")

p_viva = doc.add_paragraph()
p_viva.paragraph_format.space_before = Pt(24)
p_viva.add_run("Project Viva-voce Examination held on: ________________________").bold = True

doc.add_page_break()

# ==========================================
# 3. UNDERTAKING FOR PLAGIARISM & CONFLICT OF INTEREST
# ==========================================
add_title_p("UNDERTAKING FOR PLAGIARISM", size=16, bold=True, space_after=14)
add_body_p(
    "I, Viseash Ashley, solemnly declare that the research work presented in the report entitled \u201cSpectral Band Allocation for Invisible "
    "Watermarks Under VAE Regeneration\u201d is solely my research work with no significant contribution from any other person. Small contribution/help "
    "wherever taken has been duly acknowledged and that the complete report has been written by me. I understand the zero tolerance policy of "
    "Indian Institute of Information Technology, Pune towards plagiarism. Therefore, I declare that no portion of my report has been plagiarized and "
    "any material used as reference is properly referred and cited. I undertake that if I am found guilty of any formal plagiarism in the above titled "
    "thesis even after award of the degree, the Institute reserves the rights to withdraw or revoke my B.Tech degree."
)

p_usig = doc.add_paragraph()
p_usig.paragraph_format.space_before = Pt(18)
p_usig.add_run("Student Name: Viseash Ashley (MIS: 112115123)\nDate: 21st October 2026\nPlace: Pune, India").bold = True

add_title_p("CONFLICT OF INTEREST", size=16, bold=True, space_after=14)
add_body_p(
    "Manuscript Title: Spectral Band Allocation for Invisible Watermarks Under VAE Regeneration\n\n"
    "The author certifies that they have NO affiliations with or involvement in any organization or entity with any financial interest "
    "(such as honoraria, educational grants, employment, consultancies, stock ownership, or other equity interest) or non-financial interest "
    "(such as personal or professional relationships, affiliations, knowledge, or beliefs) in the subject matter or materials discussed in this manuscript."
)

p_csig = doc.add_paragraph()
p_csig.paragraph_format.space_before = Pt(18)
p_csig.add_run("Signature of the Student: ________________________\nDate: 21st October 2026").bold = True

doc.add_page_break()

# ==========================================
# 4. ACKNOWLEDGEMENT & ABSTRACT
# ==========================================
add_title_p("ACKNOWLEDGEMENT", size=16, bold=True, space_after=14)
add_body_p(
    "This project would not have been possible without the guidance and cooperation of many individuals. I would like to express my sincere "
    "gratitude to our honorable Director and Head of the Department for providing kind support and computational resources. "
    "First and foremost, I express my deepest gratitude to my [Supervisor Name], Department of Computer Science and Engineering, for providing "
    "exceptional guidance, encouragement, inspiration, and timely support throughout this B.Tech Project. I also thank all the faculty members "
    "of the Department of CSE and my peers for their strong support and constructive engagement."
)

add_title_p("ABSTRACT", size=16, bold=True, space_after=14)
add_body_p(
    "Invisible image watermarking is an essential technological primitive for provenance tracking, digital copyright verification, and synthetic "
    "media authentication in the era of generative AI. Emerging generative image restoration and diffusion autoencoding pipelines\u2014such as "
    "Variational Autoencoders (VAEs) and Latent Diffusion Models (LDMs)\u2014act as strong attack vectors that routinely strip invisible watermarks "
    "while preserving visual fidelity, yet existing watermarking schemes lack an analytical characterisation of the spectral mechanisms driving this degradation.\n\n"
    "This thesis formulates and investigates the hypothesis that generative VAE regeneration acts as a frequency-dependent degradation channel closely "
    "approximated by an analytical Wiener filter. We establish an orthogonal radial Fourier partitioning dividing the spatial Nyquist band [0, 0.5] "
    "cycles/pixel into 8 disjoint annular frequency bands.\n\n"
    "Across an empirical measurement campaign on COCO 2017: (1) We measure empirical transfer curves H(f) and fit the natural image power spectrum "
    "(P(f) ~ f^-2.660). We derive an analytical Wiener gain model G(f) = P(f)/(P(f) + N_eff) that predicts empirical cutoff frequencies f_c "
    "with R^2 in the range 0.877-0.910 across CompressAI qualities, and demonstrates monotonic scaling of N_eff with latent noise variance sigma^2 "
    "on the Stable Diffusion VAE. (2) In a 144,000-evaluation classical annular spread-spectrum parameter sweep (8 bands x 4 PSNR levels x 14 attack "
    "severities x 300 images, including unattacked baselines), we show that high-frequency bands (B5-B7) collapse to chance accuracy (~50%), whereas "
    "low-frequency bands (B0-B2) remain resilient, with the collapse boundary aligning with the theoretical Wiener cutoff f_c. "
    "(3) We develop an analytical Fourier surrogate filter that integrates Wiener degradation directly into the backward pass of a deep watermarking "
    "autoencoder in sub-millisecond time. (4) On a held-out benchmark of 64 test images (n=64, sampling error ~12 percentage points) against the "
    "Stable Diffusion VAE at matched embedding PSNR (40.0 dB), our classical low-band watermark (Band 2) achieves 73.97% bit accuracy at sigma=0.0 "
    "and 64.55% at sigma=0.20, and 98.24% bit accuracy (100% TPR at 0.35% FPR, tau=24) under CompressAI. The learned neural band-allocation model "
    "did not converge to above-chance performance, achieving 49.0-50.1% bit accuracy across all conditions\u2014a null result discussed in detail."
)

# Fixed: no "Keywords: Keywords:" duplication
add_body_p(
    "Invisible Digital Watermarking, Variational Autoencoders (VAE), Spectral Band Allocation, Wiener Filter, Stable Diffusion, "
    "Latent Compression, Fourier Analysis.",
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
    ("    1.3 Research Hypotheses & Objectives", "3"),
    ("    1.4 Key Contributions & Report Organization", "4"),
    ("Chapter 2: Literature Review & Theoretical Formulation", "5"),
    ("    2.1 Classical vs. Learned Digital Watermarking", "5"),
    ("    2.2 Generative Models and VAEs as Watermarking Attacks", "6"),
    ("    2.3 Spectral Degradation & Wiener Filter Formulation", "7"),
    ("Chapter 3: System Architecture & Proposed Methodology", "9"),
    ("    3.1 Orthonormal Annular Frequency Band Partitioning", "9"),
    ("    3.2 Transfer Function Characterisation Experiments", "10"),
    ("    3.3 Classical Annular Spread-Spectrum Sweep", "11"),
    ("    3.4 Learned Band-Allocation Network & Fourier Surrogate", "13"),
    ("Chapter 4: Experimental Results & Discussion", "15"),
    ("    4.1 Experimental Setup & Evaluation Protocols", "15"),
    ("    4.2 Natural Spectrum Fit and Wiener Gain Transfer Functions", "16"),
    ("    4.3 Classical Parameter Sweep & Cutoff Boundary", "18"),
    ("    4.4 Held-Out Final Benchmark", "20"),
    ("    4.5 Learned Model: Null Result", "23"),
    ("    4.6 Hypothesis Verification & Scientific Findings", "24"),
    ("Chapter 5: Conclusion & Future Scope", "26"),
    ("    5.1 Conclusion", "26"),
    ("    5.2 Threats to Validity & Limitations", "27"),
    ("    5.3 Future Research Directions", "28"),
    ("References", "29"),
]
for item, page in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.add_run(f"{item} " + "." * max(5, 75 - len(item) - len(page)) + f" {page}")

doc.add_page_break()

# ==========================================
# CHAPTER 1: INTRODUCTION
# ==========================================
add_heading_1("CHAPTER 1: INTRODUCTION")

add_heading_2("1.1 Background & Motivation")
add_body_p(
    "The rapid advancement of deep generative modeling has transformed synthetic media synthesis, image editing, and photographic reconstruction. "
    "Latent Diffusion Models (LDMs) such as Stable Diffusion, continuous flow matching architectures, and neural compression autoencoders (CompressAI) "
    "are now deployed at industrial scale. However, this transformative capability introduces unprecedented challenges to copyright protection, intellectual "
    "property tracking, and deepfake provenance verification. Malicious entities can effortlessly repurpose, modify, or misattribute high-value imagery."
)
add_body_p(
    "Digital image watermarking provides an essential technological safeguard by imperceptibly embedding a multi-bit cryptographic payload m into a host cover image x, "
    "producing a marked image x_w. The fundamental requirement of digital watermarking is imperceptible survivability: the watermark residual w = x_w - x must remain visually "
    "indistinguishable from clean photographic content (typically demanding Peak Signal-to-Noise Ratio PSNR >= 38 dB), "
    "while surviving downstream transmission, editing, and compression attacks."
)

add_heading_2("1.2 Problem Statement")
add_body_p(
    "While modern deep watermarking models (e.g., HiDDeN, StegaStamp, MBRS, TrustMark) demonstrate impressive resilience against legacy image processing operations "
    "(such as JPEG quantization, Gaussian blur, and spatial noise), they suffer catastrophic failure when confronted with generative autoencoding regeneration. "
    "When an image passes through a generative VAE bottleneck (such as an 8x spatial downsampling encoder, Gaussian latent sampling, and continuous decoder reconstruction), "
    "the output image maintains high visual quality, photorealistic textures, and sharp contours. However, the delicate spatial phase correlations and high-frequency "
    "perturbations injected by watermarking algorithms are completely sanitized."
)
add_body_p(
    "Existing deep watermarking approaches attempt to counter this vulnerability using heuristic end-to-end adversarial training. Unfortunately, backpropagating "
    "through heavy latent diffusion decoders or neural compression autoencoders incurs prohibitive computational overhead and promotes severe overfitting to specific architectures, "
    "failing to reveal the fundamental spectral mechanics governing watermark destruction."
)

add_heading_2("1.3 Research Hypotheses & Objectives")
add_body_p("This thesis formulates three testable scientific hypotheses:", bold_prefix="Hypotheses: ")
add_body_p(
    "The degradation imposed by a generative VAE on low-amplitude watermark residuals can be modeled analytically as a frequency-dependent "
    "Wiener reconstruction filter G(f) = P(f) / (P(f) + N_eff), where P(f) is the natural image power spectrum and N_eff is an effective noise parameter.",
    bold_prefix="• Hypothesis 1 (H1: Predictable Filter): "
)
add_body_p(
    "In classical spread-spectrum watermarking, the collapse boundary separating resilient from suppressed frequency bands after VAE regeneration "
    "aligns with the theoretical cutoff frequency f_c predicted by the Wiener model.",
    bold_prefix="• Hypothesis 2 (H2: Collapse Boundary Matches f_c): "
)
add_body_p(
    "Allocating watermark energy into low-frequency annular bands below the VAE cutoff horizon enables robust multi-bit extraction "
    "at matched embedding PSNR.",
    bold_prefix="• Hypothesis 3 (H3: Low-Band Advantage): "
)

add_heading_2("1.4 Key Contributions & Report Organization")
add_body_p(
    "To validate these hypotheses, we conduct an end-to-end mathematical and empirical study structured across five chapters: Chapter 2 formulates the analytical Wiener transfer "
    "gain model; Chapter 3 introduces the orthonormal annular frequency partitioning and neural surrogate architecture; Chapter 4 delivers the empirical results from our "
    "144,000-evaluation classical sweep and 5,376 held-out test evaluations on Stable Diffusion VAE and CompressAI, including a frank account of the learned model null result; "
    "Chapter 5 summarizes key conclusions, limitations, and future research directions."
)

# ==========================================
# CHAPTER 2: LITERATURE REVIEW
# ==========================================
add_heading_1("CHAPTER 2: LITERATURE REVIEW & THEORETICAL FORMULATION")

add_heading_2("2.1 Classical vs. Learned Digital Watermarking")
add_body_p(
    "Classical watermarking schemes operate primarily in transformed frequency domains. Cox et al. (1997) pioneered Discrete Cosine Transform (DCT) spread-spectrum watermarking, "
    "embedding pseudo-random carrier sequences into perceptually significant intermediate AC coefficients to evade high-frequency lossy compression while minimizing visual distortion. "
    "Discrete Wavelet Transform (DWT) schemes decompose images into multi-resolution octave sub-bands (LL, LH, HL, HH). While classical schemes offer mathematically rigorous blind detection, "
    "their capacity is inherently constrained by fixed spatial bases."
)
add_body_p(
    "Deep learning watermarking architectures (Zhu et al., 2018; Tancik et al., 2020; Bui et al., 2023) employ convolutional encoder-decoder networks trained end-to-end with "
    "differentiable distortion layers. However, these architectures treat attacks as spatial perturbations or spatial noise convolutions, completely overlooking the spectral "
    "transfer characteristics of modern generative autoencoders."
)

add_heading_2("2.2 Generative Models and VAEs as Watermarking Attacks")
add_body_p(
    "Recent benchmarks have revealed that generative regeneration poses a severe threat to invisible watermarks. W-Bench (2024) systematically evaluated state-of-the-art "
    "watermarking schemes against diffusion-based regeneration and demonstrated near-total failure across methods. Similarly, VINE (2024) proposed a learnable attack surrogate. "
    "In Latent Diffusion Models (Rombach et al., 2022), the autoencoding VAE maps a 256x256 image to a 32x32x4 latent space. During encoding, high-frequency spatial "
    "fluctuations are mapped onto the prior distribution and discarded during latent sampling, effectively acting as an aggressive low-pass reconstruction filter. "
    "Zhao et al. (2023) demonstrated that JPEG-style watermarks are particularly susceptible to such regeneration pipelines."
)

add_heading_2("2.3 Spectral Degradation & Wiener Filter Formulation")
add_body_p(
    "To understand why VAEs discard specific frequencies, we analyze natural photographic image statistics. Field (1987) demonstrated that the radially averaged power spectrum of natural images "
    "follows a strict power-law distribution:\n"
    "    P(f) = A * f^(-alpha)\n"
    "where f in [0, 0.5] denotes spatial frequency in cycles per pixel, alpha ~ 2.0 - 2.8, and A is an amplitude scaling constant."
)
add_body_p(
    "When a watermark residual w = x_w - x is added to cover image x, the observation entering the VAE is x_w = x + w. A linear Minimum Mean-Square Error (MMSE) Wiener reconstruction filter "
    "seeking to reconstruct clean natural image x under effective reconstruction noise N_eff applies the transfer gain:\n"
    "    G(f) = P(f) / (P(f) + N_eff) = 1 / (1 + (N_eff / A) * f^alpha)\n"
    "The theoretical 50% gain cutoff frequency f_c (where G(f_c) = 0.5) occurs precisely when signal power equals effective noise power P(f_c) = N_eff:\n"
    "    f_c = (A / N_eff)^(1 / alpha)"
)

# ==========================================
# CHAPTER 3: SYSTEM ARCHITECTURE
# ==========================================
add_heading_1("CHAPTER 3: SYSTEM ARCHITECTURE & PROPOSED METHODOLOGY")

add_heading_2("3.1 Orthonormal Annular Frequency Band Partitioning")
add_body_p(
    "To systematically probe and allocate watermark energy across frequency, we partition the 2D centered Fourier domain into B = 8 disjoint concentric annular bands over radial frequency range r in [0, 0.5]. "
    "The radial coordinate at Fourier coordinate (u, v) is defined as:\n"
    "    r(u, v) = sqrt( ((u - H/2)/H)^2 + ((v - W/2)/W)^2 )\n"
    "The annular boundaries are linearly spaced with bandwidth Delta r = 0.0625 cycles/pixel. Annular boolean masks M_b(u, v) satisfy exact partition of unity: sum(M_b) = 1 for all non-DC frequencies."
)

add_heading_2("3.2 Transfer Function Characterisation Experiments")
add_body_p(
    "In the transfer function characterisation study, band-limited noise probes w_b = iFFT2(M_b * FFT2(eta)) with unit RMS energy are embedded into 300 natural images at target PSNRs (35, 40, 45 dB). "
    "Images are passed through the attack channel x_att = Attack(x_w), and the empirical transfer gain H(b) = sqrt(E_out / E_in) is computed. "
    "Natural image spectrum parameters (alpha, log A) and Wiener parameter N_eff are fitted via Levenberg-Marquardt least-squares optimisation."
)

add_heading_2("3.3 Classical Annular Spread-Spectrum Sweep")
add_body_p(
    "In the classical parameter sweep, 32 orthogonal band-limited carrier sequences c_i in R^(HxW) are modulated by a 32-bit payload m in {-1, +1}^32. "
    "The spatial watermark w = sum(m_i * c_i) is embedded at target PSNR (35, 38, 41, 44 dB) with 8-bit integer quantisation. "
    "The decoder performs blind cross-correlation m_hat_i = sign(<x_att - mean(x_att), c_i>). "
    "Detection significance is evaluated against a null binomial distribution B(32, 0.5) with detection threshold tau = 24 (yielding FPR = 0.35%, "
    "i.e., P(k >= 24 | H_0) = sum_{k=24}^{32} C(32,k) * 0.5^32 = 0.0035)."
)

add_heading_2("3.4 Learned Band-Allocation Network & Fourier Surrogate")
add_body_p(
    "In the learned band-allocation study, a deep convolutional watermark encoder embeds a 32-bit message into a spatial residual r. "
    "A learnable band-allocation layer decomposes r into 8 annular bands and weights them using softmax logits g_b = exp(theta_b) / sum(exp(theta_j)). "
    "Crucially, instead of invoking the heavy SD VAE during training, an analytical Fourier surrogate filter applies G(f) directly in the Fourier domain: "
    "x_att = x + iFFT2(G(f) * FFT2(x_w - x)). "
    "This allows gradients dL / d theta_b to backpropagate directly into the frequency allocation weights in sub-millisecond execution time. "
    "The surrogate is a theoretical contribution in its own right, as it provides a computationally tractable proxy for the full VAE pipeline during training."
)

# ==========================================
# CHAPTER 4: EXPERIMENTAL RESULTS
# ==========================================
add_heading_1("CHAPTER 4: EXPERIMENTAL RESULTS & DISCUSSION")

add_heading_2("4.1 Experimental Setup & Evaluation Protocols")
add_body_p(
    "Experiments were conducted on the Microsoft COCO 2017 dataset. "
    "Transfer function characterisation and classical parameter sweep used 300 calibration images. "
    "The held-out final benchmark used 64 images drawn from the non-overlapping COCO test split "
    "(n=64; at this sample size each TPR estimate carries a sampling uncertainty of approximately +/-12 percentage points at 95% confidence, "
    "so small differences between methods in Tables 1 and 2 should be interpreted cautiously). "
    "Attacks evaluated include Stability AI's Stable Diffusion VAE (stabilityai/sd-vae-ft-mse) across latent noise levels sigma in [0.0, 0.20] "
    "and CompressAI Factorised Prior (bmshj2018) across quality factors q in [1, 8]. "
    "Target embedding fidelity was strictly matched at PSNR = 40.0 dB (+/- 0.2 dB)."
)

add_heading_2("4.2 Natural Spectrum Fit and Wiener Gain Transfer Functions")
add_body_p(
    "Fitting the natural image power spectrum across 300 photographic images yielded alpha = 2.660 +/- 0.296 and log A = -8.737, confirming the steep 1/f^2.66 power-law falloff."
)

add_figure("figures/fig1_transfer_functions.png", "Figure 1: Empirical vs. Fitted Wiener Transfer Functions H(f) across CompressAI quality factors (left) and Stable Diffusion VAE noise levels (right).")
add_body_p(
    "As shown in Figure 1, the measured transfer curves H(f) for CompressAI demonstrate good agreement with the analytical Wiener filter "
    "(R^2 = 0.877 at q=1, R^2 = 0.910 at q=2; fit quality degrades at higher qualities as the bottleneck becomes less aggressive). "
    "Stable Diffusion VAE exhibits severe high-frequency attenuation even at sigma=0.0 due to latent compression."
)

add_figure("figures/fig2_cutoff_and_scaling.png", "Figure 2: Theoretical vs. Measured Cutoff Frequency f_c (Left) and Effective Noise Parameter N_eff vs. Noise Variance sigma^2 on Stable Diffusion VAE (Right).")
add_body_p(
    "Figure 2 (Left) shows the relationship between the theoretical Wiener cutoff f_c = (A / N_eff)^(1/alpha) and the empirically measured 50% energy cutoff points. "
    "Figure 2 (Right) demonstrates that effective noise parameter N_eff scales monotonically with noise variance sigma^2, supporting Hypothesis H1."
)

add_heading_2("4.3 Classical Parameter Sweep & Cutoff Boundary")
add_figure("figures/fig3_classical_heatmaps.png", "Figure 3: Classical Annular Spread-Spectrum Parameter Sweep (144,000 total evaluations including unattacked baselines) showing Bit Accuracy Heatmaps across Bands and Strengths overlaid with Wiener Cutoff contours f_c (red dashed curve).")
add_body_p(
    "Figure 3 establishes the empirical frequency landscape across 144,000 total evaluations (134,400 attacked + 9,600 unattacked baselines). "
    "Across both CompressAI and SD VAE, high-frequency bands (B5-B7) collapse to random chance (~50% bit accuracy) under all non-trivial attack strengths. "
    "The red dashed line represents the analytical Wiener cutoff f_c(strength). "
    "The boundary separating high bit accuracy (>80%) from collapse aligns with the theoretical Wiener cutoff, supporting Hypothesis H2."
)

add_heading_2("4.4 Held-Out Final Benchmark")
add_body_p(
    "The 5,376 held-out test evaluations (64 images x 6 methods x 14 attack conditions) against Stable Diffusion VAE and CompressAI "
    "at matched PSNR = 40.0 dB are summarised in Table 1 and Table 2, and plotted in Figure 4. "
    "Detection threshold tau = 24 is used throughout, corresponding to FPR = 0.35% under the null binomial B(32, 0.5). "
    "Note that at n = 64 images, each TPR cell has a sampling uncertainty of approximately +/-12 pp."
)

add_figure("figures/fig4_held_out_benchmark.png", "Figure 4: Held-Out Final Benchmark Bit Accuracy Comparison on Stable Diffusion VAE across noise levels sigma (Panel A) and CompressAI across quality factors q (Panel B).")

# --- TABLE 1 --- (tau=24 TPR values)
add_heading_3("Table 1: Robustness on Held-Out Stable Diffusion VAE (n=64, Matched PSNR = 40.0 dB)")
p_t1_desc = doc.add_paragraph()
p_t1_desc.paragraph_format.space_after = Pt(4)
p_t1_desc.add_run(
    "Detection TPR at FPR = 0.35% (tau = 24/32). Bit accuracy averaged over 64 test images x 6 noise levels. "
    "Sampling uncertainty ~+/-12 pp per cell."
).italic = True

t1_data = [
    ["Method", "Metric", "sigma=0.00", "sigma=0.02", "sigma=0.05", "sigma=0.10", "sigma=0.15", "sigma=0.20"],
    ["Classical SS (Band 2)", "Bit Acc (%)\nTPR @ 0.35% FPR", "73.97%\n51.56%", "70.80%\n43.75%", "68.02%\n28.12%", "67.53%\n25.00%", "66.41%\n15.62%", "64.55%\n15.62%"],
    ["Classical SS (Band 0)", "Bit Acc (%)\nTPR @ 0.35% FPR", "57.96%\n6.25%", "57.76%\n6.25%", "57.47%\n3.12%", "57.23%\n4.69%", "56.74%\n6.25%", "56.84%\n6.25%"],
    ["Learned Control (Low: B0-2)", "Bit Acc (%)\nTPR @ 0.35% FPR", "55.76%\n6.25%", "55.62%\n3.12%", "55.42%\n0.00%", "56.25%\n1.56%", "56.05%\n1.56%", "54.98%\n0.00%"],
    ["Learned Control (Mid: B3-5)", "Bit Acc (%)\nTPR @ 0.35% FPR", "49.17%\n0.00%", "49.22%\n0.00%", "49.46%\n0.00%", "49.37%\n0.00%", "49.76%\n0.00%", "49.02%\n0.00%"],
    ["Learned Control (High: B6-7)", "Bit Acc (%)\nTPR @ 0.35% FPR", "52.39%\n0.00%", "52.34%\n0.00%", "52.29%\n0.00%", "52.00%\n1.56%", "52.25%\n1.56%", "50.88%\n1.56%"],
    ["Learned Main (Surrogate)", "Bit Acc (%)\nTPR @ 0.35% FPR", "49.95%\n0.00%", "49.90%\n0.00%", "49.76%\n0.00%", "49.76%\n0.00%", "49.80%\n0.00%", "48.93%\n0.00%"],
]

table1 = doc.add_table(rows=len(t1_data), cols=8)
table1.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t1_data):
    for c_idx, val in enumerate(row):
        cell = table1.cell(r_idx, c_idx)
        cell.text = val
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(9.5)
        if r_idx == 0:
            set_cell_background(cell, "D9D9D9")
            p.runs[0].bold = True
        elif c_idx == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

doc.add_paragraph().paragraph_format.space_before = Pt(8)

# --- TABLE 2 --- (tau=24 TPR values)
add_heading_3("Table 2: Cross-Model Generalisation on CompressAI VAE (n=64, Matched PSNR = 40.0 dB)")
p_t2_desc = doc.add_paragraph()
p_t2_desc.paragraph_format.space_after = Pt(4)
p_t2_desc.add_run(
    "Detection TPR at FPR = 0.35% (tau = 24/32). Quality factors q in [1, 8]. Sampling uncertainty ~+/-12 pp per cell."
).italic = True

t2_data = [
    ["Method", "Metric", "q=1", "q=2", "q=3", "q=4", "q=5", "q=6", "q=7", "q=8"],
    ["Classical SS (Band 2)", "Bit Acc (%)\nTPR (%)", "62.06%\n14.06%", "70.31%\n40.62%", "78.03%\n71.88%", "85.60%\n85.94%", "93.07%\n96.88%", "96.29%\n100.0%", "97.56%\n100.0%", "98.24%\n100.0%"],
    ["Learned Control (Low)", "Bit Acc (%)\nTPR (%)", "50.54%\n0.00%", "51.27%\n0.00%", "51.81%\n0.00%", "53.37%\n0.00%", "58.35%\n0.00%", "68.90%\n34.38%", "76.17%\n68.75%", "77.10%\n79.69%"],
    ["Classical SS (Band 0)", "Bit Acc (%)\nTPR (%)", "57.37%\n4.69%", "58.06%\n6.25%", "58.40%\n6.25%", "58.64%\n6.25%", "58.98%\n6.25%", "59.23%\n6.25%", "59.33%\n6.25%", "59.42%\n6.25%"],
    ["Learned Control (Mid)", "Bit Acc (%)\nTPR (%)", "49.36%\n0.00%", "49.66%\n0.00%", "49.37%\n0.00%", "49.32%\n0.00%", "49.37%\n0.00%", "49.37%\n0.00%", "49.37%\n0.00%", "49.27%\n0.00%"],
    ["Learned Control (High)", "Bit Acc (%)\nTPR (%)", "52.73%\n0.00%", "52.49%\n0.00%", "52.30%\n0.00%", "52.20%\n0.00%", "52.10%\n0.00%", "52.25%\n0.00%", "52.20%\n0.00%", "52.10%\n0.00%"],
    ["Learned Main (Surrogate)", "Bit Acc (%)\nTPR (%)", "50.00%\n0.00%", "49.56%\n0.00%", "50.00%\n0.00%", "50.10%\n0.00%", "50.05%\n0.00%", "49.95%\n0.00%", "50.00%\n0.00%", "49.90%\n0.00%"],
]

table2 = doc.add_table(rows=len(t2_data), cols=10)
table2.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t2_data):
    for c_idx, val in enumerate(row):
        cell = table2.cell(r_idx, c_idx)
        cell.text = val
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(8.5)
        if r_idx == 0:
            set_cell_background(cell, "D9D9D9")
            p.runs[0].bold = True
        elif c_idx == 0:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.runs[0].bold = True

doc.add_paragraph().paragraph_format.space_before = Pt(8)

add_heading_2("4.5 Learned Model: Null Result")
add_body_p(
    "The learned band-allocation network (Stage 1 CNN encoder + Stage 2 joint training with Fourier surrogate) failed to converge "
    "to above-chance bit accuracy on the held-out benchmark. Across all six conditions tested, the learned main surrogate achieves "
    "49.0-50.1% bit accuracy (Tables 1 and 2), indistinguishable from random guessing (50%). "
    "The fixed-band learned controls (Low, Mid, High) confirm the pattern: even with the correct frequency region pre-specified, "
    "the learned architectures achieve substantially lower TPR than the equivalent classical spread-spectrum baseline. "
    "Learned Control Low reaches 77.10% bit accuracy at CompressAI q=8 (comparable to classical Band 2), but achieves 0% TPR "
    "at tau=24 under the SD VAE at all tested noise levels, versus 15.62-51.56% TPR for classical Band 2."
)
add_body_p(
    "We attribute the null result to three factors: (a) the Fourier surrogate underestimates the nonlinear hallucination component "
    "of the VAE decoder that is not captured by a linear Wiener gain model; (b) 30 training epochs on a single T4 GPU (Google Colab) "
    "are insufficient for convergence of the joint encoder-decoder objective; and (c) the effective gradient signal through the surrogate "
    "is weak when the Wiener filter already attenuates the relevant frequency range near zero. "
    "The Fourier surrogate remains a sound theoretical contribution as a computationally efficient differentiable proxy, "
    "but the empirical neural watermarking results are a null result and should be interpreted as such."
)

add_heading_2("4.6 Hypothesis Verification & Scientific Findings")
add_body_p(
    "In Table 1, Classical Band 2 achieves the highest robustness across all noise levels, reaching 73.97% bit accuracy at sigma=0.0 and maintaining 64.55% "
    "even under extreme noise (sigma=0.20), with TPR of 51.56% at sigma=0.0 (FPR = 0.35%). "
    "High-frequency bands (B6-B7: ~52% bit accuracy) and mid-band controls (B3-5: ~49% bit accuracy) collapse to near-random performance, "
    "confirming Hypothesis H3.",
    bold_prefix="1. Low-Band Superiority (H3 supported): "
)
add_body_p(
    "While Band 0 ([0.0, 0.0625]) experiences minimal attenuation through the Wiener filter, its close proximity to DC exposes the watermark to heavy host-image interference. "
    "Band 2 ([0.125, 0.1875]) achieves the optimal compromise: low enough in frequency to survive VAE reconstruction filtering, yet high enough to evade strong low-frequency host image interference.",
    bold_prefix="2. The Sweet Spot of Band 2: "
)
add_body_p(
    "The transfer function heatmaps in Figure 3 show that the boundary between high and low bit accuracy in the sweep aligns with the theoretical f_c contour, "
    "confirming Hypothesis H2. Note that this supports the weaker claim that the collapse boundary matches f_c; "
    "whether the single best-performing band is always the one closest to f_c requires a more targeted plot (argmax band vs. f_c across attack strengths) "
    "which is deferred to future work.",
    bold_prefix="3. Collapse Boundary Alignment (H2 supported): "
)
add_body_p(
    "The Wiener model achieves R^2 = 0.877-0.910 across moderate CompressAI quality factors (q=1, 2), "
    "and N_eff scales monotonically with sigma^2 on the SD VAE, confirming H1. "
    "Fit quality degrades at high quality factors (q >= 4) where the bottleneck is less aggressive and model nonlinearities dominate.",
    bold_prefix="4. Wiener Model Validity (H1 supported with caveat): "
)

# ==========================================
# CHAPTER 5: CONCLUSION
# ==========================================
add_heading_1("CHAPTER 5: CONCLUSION & FUTURE SCOPE")

add_heading_2("5.1 Conclusion")
add_body_p(
    "This thesis presented an empirical and theoretical investigation of invisible digital watermarking under generative VAE regeneration attacks. "
    "By combining orthonormal annular Fourier decomposition with analytical Wiener filter modelling, we demonstrated that generative autoencoding behaves "
    "as an aggressive low-pass reconstruction filter governed by natural image statistics P(f) ~ f^-alpha.\n\n"
    "Through a 144,000-evaluation empirical sweep and held-out benchmarking on Stable Diffusion VAE and CompressAI (64 test images), we show that watermark "
    "allocation in annular Band 2 (0.125 - 0.1875 cycles/pixel) delivers optimal robustness, achieving up to 98.24% bit accuracy on CompressAI and 73.97% "
    "on Stable Diffusion VAE at 40.0 dB PSNR. The collapse boundary between resilient and suppressed bands aligns with the theoretical Wiener cutoff f_c. "
    "Our analytical Fourier surrogate provides a computationally efficient differentiable proxy for VAE simulation during training. "
    "However, the learned neural band-allocation component did not improve over classical baselines within the training budget available, a null result "
    "that motivates future work with larger compute and a more expressive surrogate."
)

add_heading_2("5.2 Threats to Validity & Limitations")
add_body_p(
    "1. Small Held-Out Sample: The final benchmark used 64 test images, yielding approximately +/-12 percentage points of sampling uncertainty per TPR cell. "
    "Differences smaller than this should not be over-interpreted.\n"
    "2. Linearity Assumption: The Wiener model captures radially symmetric amplitude degradation (R^2 = 0.877-0.910 at low quality factors), "
    "but generative VAE decoders also introduce localised phase jitter and nonlinear perceptual hallucinations not modelled by a linear filter.\n"
    "3. Perceptual Metrics: Only PSNR was matched in the embedding constraint. Full SSIM and LPIPS evaluation is deferred to future work.\n"
    "4. Resolution Constraints: Experiments were conducted at 256x256. While frequency bounds normalise naturally by cycles per pixel, "
    "scaling to ultra-high resolution shifts absolute pixel frequencies.\n"
    "5. Learned Model Convergence: The neural watermarker was trained for only 30 epochs on a T4 GPU, which was insufficient for convergence."
)

add_heading_2("5.3 Future Research Directions")
add_body_p(
    "1. Rerun on Full 500 Images: Increasing the held-out benchmark from 64 to 500 images would reduce sampling error to approximately +/-4 pp "
    "and confirm whether the Band 2 advantage over Band 0 is statistically significant.\n"
    "2. Nonlinear Phase Modelling: Extending the Wiener gain model to incorporate circular complex phase dispersion and nonlinear decoder effects.\n"
    "3. Learned Model with Extended Training: Training the neural band-allocation network for 300+ epochs with a larger batch size and a refined surrogate "
    "that captures VAE decoder nonlinearities.\n"
    "4. Latent-Space Direct Watermarking: Embedding directly within diffusion latent tokens prior to latent decoding.\n"
    "5. Video Generative VAEs: Extending annular spectral allocation to 3D spatiotemporal Fourier volumes for generative video regeneration models."
)

# ==========================================
# REFERENCES
# ==========================================
add_heading_1("REFERENCES")
references = [
    "[1] Cox, I. J., Kilian, J., Leighton, F. T., & Shamoon, T. (1997). Secure spread spectrum watermarking for multimedia. IEEE Transactions on Image Processing, 6(12), 1673-1687.",
    "[2] Zhu, J., Kaplan, R., Johnson, J., & Fei-Fei, L. (2018). HiDDeN: Hiding images with deep networks. European Conference on Computer Vision (ECCV), 657-672.",
    "[3] Tancik, M., Mildenhall, B., & Ng, R. (2020). StegaStamp: Invisible hyperlinks in physical photographs. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2117-2126.",
    "[4] Bui, T., Agarwal, S., & Collomosse, J. (2023). TrustMark: Universal watermarking for arbitrary resolution images. arXiv preprint arXiv:2311.18297.",
    "[5] Rombach, R., Blattmann, A., Lorenz, D., Esser, P., & Ommer, B. (2022). High-resolution image synthesis with latent diffusion models. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 10684-10695.",
    "[6] Ballé, J., Laparra, V., & Simoncelli, E. P. (2018). Variational image compression with a scale hyperprior. International Conference on Learning Representations (ICLR).",
    "[7] Jia, Z., Fang, H., & Zhang, W. (2021). MBRS: Enhancing robustness of DNN-based watermarking via mini-batch of real and simulated JPEG compression. ACM International Conference on Multimedia (MM), 41-49.",
    "[8] Wiener, N. (1949). Extrapolation, interpolation, and smoothing of stationary time series. MIT Press.",
    "[9] Field, D. J. (1987). Relations between the statistics of natural images and the response properties of cortical cells. Journal of the Optical Society of America A, 4(12), 2379-2394.",
    "[10] Lin, T. Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P., & Zitnick, C. L. (2014). Microsoft COCO: Common objects in context. European Conference on Computer Vision (ECCV), 740-755.",
    "[11] Zhao, S., Wang, A., Yu, S., & Lyu, S. (2023). Invisible image watermarks are provably removable using generative AI. arXiv preprint arXiv:2306.01953.",
    "[12] W-Bench Authors. (2024). W-Bench: A benchmark for watermarking robustness under generative regeneration. (Preprint / workshop paper; full citation to be confirmed upon publication.)",
    "[13] An, T., et al. (2024). VINE: A versatile invisible watermark eraser via diffusion models. arXiv preprint arXiv:2410.14745.",
]
for ref in references:
    p_ref = doc.add_paragraph()
    p_ref.paragraph_format.space_after = Pt(4)
    p_ref.add_run(ref)

# Save document
doc.save(str(DOCX_OUT))
print(f"✓ Successfully generated Word document: {DOCX_OUT.resolve()} (Size: {DOCX_OUT.stat().st_size / 1024:.1f} KB)")
