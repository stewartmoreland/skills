# dotLottie State Machines Reference (v2.0)

State machines turn a passive animation file into an interactive component.
They are JSON files in `s/` that describe **states** (each tied to an animation
or acting as a global override), **transitions** between states, **guards** that
gate transitions, **actions** that fire on transitions or interactions, and
**inputs** that hold the variables driving the whole thing.

Spec: https://dotlottie.io/spec/2.0/#state-machines

## When To Use One

Reach for a state machine when the animation needs to *react*:

- A toggle that flips between two states (on/off, mute/unmute, expand/collapse)
- A button that plays a "press" animation on click and returns to idle
- A loader that has distinct loading/success/error visuals
- A star rating that fills based on a numeric input
- A hover-to-play element that pauses on pointer exit
- Any UI with conditional branching driven by user events

For "play this thing once and stop" or "loop this forever," skip the state
machine — just configure looping in the player or use a single animation.

## Top-Level Structure

```json
{
  "initial": "idle",
  "states": [ /* State objects */ ],
  "interactions": [ /* Interaction objects, optional */ ],
  "inputs": [ /* Input variable objects, optional */ ]
}
```

| Field          | Required | Type     | Notes |
| -------------- | -------- | -------- | ----- |
| `initial`      | yes      | string   | Name of the state to enter on start. Must match one of the `states[].name`. |
| `states`       | yes      | array    | At least one state. Each is either a `PlaybackState` or `GlobalState`. |
| `interactions` | no       | array    | Top-level event handlers. Apply across the whole machine. |
| `inputs`       | no       | array    | Variables (numeric, string, boolean, event) the machine can read and write. |

## States

### PlaybackState

The common case — a state tied to an animation, with playback options.

```json
{
  "name": "idle",
  "type": "PlaybackState",
  "animation": "loader",
  "loop": true,
  "autoplay": true,
  "mode": "Forward",
  "speed": 1.0,
  "transitions": [ /* Transition objects */ ]
}
```

| Field             | Required | Type     | Notes |
| ----------------- | -------- | -------- | ----- |
| `name`            | yes      | string   | Unique state identifier. |
| `type`            | yes      | string   | `"PlaybackState"`. |
| `animation`       | yes      | string   | Animation ID from the manifest. |
| `loop`            | no       | boolean  | Loop the animation while in this state. |
| `loopCount`       | no       | integer (≥1) | Limit loops. Ignored when `loop` is false. Omit for infinite. |
| `autoplay`        | no       | boolean  | Start playing on enter. |
| `final`           | no       | boolean  | Terminal state — no transitions out. |
| `mode`            | no       | string   | `Forward` (default) / `Reverse` / `Bounce` / `ReverseBounce`. |
| `speed`           | no       | number   | Playback multiplier (1.0 = normal, 2.0 = 2×, 0.5 = ½×). |
| `segment`         | no       | string   | Lottie marker name; play only that range. Falls back to full range if missing. |
| `backgroundColor` | no       | u32      | u32 RGBA, same encoding as manifest `background`. |
| `entryActions`    | no       | array    | Actions fired on entering this state. |
| `exitActions`     | no       | array    | Actions fired on leaving this state. |
| `transitions`     | yes      | array    | How this state leaves itself. |

> **Mode `Bounce`** — animation plays forward to the end, then reverses back
> to the start. One bounce = one loop iteration for `loopCount` purposes.

### GlobalState

A pseudo-state whose transitions are checked **before** the current state's
transitions, every tick. Use it for "always-available" actions like a reset
button or a global error path.

```json
{
  "name": "global",
  "type": "GlobalState",
  "transitions": [
    {
      "type": "Transition",
      "toState": "error",
      "guards": [{ "type": "Event", "inputName": "onError" }]
    }
  ]
}
```

GlobalStates have no `animation` field — they don't drive playback. They only
exist to host transitions that should be evaluated regardless of where the
machine currently is.

## Transitions

Two types: immediate and tweened. Both live inside a state's `transitions`
array. The machine evaluates them in declaration order; the first whose guards
all pass is taken. Guards on a single transition are ANDed together.

### Immediate Transition

```json
{
  "type": "Transition",
  "toState": "active",
  "guards": [
    { "type": "Boolean", "inputName": "isActive", "conditionType": "Equal", "compareTo": true }
  ]
}
```

| Field     | Required | Notes |
| --------- | -------- | ----- |
| `type`    | yes      | `"Transition"`. |
| `toState` | yes      | Name of the destination state. |
| `guards`  | no       | All must pass for the transition to fire. Omit for an unconditional fall-through. |

### Tweened Transition

