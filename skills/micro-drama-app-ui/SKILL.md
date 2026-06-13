---
name: micro-drama-app-ui
description: Use when designing or generating UI for the micro-drama app from confirmed project docs. Applies to short drama app screens such as Me page, home, playback-adjacent pages, wallet, My List, settings, and similar app surfaces. Use this when the user wants a new UI concept, a redesign, a design prompt, or a generated screen based on docs/prd, docs/architecture, and docs/原始需求, while explicitly ignoring root-level historical markdown drafts.
---

# Micro Drama App UI

Use this skill for this project's app UI design work.

This skill is primarily a style system distilled from the `Me` page work. It summarizes the visual language, product tone, density, and monetization hierarchy that the `Me` page established successfully.

Use this style system as the default visual constraint set for this project's UI generation work.

Reuse the `Me` page's style language across pages as a strict style constraint set, but do not mechanically copy the `Me` page structure onto pages whose PRD requires a different layout.

## Scope

Use only these project sources as truth:

- `docs/prd/`
- `docs/architecture/`
- `docs/原始需求/`

Do not use root-level historical markdown files in `docs/` as design truth unless the user explicitly tells you to.

## Canonical Style Anchor

For this project, the strongest current visual anchor is:

- `docs/design-review/market-inspired-my-page/my-page-market-inspired.html`

Treat this file as the current highest-fidelity style anchor for shipped-product feel, density, card hierarchy, text restraint, and warm-dark entertainment polish.

If a future generated page follows the written rules but still drifts away from this anchor's product feel, the result is still wrong.

This anchor controls style language, not page IA:

- inherit its visual tone, density, typography restraint, color balance, and module hierarchy discipline
- do not blindly copy its exact `Me` page structure onto unrelated pages whose PRD requires different content

## Goal

Produce UI that feels like a successful short-drama app, not a generic SaaS dashboard and not a random design exercise.

More specifically, this skill turns the `Me` page's mature short-drama product style into reusable constraints.

Target vibe:

- content-first entertainment product
- premium but commercially practical
- mobile-native
- strong emotional atmosphere
- VIP and wallet feel valuable
- fast scan hierarchy

The closest market references are products in the same family as ReelShort, ShortMax, and RapidTV.

## Core Design Thesis

For this product, the UI must feel like:

- a dark entertainment app, not a utility console
- a monetized streaming surface, not a marketing poster
- emotionally warm and dramatic, not cold, flat, or overly technical
- visually premium, but still dense enough to feel like a real shipped app

This project's hard design core is derived from mature short-drama app patterns and must be treated as a market-proven direction, not a subjective styling preference.

This hard design core is:

- content atmosphere
- VIP
- wallet
- fast-entry navigation
- dark entertainment product feel
- high-fidelity shipped-app realism
- dense mobile layout aligned to mature successful short-drama apps

If a design does not make these five things obvious in the first screen, it is missing the target and drifting away from the design logic used by successful short-drama apps.

All design choices must align toward mature short-drama app thinking rather than toward generic consumer-app or tool-app conventions.

When generating through external tools such as Open Design or Stitch, explicitly instruct them to align to the canonical style anchor above, not only to the abstract rules.

Style-transfer boundary:

- transfer the `Me` page style system
- do not mechanically transfer the `Me` page structure

## Source Compression Workflow

Before generating or designing a screen:

1. Read the relevant PRD section for the target page.
2. Read matching architecture or DB notes only if they affect visible UI states.
3. Read original requirement screenshots or image descriptions for layout hints.
4. Compress all of that into:
   - page purpose
   - default state
   - required sections
   - forbidden sections
   - state changes
   - monetization emphasis
   - design tone

Do not dump raw PRD language directly into prompts when shorter product language will do.

## Product UI Rules

### Hard Standards

These four standards are non-negotiable and may only tighten further in future iterations:

1. Card layout: VIP and wallet are the primary cards. Ordinary entry areas stay row-based when the confirmed product pattern is list-first. Do not pile up unnecessary sub-cards. Card height and spacing stay compact.
2. Text strategy: all visible copy must be formal shipped-product copy. Keep it short, direct, and scannable. Remove explanatory, proposal-style, workshop-style, and draft-style wording.
3. Color strategy: use a warm dark entertainment base. Use gold / amber to emphasize VIP and wallet. Keep ordinary utility rows visually calmer.
4. Visual effects: use light glow, soft gradients, and restrained shadow only to support shipped-product polish. Do not use effects that introduce concept-art, demo, or temporary-styling feel.
5. Interaction treatment: design for a mobile app preview, not a desktop web page. Do not use hover zoom, hover overlays, hover reveal states, or hover-only affordances as visible polish.

