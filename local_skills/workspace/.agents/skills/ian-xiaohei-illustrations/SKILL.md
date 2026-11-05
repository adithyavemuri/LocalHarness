---
name: ian-xiaohei-illustrations
description: Plan Ian/Xiaohei-style English article illustrations and prepare image prompts; generate or edit only when an actual image tool is connected and the user requests it.
license: MIT
---

# Ian/Xiaohei illustrations with a local model

Adapted from https://github.com/tojileon/ian-xiaohei-illustrations-en.
See LICENSE.txt for the upstream notice. This compact adapter is not the full
upstream skill bundle. It supports the style and planning workflow without
assuming Codex's built-in `image_gen` exists in every agent client.

Use this style only for explicit Ian/Xiaohei requests or when the user accepts
it. For generic artwork or scientific diagrams, follow the requested style and
accuracy requirements instead.

Read the supplied article and select its main claims, transitions or metaphors.
For a short article, propose one to three images; choose additional scenes only
when they convey distinct ideas. Give a shot list with placement, core idea,
composition, character action and short English labels.

Prepare one prompt per image:

- A horizontal 16:9 frame, white background, black hand-drawn lines and generous
  empty space, with sparse red, orange or blue handwritten annotations.
- Xiaohei is a solid black creature with white dot eyes, thin legs and a blank
  expression. Make the character perform the central action.
- Explain one idea through a fresh visual metaphor. Keep labels short and avoid
  title blocks, dense slides, decorative characters and recycled compositions.

Before generation, check the connected tools. A text model and a text-chat API
cannot render a PNG. When an image backend is missing, return the shot list and
ready-to-use prompts and label generation as blocked. Do not invent an
`image_gen` call or claim that a prompt is a generated image.

When the user requests generation or editing and an image tool is connected,
use that tool's actual schema. Preserve reference images and requested edits.
Generate scenes separately, then inspect the images when visual inspection is
available. Check aspect ratio, white space, character action, legible labels
and the requested meaning; disclose any checks you could not perform.

Save actual outputs under `assets/<article-slug>-illustrations/` in the
workspace, using sequential filenames. Preserve existing files. Report only
paths or attachments that the tool actually produced.