An interpolated change — the renderer crossfades between the two states'
visuals over a duration. Useful for smooth visual transitions between two
distinct animations.

```json
{
  "type": "Tweened",
  "toState": "expanded",
  "duration": 0.3,
  "easing": [0.4, 0.0, 0.2, 1.0],
  "guards": [{ "type": "Event", "inputName": "onExpand" }]
}
```

`easing` is a 4-tuple cubic bezier `[x1, y1, x2, y2]` — the same control
points you'd use in CSS or D3. This is **not** the same as the per-keyframe
tangent format used inside Lottie animations and theme rules; tween easing
has its own simpler representation.

> **During a tween:** input changes that would trigger another transition
> are blocked. The destination state is finalized only when the tween
> completes, then its entry actions run.

### Guardless Fallback Pattern

```json
"transitions": [
  { "type": "Transition", "toState": "success", "guards": [/* event */] },
  { "type": "Transition", "toState": "error",   "guards": [/* event */] },
  { "type": "Transition", "toState": "idle" }
]
```

Guards are evaluated in order; the unguarded final entry catches everything else.

## Guards

Four guard types: `Numeric`, `String`, `Boolean`, `Event`. All read from an
input variable declared in `inputs`.

### Numeric Guard

```json
{
  "type": "Numeric",
  "inputName": "progress",
  "conditionType": "GreaterThanOrEqual",
  "compareTo": 100
}
```

`conditionType` is one of `Equal`, `NotEqual`, `GreaterThan`,
`GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`.

`compareTo` is a number, OR a string prefixed with `$` referencing another
numeric input, e.g. `"$threshold"`. The `$` syntax lets you parameterize
comparisons at runtime.

### String Guard

```json
{
  "type": "String",
  "inputName": "mode",
  "conditionType": "Equal",
  "compareTo": "active"
}
```

`conditionType` is `Equal` or `NotEqual`. Comparisons are case-sensitive.
`compareTo` accepts the `$inputName` reference syntax.

### Boolean Guard

```json
{
  "type": "Boolean",
  "inputName": "isMuted",
  "conditionType": "Equal",
  "compareTo": true
}
```

`conditionType` is `Equal` or `NotEqual`. `compareTo` is a literal boolean
or a `$inputName` reference (note: schema accepts string here for the reference
case).

### Event Guard

```json
{
  "type": "Event",
  "inputName": "onClick"
}
```

Events are edge-triggered — they fire once when consumed by the pipeline,
then clear. The guard matches whenever the named event was fired since the
last pipeline run.

> The machine has a single "current event" slot. Rapid-fire events overwrite
> previous ones before processing — there is no queue. Last-one-wins behavior.

## Actions

Actions execute on transitions (entry/exit) or as the body of an interaction.
The action list is long; here are the buckets:

### Theme & UI

- **`SetTheme`** — switch the active theme. `value` is the theme ID, or a
  `$inputName` reference.
  ```json
  { "type": "SetTheme", "value": "dark" }
  ```

- **`OpenUrl`** — open an external URL. `target` follows HTML semantics
  (`_blank`, `_self`, `_parent`, `_top`, `_unfencedTop`).
  ```json
  { "type": "OpenUrl", "url": "https://example.com", "target": "_blank" }
  ```

### Input Mutation

- **`Increment`** / **`Decrement`** — adjust a numeric input. `value` defaults
  to 1; can be a number or `$inputName` reference.
  ```json
  { "type": "Increment", "inputName": "score", "value": 10 }
  ```

- **`SetNumeric`** / **`SetString`** / **`SetBoolean`** — overwrite an input
  with a literal value.

- **`Toggle`** — flip a boolean input.
  ```json
  { "type": "Toggle", "inputName": "isMuted" }
  ```

- **`Reset`** — restore an input to its initial value.
  ```json
  { "type": "Reset", "inputName": "score" }
  ```

### Animation Control

- **`SetFrame`** — jump to a specific frame on the active animation.
  ```json
  { "type": "SetFrame", "value": 30 }
  ```
- **`SetProgress`** — jump to a normalized 0–1 position.
  ```json
  { "type": "SetProgress", "value": 0.5 }
  ```

Both accept `$inputName` references in `value`. They operate on the
*currently active* animation — there is no per-animation targeting.

### Events

- **`Fire`** — fire an event input (consumed by Event guards).
  ```json
  { "type": "Fire", "inputName": "onComplete" }
  ```
- **`FireCustomEvent`** — emit an event to the **host application** (not the
  machine itself). For wiring into React handlers, Android callbacks, etc.
  ```json
  { "type": "FireCustomEvent", "value": "rating_submitted" }
  ```