If a result drifts away from any of these four standards, it is wrong for this project even if it still looks attractive.

### Density Is A Hard Constraint

In this project, `compact` is not a loose preference. Treat it as a hard product-layout rule.

- First screen must prioritize actionable consumption density over decorative display.
- A single hero, banner, or oversized poster must not dominate so much of the first screen that monetization and next-click paths become secondary.
- On discovery or home-like pages, the first screen should already expose:
  - at least one strong content entry area
  - at least one strong monetization or asset-adjacent area such as `VIP`, `Wallet`, `Top-up`, `Gift`, `Unlock`, or equivalent
  - immediate continuation into content rails or lists
- Do not use large headings, oversized poster blocks, or luxury spacing to simulate polish.
- If the page feels like a cinematic content showcase before it feels like a consumption product, it is wrong.
- If a generator tends to produce elegant-but-loose layouts, explicitly prompt one level tighter than the target result.

### 1. Entertainment First

- Use a dark or warm-dark base.
- Every app screen background must carry the same short-drama cinema feel: deep wine-brown / cinema-black base, subtle gold-red ambient light, restrained vignette, and content-first hierarchy.
- Every mobile screen prototype must include a perceptible but restrained cinema background effect. This is mandatory, not optional decoration.
- Low-frequency ambient background flow should be used to strengthen entertainment atmosphere, but it must stay behind content, preserve readability, avoid showy motion, and respect reduced-motion settings.
- The background effect must be screen-level, not only a local card effect: deep wine / cinema-black base, gold-red ambient light, subtle vignette, and slow background-layer movement.
- Utility, settings, feedback, history, legal, and form pages still need this cinema background effect; low-attraction page content does not mean the background may fall back to plain system black or workbench dark.
- Build atmosphere with tonal depth, glow, poster-like accents, and cinematic hierarchy.
- Let the screen feel tied to video, episodes, and drama consumption.
- The page must feel like the user is still inside a drama product, not like they switched into a utility settings shell.

### 2. Strong Monetization Hierarchy

VIP and wallet are not side notes. They must feel important.

- VIP must feel aspirational and premium.
- Wallet must feel actionable and close to unlock behavior.
- Coins must feel tangible and visually valuable.
- VIP and wallet must appear before low-value utility navigation when the page contains both monetization modules and utility navigation.
- Their visual weight must be clearly stronger than ordinary list rows.
- If a page does not literally contain VIP or wallet modules, the equivalent monetization entry must still be clearly foregrounded.

### 3. Content Memory

Short-drama apps often imply recent content, progress, or drama context even on account screens.

- Use content memory only when the PRD, architecture state, or source reference supports it.
- Do not violate the PRD by inventing unsupported modules.
- Use subtle content atmosphere instead of empty decorative gradients.

### 4. Mobile Product Density

- The page must feel optimized for thumb use.
- Tap targets must be generous.
- Hierarchy must be understandable in one quick glance.
- Avoid empty luxury spacing that makes the product feel unfinished.
- Fast-entry navigation matters: users must instantly know the next tap target.
- Density must align to mature short-drama app production screens, not airy prototype layouts.
- When a reference screenshot exists, use it as a density and proportion calibration baseline.
- When no direct screenshot exists, preserve the same mature short-drama product density rather than relaxing into generic mobile UI spacing.
- Users should not need to visually “wait through” a large decorative section before finding high-frequency actions.

### 5. High-Fidelity Standard

- The screen must feel like a shipped mobile product, not a wireframe, pitch deck, or concept poster.
- Reduce oversized typography, oversized cards, and exaggerated padding that create a low-fidelity prototype feel.
- If the page looks readable only because everything is large, the density is wrong.

## Visual System

This project's reusable visual summary is defined from four angles:

- card layout
- text strategy
- color strategy
- visual effects strategy

Default palette:

- base: charcoal, espresso, black-cherry, or warm near-black
- accent: amber, gold, coin-yellow
- support accents: muted blue or warm coral only when functionally useful

Preferred base direction for this project:

- deep champagne-brown cinema dark
- warm black with subtle golden undertone
- dark wine-brown black

Avoid letting the base drift into:

- neutral gray-black
- blue-gray black
- system-dark utility black

Avoid:

- purple-heavy palettes
- white-first productivity look
- pastel soft-app treatment
- enterprise dashboard styling

Typography:

- use modern mobile system-friendly display and body fonts
- headlines must feel entertainment-grade and compact
- labels must scan fast
- avoid editorial serif systems unless the user explicitly wants them
- default to slightly smaller text than generic prototypes when matching dense consumer-app screenshots
- typography and spacing must feel productized and compact, even when no direct screenshot exists

Text strategy summary:

- product text must be short, literal, and release-grade
- remove explanatory or atmospheric filler when the source product pattern is concise
- titles must be clear and fast to scan, not oversized
- secondary text must be limited and only used where the real product pattern supports it
- if a module is already visually obvious, do not explain it with extra copy
- account, VIP, wallet, and navigation labels must follow formal shipped-product wording, not concept-deck or draft wording
- do not write copy that explains the design intent, emotional intent, or user journey unless the confirmed product copy explicitly requires it
- when multiple valid labels exist, choose the shorter and more product-like label
- long plot-synopsis style secondary copy should be reduced or removed unless the source pattern clearly uses it
- this is a hard standard and text choices may only converge further in this direction, never away from it

Mobile label copy rules:

- Treat every visible label, title, tab, row entry, button, link, badge, and helper line as final production English UI copy unless the PRD explicitly specifies another language.
- Labels and navigation entries should normally be 1-2 words. Action buttons should normally be 1-3 words and must not exceed 4 words unless the PRD text is legally required.
- Use simple, common, precise words. Choose the shortest standard product term that keeps the meaning clear.
- Use verbs for actions and CTAs: `Sign in`, `Top-up`, `Unlock`, `Watch`, `Continue`, `Add`, `Save`.
- Use nouns or short noun phrases for destinations and states: `VIP`, `Wallet`, `My List`, `Settings`, `History`.
- Drop articles, filler, and ceremony: prefer `Import Files` over `Import a File`, `Sign in` over `Sign in to continue watching and keep your account synced`.
- Do not write labels that explain the interface, product strategy, emotional intent, or user journey. If context is visually obvious, delete the helper copy.
- Keep labels and short helper copy to one line on mobile whenever possible. If copy wraps, shorten it before resizing the UI.
- Keep casing consistent with the surface: action buttons and links use sentence case; destination/navigation labels may use title case when matching the established app pattern.
- Links must name the destination or immediate outcome in no more than 4 words, for example `Service Agreement`, `Privacy Agreement`, `View details`.
- Tooltips are rarely needed in mobile previews. If a tooltip-like hint is required, keep the label to 1-3 words and the explanation to one short sentence.
- Reject explanatory drafts such as `Unlock premium short-form drama`, `Keep your account synced`, `Explore all your benefits`, `Tap here to continue`, and `Please click Next` unless the PRD or legal copy requires them.

Shapes:

- rounded cards and pill controls are part of this product's shipped-app language
- corners must feel polished and consumer-product ready
- avoid boxy admin-panel geometry
- avoid overusing nested cards and decorative sub-blocks inside already clear modules
- compact secondary entry groups must not become plain workbench dividers; keep a dark cinema base, subtle entertainment glow, and semantic multi-color icons even when the layout is row-based

Card layout summary:

- cards must feel like real app modules, not stacked concept blocks
- VIP and wallet are primary cards and must carry the strongest visual weight
- row-based entry areas must stay row-based when the product pattern is list-first
- reduce unnecessary nested panels, chips, and sub-cards
- do not create hierarchy by wrapping a large card around several smaller cards; use single-layer entry rails, list rows, dividers, or icon+label groups for secondary actions
- do not add large outer panels around brand areas, form fields, settings lists, history entry groups, or upload areas just to create atmosphere; cinema feel must come from the page background, module material, and single-layer separation
- spacing between cards must be compact enough to feel production-ready
- card height must be controlled so the page feels dense and efficient rather than airy
- on home or discovery pages, banner or hero areas must stay subordinate to the surrounding consumption structure
- if a layout choice makes the screen look like a draft, a showcase, or a design exercise, reject it
- card layout must strictly follow formal shipped-product standards
- this is a hard standard and layout choices may only converge further in this direction, never away from it

Generator-specific note:

- Stitch often drifts toward spacious premium layouts. When using Stitch, explicitly ask for tighter vertical rhythm, smaller hero height, smaller headings, and a deeper champagne-dark base than the first-pass instinct.
- Stitch also tends to introduce desktop-web hover polish. Explicitly forbid hover zoom, hover reveal overlays, hover color swaps, and hover-only emphasis unless a reference screenshot proves they exist.

Color strategy summary:

- use a warm dark base to maintain entertainment atmosphere
- bias specifically toward a deeper champagne-tinted dark cinema base instead of a neutral dark base
- apply the cinema base to the whole screen, not only to isolated modules; the background must not read as a plain utility workbench, neutral system black, or admin surface
- every screen must use the project cinema background recipe: deep wine / cinema-black base, gold-red ambient light, restrained vignette, and slow background-layer flow
- let gold / amber own VIP and wallet emphasis
- use accent colors sparingly and functionally
- keep utility rows darker and calmer than monetization modules
- avoid decorative rainbow accents or excessive color variety
- color must support hierarchy first, style second
- Glow-on-Dark Wallet and Reward Cards (Anti-Whiteout Rule): In high-value scenarios such as sign-in rewards and wallet balances, avoid large solid-light (white or bright yellow) card backgrounds which break the dark cinema base. Use a "warm dark base + gold/amber/pink glowing borders + high-contrast text" formula to draw clicks without ruining the theater environment.
- this is a hard standard and color choices may only converge further in this direction, never away from it

Visual effects strategy summary:

- use subtle glow, soft gradients, and restrained contrast instead of heavy decoration
- visual effects must support premium feel without looking like a concept render
- animated background effects, when used, must be slow ambient light movement only; never animate content readability, transaction rows, primary CTAs, or essential controls
- screen-level cinema background flow is required for prototypes, but it must remain low-frequency and background-only
- if reduced motion is enabled, the animation stops while the static cinema base, gold-red ambient light, and vignette remain visible
- reject obvious scan waves, concentric ripples, particle rain, neon flashing, broad white light bands, or any background highlight that lowers text contrast
- avoid effects that make the screen look blurry, noisy, or overbuilt
- keep shadows soft and supportive, not theatrical
- use visual polish to reinforce a shipped-app feel, not to compensate for weak layout
- every visual effect must strictly meet production-release standards and must not look like temporary styling layered onto unfinished product structure
- mobile preview pages should not rely on mouse-hover effects for polish
- Mobile-Native Tap Resistance Feedback: Never rely on mouse-hover effects for click targets. All buttons, grids, and check-in tiles must support active pressing feedback (such as scaling down to 0.96-0.98 with 5-10% opacity dimming) to guide developers implementing GestureDetector or InkWell in Flutter.
- this is a hard standard and visual-effect choices may only converge further in this direction, never away from it

Asset strategy summary:

- shared prototype icons, illustrations, and background images must live under `docs/design-review/ui-prototype/assets/` with source and license notes
- do not scatter duplicate page-local assets across page family directories
- do not hotlink external images in prototype HTML; download approved network resources into the shared asset directory first
- when a UI needs vivid entertainment or coin/reward texture, prefer licensed PNG / WebP network resources with strong image quality instead of ad-hoc handmade low-fidelity icons or plain line SVGs
- icon assets must feel like mature short-drama app assets, not mobile game loot items; allow brightness, soft 3D volume, and cinema polish, but avoid excessive gems, spark bursts, exploding gift boxes, trophy-drop effects, and cartoon game props
- 3D Tangible Asset Representation: Any asset-related icons (coins, chests, badges) must feature prominent volume and metallic depth. When drawn with CSS, employ multi-layered radial gradients, inset shadows, and sliced golden highlight accents. Avoid flat, solid shapes or cheap cartoonish game-loot textures.
- Treat icon creation as a small visual asset system, not as isolated emoji replacement. Before creating or swapping icons, define semantics, use cases, hierarchy, size range, static/animated needs, reuse locations, and source/license path.
- Icon creation must include external resource research before production: search mature app references, licensed icon libraries, and high-quality PNG/WebP resources; capture useful semantics, material direction, color behavior, and license constraints before deciding whether to adopt, adapt, or generate.
- Decision order is mandatory: if a quality-approved, clearly licensed PNG/WebP asset can be obtained from the web, download it into the shared assets directory and use it instead of making a new one. Generate or hand-create icons only when no suitable licensed resource exists, licensing blocks use, or the project requires a custom coherent set.
- Icon families must be designed and reviewed as a set. A wallet/reward/consumption/top-up set must share light direction, perspective, material, saturation, contour sharpness, shadow style, and cinema polish.
- Generate or collect multiple candidates, then reject candidates that read as low-resolution, flat SVG, plain emoji, generic office UI, or game-loot props. Do not accept the first attractive output if it misses the product tone.
- Verify icons at mobile UI sizes such as 20px, 24px, and 28px against the actual dark cinema background. Large preview quality is not enough.
- Preserve source sheets or originals, cropped transparent PNG/WebP files, source/license notes, and intended usage. Flutter must reuse the same asset keys instead of substituting similar icons later.
- content-list pages such as playback history, favorites, recommendations, and My List must use real poster-like image assets; do not fake drama posters with abstract gradients, blobs, or CSS-only placeholders

