# Cinematic camera — frame-driven moves that make a scene feel directed

A static, dead-center frame is the #1 reason a scene reads as "a slide" instead of "a shot". The
fastest upgrade to perceived production value is a **motivated, eased camera move**. This applies
to true 3D (R3F `<ThreeCanvas>` — move the actual camera) and to 2D (Skia/DOM — move a *virtual*
camera = a transform on the world group). Everything here obeys the one law: the camera is a pure
function of `useCurrentFrame()`, never `useFrame`/clock.

---

## The move vocabulary (and what each one is *for*)

Pick the move from the intent, not the other way around.

| Move | What changes | Use it to… |
| --- | --- | --- |
| **Push-in / pull-out (dolly)** | camera distance along view axis | build intensity (in) or reveal context (out). The slow push-in is the default "make a static frame alive" move. |
| **Truck / pedestal** | lateral / vertical position | follow a subject, reveal a neighbor, reframe |
| **Pan / tilt** | yaw / pitch rotation (or moving lookAt target) | scan across a space, connect two focal points, reveal up/down |
| **Orbit (arc)** | camera travels an arc around the subject | show a 3D object *is* 3D; hero reveal |
| **Zoom (FOV)** | field of view | emphasis without moving; pairs with dolly |
| **Dolly-zoom (vertigo)** | dolly one way + zoom the other, subject stays same size | dramatic unease / "whoa" beat. Use rarely. |
| **Rack focus (DoF)** | focal plane | shift attention between near and far elements |
| **Roll / Dutch** | roll around view axis | tension, energy, stylized beats. Sparingly. |
| **Handheld** | tiny seeded noise on rotation/position | organic, documentary energy. Very subtle or it reads as broken. |
| **Parallax** | layers move at different rates | manufacture depth in 2D and 2.5D |

## The cinematography rules (this is the "director" part)

1. **Every move is motivated.** It reveals, follows, emphasizes, or transitions. A move with no
   reason reads as restlessness. When in doubt, hold the frame.
2. **Ease and settle.** Use the house ease `Easing.bezier(0.16, 1, 0.3, 1)`, clamp both ends, and
   let the move *come to rest* — a camera that drifts forever is nauseating. Exception: an
   intentional ultra-slow constant push (a few % over the whole scene) to keep a "static" frame alive.
2b. **One dominant move per beat.** Combine at most a primary + a tiny secondary (e.g. push-in +
   faint handheld). Stacking pan+tilt+zoom+roll at once reads as chaos, not cinema.
3. **Lead the eye, respect the focal point.** The frame after the move should still land the eye on
   the beat's focal point (see `story-craft`). Compose with margin; don't move the subject into a
   corner unless that's the point.
4. **Motivated by depth.** Camera moves only pay off when there's depth to reveal — parallax layers,
   3D geometry, foreground occluders. A move across a flat plane does nothing.
5. **Continuity across beats.** Match the camera's end state to the next beat's start (or cut
   deliberately). The persistent-map / persistent-stage pattern (`MondayFoundations`, `EngraStage`)
   makes a continuous through-shot possible — drive the camera off the **absolute** frame there.
6. **Rack focus / DoF for attention, not decoration.** Pull focus to hand off attention; don't blur
   for vibes.

---

## 3D — drive the real camera (R3F `<ThreeCanvas>`)

The `camera` prop on `<ThreeCanvas>` sets only the *initial* state. To animate, grab the camera with
`useThree` inside the canvas and set it from the frame, then call `updateProjectionMatrix()` when you
change `fov`/`zoom`. Mutating in the render body is deterministic in Remotion (the component
re-renders once per frame). Never use `useFrame`/`THREE.Clock`.