### When Actions Run

- **Exit actions** fire just before the state changes (or before a tween starts).
- **Entry actions** fire just after entering — except for tweened transitions,
  where they wait for the tween to complete.
- Actions are synchronous and run in array order.

## Interactions

Interactions are top-level event handlers — they're not part of any single
state's transition list, they fire whenever the trigger occurs (subject to
`layerName` filtering).

Most produce an `actions` array; some also require `stateName` or `layerName`.

| Type             | Trigger                                                |
| ---------------- | ------------------------------------------------------ |
| `Click`          | Click / tap on the animation (or a specific layer)     |
| `PointerDown`    | Pointer pressed                                        |
| `PointerUp`      | Pointer released                                       |
| `PointerEnter`   | Pointer enters layer area                              |
| `PointerExit`    | Pointer leaves layer area                              |
| `PointerMove`    | Pointer moves over area                                |
| `OnComplete`     | A specific state's animation playback finishes         |
| `OnLoopComplete` | A specific state's loop iteration finishes             |

Example — click anywhere to toggle a boolean:

```json
{
  "type": "Click",
  "actions": [{ "type": "Toggle", "inputName": "isOn" }]
}
```

Example — click a specific layer named "Button":

```json
{
  "type": "Click",
  "layerName": "Button",
  "actions": [{ "type": "Fire", "inputName": "onButtonClick" }]
}
```

Layer name matching is exact and case-sensitive. The layer must exist in the
animation by that `nm` string.

### OnComplete vs OnLoopComplete

- `OnComplete` fires once when the animation reaches its true end. For looped
  animations, it only fires after the last `loopCount` iteration. For infinite
  loops, it **never fires**.
- `OnLoopComplete` fires every iteration, including the last one. For infinite
  loops, it keeps firing. In `Bounce` mode, a "loop" = full forward + reverse cycle.

Both require `stateName`:

```json
{
  "type": "OnComplete",
  "stateName": "intro",
  "actions": [{ "type": "Fire", "inputName": "introFinished" }]
}
```

## Inputs

Inputs are the machine's variables. Four types — each has a `name` and
`value` (initial value). Names must be unique across the machine.

```json
"inputs": [
  { "type": "Numeric", "name": "progress", "value": 0 },
  { "type": "Boolean", "name": "isMuted",  "value": false },
  { "type": "String",  "name": "mode",     "value": "idle" },
  { "type": "Event",   "name": "onClick" }
]
```

Event inputs don't have a `value` — they're triggered, not stored.

Hosts (web/iOS/Android) can read and write inputs at runtime via the player
SDK, which is how external state (e.g. a Redux store, a Compose state holder)
syncs with the machine.

## Worked Example: Click Toggle

A button with two visual states. Tap to toggle between them. The animation
file is a single Lottie with both visuals on separate layers, controlled by
opacity slots — but you could equally use two animations and two PlaybackStates.

`s/toggle.json`:

```json
{
  "initial": "off",
  "states": [
    {
      "name": "off",
      "type": "PlaybackState",
      "animation": "button",
      "autoplay": true,
      "loop": false,
      "segment": "off_state",
      "transitions": [
        {
          "type": "Transition",
          "toState": "on",
          "guards": [
            { "type": "Boolean", "inputName": "isOn", "conditionType": "Equal", "compareTo": true }
          ]
        }
      ]
    },
    {
      "name": "on",
      "type": "PlaybackState",
      "animation": "button",
      "autoplay": true,
      "loop": false,
      "segment": "on_state",
      "transitions": [
        {
          "type": "Transition",
          "toState": "off",
          "guards": [
            { "type": "Boolean", "inputName": "isOn", "conditionType": "Equal", "compareTo": false }
          ]
        }
      ]
    }
  ],
  "interactions": [
    {
      "type": "Click",
      "actions": [{ "type": "Toggle", "inputName": "isOn" }]
    }
  ],
  "inputs": [
    { "type": "Boolean", "name": "isOn", "value": false }
  ]
}
```

## Worked Example: Hover To Play

A logo that plays only while hovered, freezing on pointer exit.

```json
{
  "initial": "idle",
  "states": [
    {
      "name": "idle",
      "type": "PlaybackState",
      "animation": "logo",
      "autoplay": false,
      "transitions": [
        {
          "type": "Transition",
          "toState": "playing",
          "guards": [{ "type": "Event", "inputName": "onHover" }]
        }
      ]
    },
    {
      "name": "playing",
      "type": "PlaybackState",
      "animation": "logo",
      "autoplay": true,
      "loop": true,
      "transitions": [
        {
          "type": "Transition",
          "toState": "idle",
          "guards": [{ "type": "Event", "inputName": "onUnhover" }]
        }
      ]
    }
  ],
  "interactions": [
    { "type": "PointerEnter", "actions": [{ "type": "Fire", "inputName": "onHover" }] },
    { "type": "PointerExit",  "actions": [{ "type": "Fire", "inputName": "onUnhover" }] }
  ],
  "inputs": [
    { "type": "Event", "name": "onHover" },
    { "type": "Event", "name": "onUnhover" }
  ]
}
```