Formal product execution rule:

- card layout, visual effects, and entry shape must strictly follow formal shipped-product standards
- text strategy, card layout, color strategy, and visual effects strategy are all non-negotiable hard standards
- future design iterations may only tighten alignment with these four standards and must not drift away from them
- these hard standards are reusable across pages as style constraints, not as a forced page template

## Layout Pattern For This App

Default mobile app order for account-oriented pages:

1. status bar / top breathing space
2. account or hero identity block
3. content atmosphere or lightweight content memory
4. VIP module
5. wallet module
6. high-frequency entry list
7. bottom navigation

If a page is account-centric, the first screen must answer:

- who am I
- what premium offer is in front of me
- how much balance do I have
- what can I do next

## Me Page Rules

When designing the `Me` page:

- default first-screen state is guest mode unless the user asks for logged-in mode
- show `Visitor`, guest ID, and `Log in`
- do not gray out major functions in guest mode
- keep `VIP` and `My Wallet` visually above the utility list
- the list must feel like core product navigation, not plain settings rows
- do not place `About Us` or `Version` on the home screen if PRD says they live under Configuration
- keep utility entries as list rows when the source product pattern is row-based; do not convert them to square cards unless the user explicitly asks for a redesign
- remove construction-language copy, design-commentary copy, and explanatory filler unless the PRD explicitly requires those words
- treat all visible text as final product UI; do not leave placeholder-style, pitch-style, or workshop-style wording on the page
- avoid stuffing VIP or wallet with descriptive helper microcopy and feature chips when the source pattern is cleaner and more compact
- if no direct screenshot exists, infer the page from the established short-drama product style of this project rather than falling back to generic mobile UI patterns

The `Me` page must feel more like:

- personal control hub for a drama app
- entertainment-side home for identity, assets, and quick drama-oriented actions

and less like:

- a settings page with a profile header
- a dark utility panel

For this page specifically, the final effect must read as:

- compact and high-density
- visually premium but restrained
- monetization-first without looking pushy
- closer to a successful short-drama app account page than to a generic mobile settings page

## Prompt Template

Use a prompt structure like this:

1. screen type and device
2. target state
3. exact modules to include
4. exact modules to exclude
5. product rules
6. visual direction
7. anti-pattern warnings

Example structure:

```text
Create a mobile Android-style Me page for a short drama app.
Only generate the main home screen of the personal center.
Default state must be guest mode.

Include:
- account area with Visitor, guest ID, Log in
- VIP card
- wallet card with Details and Top-up
- list entries: My List, Languages, Configuration, FeedBack
- bottom navigation with Me selected

Exclude:
- login page
- subpages
- About Us row
- Version row

Product rules:
- guest users can still access major features
- VIP and wallet must feel high-value
- page must feel like a real entertainment app

Visual direction:
- warm dark cinematic background
- amber/gold accents
- polished rounded cards
- stronger entertainment feel than generic tool UI

Avoid:
- purple bias
- dashboard card mosaic
- flat utility-only settings look
- poster-only concept art with weak product structure
```

## Anti-Patterns

Reject results that look like:

- generic SaaS settings dashboard
- a marketing landing page instead of app UI
- a plain list with decorative header only
- too much empty space and too little product signal
- weak VIP and weak wallet presence
- overly futuristic concept art that ignores usability
- a dark tool panel that could belong to admin, finance, or device settings
- a page without strong content atmosphere
- oversized low-density blocks that feel like prototype scaffolding
- explanatory filler copy that reads like a draft rather than product UI
- any copy that sounds like the designer is narrating the interface instead of the product speaking for itself
- converting clearly row-based navigation into grid tiles without product evidence

## Output Expectations

When delivering a design:

- state which docs were used
- state which page state was chosen
- state which market-inspired principles were applied
- keep the design within confirmed PRD boundaries

When multiple generators are available:

- keep the prompt consistent across tools for fair comparison
- if outputs are weak, improve the prompt and design direction before retrying
- do not accept weak generator output as final just because a tool returned something

## Recommended Companion Asset

For reusable wording and design constraints, see:

- `docs/design-review/ui-prompt-system/micro-drama-app-ui-prompt-system.md`
