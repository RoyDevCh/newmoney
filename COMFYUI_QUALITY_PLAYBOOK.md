# ComfyUI Quality Playbook

Target host:
- GPU: `AMD Radeon RX 9060 XT`
- Runtime: `DirectML`
- RAM budget: `24 GB`
- Current checkpoint: `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`

Constraints:
- DirectML is less forgiving than CUDA.
- SDXL-class models can spike both VRAM and system RAM.
- On this host, keep ComfyUI as the main heavy process and stop unused AdsPower profiles after automation runs.

## Baseline Runtime

Recommended boot command:

```powershell
py -3 start_comfy_directml.py --extra-args "--disable-auto-launch"
```

If memory pressure increases:

```powershell
py -3 start_comfy_directml.py --extra-args "--disable-auto-launch --cpu-vae"
```

Use `--cpu-vae` only when needed. It reduces GPU pressure but is slower.

## Best-Quality Still Image Preset

Use this first for premium cover images and Xiaohongshu/Bilibili key art.

- Model: `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`
- Width x Height:
  - Xiaohongshu: `832x1216`
  - Zhihu cover / WeChat header: `1344x768`
  - Bilibili cover: `1536x864`
  - Universal square asset: `1024x1024`
- Sampler: `DPM++ 2M Karras`
- Scheduler: `karras`
- Steps: `30-36`
- CFG: `5.0-6.5`
- Seed: fixed per batch when comparing variants
- Batch size: `1`

Second pass for hero assets:

- Latent upscale: `1.5x`
- Denoise: `0.22-0.30`
- Extra steps: `12-18`

This gives better texture and typography-safe space than pushing one giant first pass.

## Memory-Safe Production Rules

- Never run large AdsPower batches while ComfyUI is rendering.
- Prefer one render at a time.
- Keep `batch_size=1`.
- Prefer `832x1216` or `1024x1024` over very large native renders.
- Use upscale second pass instead of starting at `1536+` on the first pass.
- After browser tests or publishing jobs:

```powershell
py -3 release_browser_memory.py --all --base-url http://local.adspower.net:50361
```

## Prompt Design For Monetizable Content

General rules:
- Avoid generic "beautiful girl / cool cyberpunk wallpaper" prompts.
- Build prompts around a platform use case: cover image, product mood board, comparison card background, expert brand visual.
- Leave negative space for title overlays.
- Ask for one focal subject, one lighting logic, one camera logic.

Template:

```text
[subject], [commercial angle], [lighting], [camera], [composition], [surface/material detail], [mood], [background restraint], space for editorial text, premium social media cover, highly detailed, realistic, polished color grading
```

Negative prompt:

```text
low quality, blurry, extra fingers, malformed hands, duplicate objects, text, watermark, logo, noisy background, clutter, oversaturated, cheap poster look
```

## Platform-Specific Visual Directions

### Xiaohongshu

Goal:
- high save rate
- immediate visual desirability
- clean layout for short headline overlay

Prompt direction:
- premium desk setup
- warm daylight
- tactile product surfaces
- one emotional anchor color

Example:

```text
premium AI workspace setup, slim laptop, soft daylight through window, warm neutral palette, tidy desk, notebook and coffee as secondary props, shallow depth of field, editorial composition, realistic materials, clean premium productivity lifestyle, space for title overlay
```

### Zhihu

Goal:
- credible, expert, data-driven
- less emotional, more authority

Prompt direction:
- analytical desk scene
- monitor dashboards
- restrained palette
- minimal clutter

Example:

```text
professional AI automation analysis desk, monitor with abstract workflow charts, cool neutral lighting, documentary realism, balanced composition, subtle depth, premium editorial tech illustration, clean background, authority and trust, space for headline
```

### Douyin

Goal:
- strong first-frame stop power
- high contrast focal point

Prompt direction:
- one dramatic object
- bold light split
- bigger subject scale

Example:

```text
dramatic AI productivity command center, bold rim lighting, strong contrast, central focal screen, intense commercial framing, cinematic tech realism, sharp details, fast-scroll stopping thumbnail, space for short hook text
```

### Bilibili

Goal:
- curiosity + niche taste
- stronger narrative atmosphere

Prompt direction:
- darker but readable scene
- evidence board / archive desk / lab mood
- richer texture

Example:

```text
investigation archive desk about AI automation, pinned notes and screens, moody cinematic lighting, textured surfaces, narrative depth, premium documentary thriller mood, highly detailed, balanced composition, space for title and badge
```

## Recommended Content Categories

Best fit for the current model stack:
- AI productivity covers
- hardware/desk setup visuals
- documentary-style tech thumbnails
- soft commercial lifestyle scenes

Avoid for now:
- dense infographic generation inside the model
- exact branded product replicas
- multi-character scenes with complex hand poses

## Quality Upgrade Gaps

Current model inventory is thin:
- Checkpoints: `1`
- LoRAs: `0`

Highest ROI additions later:
- one clean product-photography SDXL LoRA
- one editorial lighting LoRA
- one typography-safe composition LoRA

Without those, prioritize composition and lighting discipline over stylistic variety.