## Worked Example: Loader → Success / Error

A loader that branches on completion based on a host-provided status.

```json
{
  "initial": "loading",
  "states": [
    {
      "name": "loading",
      "type": "PlaybackState",
      "animation": "spinner",
      "loop": true,
      "autoplay": true,
      "transitions": [
        {
          "type": "Tweened",
          "toState": "success",
          "duration": 0.3,
          "easing": [0.4, 0.0, 0.2, 1.0],
          "guards": [{ "type": "String", "inputName": "status", "conditionType": "Equal", "compareTo": "success" }]
        },
        {
          "type": "Tweened",
          "toState": "error",
          "duration": 0.3,
          "easing": [0.4, 0.0, 0.2, 1.0],
          "guards": [{ "type": "String", "inputName": "status", "conditionType": "Equal", "compareTo": "error" }]
        }
      ]
    },
    {
      "name": "success",
      "type": "PlaybackState",
      "animation": "check",
      "autoplay": true,
      "loop": false,
      "final": true,
      "transitions": []
    },
    {
      "name": "error",
      "type": "PlaybackState",
      "animation": "cross",
      "autoplay": true,
      "loop": false,
      "final": true,
      "transitions": []
    }
  ],
  "inputs": [
    { "type": "String", "name": "status", "value": "pending" }
  ]
}
```

The host sets `status` to `"success"` or `"error"` via the player SDK, the
loader tweens to the matching terminal state, and the machine stops.

## Common Mistakes

**`initial` references a missing state name** — typo or copy-paste error.
Loaders will fail to start.

**Transition's `toState` references a missing state** — silent failure path,
hard to debug. Validate target names against the `states` array.

**Wrong `conditionType` casing** — `"equals"` (lowercase) instead of `"Equal"`.
The spec is case-sensitive on enum values. (The non-normative example in the
spec actually uses `"equals"` in places — that's an error in the spec example;
the schema requires `Equal`, `NotEqual`, etc.)

**Looking for an animation by name instead of ID** — the `animation` field on
a state is the manifest's animation `id` (which is the file stem), not the
Lottie animation's internal `nm` field.

**Mixing tangent formats** — keyframe tangents inside theme rules use the
`{x, y}` object form. Tweened-transition easing uses the 4-tuple
`[x1, y1, x2, y2]` form. They're not interchangeable.

**Forgetting GlobalState precedence** — a poorly-scoped GlobalState transition
can pre-empt every other state's transitions. Use guards to restrict when it
fires (typically an Event guard tied to a specific input).

**Event guard but never firing the event** — Event inputs need a `Fire`
action or an SDK call to actually fire. They don't fire themselves on input
changes the way Boolean guards re-evaluate.

**Final state with transitions** — `final: true` and a populated
`transitions` array contradict each other. The machine treats the state as
terminal; the transitions are dead code.

**Wrong target on `OpenUrl`** — `target` must be one of the five allowed
values; arbitrary frame names won't validate.

**No interaction wired to drive an Event input** — an Event guard guards a
transition, but the event has to come from somewhere. Either an interaction's
`Fire` action or the host SDK must produce it.

**SetFrame/SetProgress on no active animation** — if a state has no
`animation` (i.e. a GlobalState), these actions have undefined behavior. Keep
animation-control actions inside PlaybackStates.

## Validation Checklist

Before packaging, confirm:

- [ ] `initial` matches a state in `states`
- [ ] Every `toState` in every transition matches a state name
- [ ] Every `animation` field references an animation ID in the manifest
- [ ] Every `inputName` in guards/actions matches an entry in `inputs`
- [ ] Every input `name` is unique
- [ ] `conditionType` values use exact spec casing (`Equal`, not `equals`)
- [ ] Tweened transitions have both `duration` and `easing`
- [ ] `easing` is a 4-number array, not an object
- [ ] No state is marked `final: true` AND has non-empty transitions
- [ ] Every `OnComplete`/`OnLoopComplete` `stateName` matches a state
- [ ] Layer names referenced in interactions match `nm` fields in animations
- [ ] `loopCount` only present when `loop: true`

The `validate_dotlottie.py` script enforces all of these.