```tsx
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";

const EASE = { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16,1,0.3,1) } as const;

/** Frame-driven cinematic rig: orbit + push-in + a touch of FOV, easing to rest. */
const CameraRig: React.FC = () => {
  const frame = useCurrentFrame();
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;

  const angle  = interpolate(frame, [0, 220], [-0.45, 0.15], EASE);   // gentle orbit, settles
  const radius = interpolate(frame, [0, 220], [6.5, 4.2], EASE);      // push in
  const fov    = interpolate(frame, [0, 220], [52, 40], EASE);        // mild zoom
  const target = new THREE.Vector3(0, 0, 0);                          // can also be frame-driven

  camera.position.set(Math.sin(angle) * radius, 0.7, Math.cos(angle) * radius);
  camera.lookAt(target);
  camera.fov = fov;
  camera.updateProjectionMatrix();
  return null;
};

export const CinematicScene: React.FC = () => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} gl={{ alpha: true, antialias: true }} camera={{ position: [0,0.7,6.5], fov: 52 }}>
      <CameraRig />
      {/* ...additive neon meshes; reuse VectorCloud3D material recipe... */}
    </ThreeCanvas>
  );
};
```

- **Pan/tilt** = animate the `target` you `lookAt` (move it in x for pan, y for tilt) instead of, or
  in addition to, the position — usually cleaner than setting `camera.rotation` directly.
- **Dolly-zoom (vertigo):** move `radius` and `fov` in *opposite* directions so the subject keeps
  its screen size while the background warps. Tune by eye.
- **Roll/Dutch:** `camera.rotation.z = interpolate(frame, …)` after `lookAt` (lookAt resets it, so set
  roll last), or set `camera.up` to a tilted vector.
- **Handheld:** add `mulberry32`-seeded low-amplitude noise to position/target (deterministic across
  workers — never `Math.random()`).
- **Depth of field:** real DoF needs postprocessing (heavy offline). Fake it: render a blurred
  far-layer + sharp near-layer, or use additive bloom falloff with distance. Rack focus = crossfade
  the two layers' blur on frame.
- Camera reuse/hygiene as in `react-three-fiber` → `remotion-r3f.md` + `design-and-aesthetics.md`.

## 2D — drive a *virtual* camera (Skia / DOM)

There is no camera; you move the world. Wrap everything in one group and apply a frame-driven
transform + origin. The repo's reference is `cameraForFrame()` in
`src/scenes/scribe/draw-helpers.ts` (zoom-to-focus on a moving point, then a gentle reveal pull-out).

```tsx
// Skia: transform the stage Group. Pan = translate, zoom = scale (around `origin`), Dutch = rotate.
const scale = interpolate(frame, [0, 200], [1, 1.12], { extrapolateLeft:"clamp", extrapolateRight:"clamp", easing: Easing.bezier(0.16,1,0.3,1) }); // slow push-in
const tx = (CENTER.x - focus.x) * (scale - 1);   // keep `focus` centered as you zoom
const ty = (CENTER.y - focus.y) * (scale - 1);
<Group transform={[{ translateX: tx }, { translateY: ty }, { scale }]} origin={vec(focus.x, focus.y)}>
  {/* scene */}
</Group>
```

- **DOM equivalent:** a wrapping `<div style={{ transform: `translate(${tx}px,${ty}px) scale(${s}) rotate(${r}deg)`, transformOrigin: `${ox}px ${oy}px` }}>`. (A frame-computed `transform` value is fine — that's not a CSS *transition*; never use `transition`/`@keyframes`.)
- **Parallax:** give each depth layer its own translate rate (`vx * frame * depthFactor`). Background
  moves least, foreground most.
- **2.5D push-in:** scale background + foreground at slightly different rates for a faux-dolly.

---

## How to apply this in the workflow

In step 2 (visual concept) decide the **one** camera move per beat from its intent, and whether the
scene even has the depth to justify it. In step 4 (build) implement it as a rig (3D) or a stage
transform (2D), driven by the absolute frame if the camera must persist across beats. In step 5
add a camera line to the review: *is the move motivated, eased, settled, and does the final framing
still land the focal point?* If a move doesn't earn its place, cut it — restraint reads as
confidence.
