# Content Quality Standard (Monetization Grade)

This file defines minimum standards for publishable content.

## Pass Criteria

- Overall score >= 78/100
- No truncation, no missing fields
- No unverifiable hard claims (precise numbers without source/test context)
- Platform fit must pass (length, tone, CTA behavior)

## Hard Fail (reject directly)

- Body is incomplete/truncated
- Fabricated hard facts presented as certainty
- Excessive clickbait words without useful payload
- Generic CTA with no platform action

## Platform Targets

- Zhihu: structured analysis + source/testing context + practical checklist
- Xiaohongshu: scene-based practical notes + concise emotional value + save/follow CTA
- Douyin: strong 3-second hook + short spoken rhythm + one clear takeaway per segment
- Bilibili: evidence-first narrative + segmented outline + test context transparency

## Rewrite Priority

1. Factual safety (source signal / uncertain claim softening)
2. Hook strength and relevance
3. Platform style adaptation
4. Conversion CTA

## Output Contract

Always output JSON with fields:
platform, title, hook, body, cta, tags
