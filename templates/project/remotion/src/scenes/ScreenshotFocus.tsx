import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Palette, SceneProps } from "../types";
import { Caption } from "./Caption";
import { TitleCard } from "./TitleCard";

/**
 * Produkt-Screenshot mit geführtem Blick: Kamerafahrt auf einen Bildausschnitt,
 * Markierung (Rahmen oder Spotlight), animierter Mauszeiger mit Klick, Schritt-Badge.
 *
 * Bild: scene.assets.image (z. B. "screens/02-dashboard.png").
 * Koordinaten sind Anteile der Bildgröße (0–1), Ursprung oben links –
 * Raster zum Ablesen: `python3 tools/screens.py grid`.
 *
 * visual.props:
 *   focus      {x,y,w,h, at?, label?, zoom?, click?} oder Liste davon (mehrere Klicks
 *              auf demselben Bildschirm). at = Startzeit in s (Default 0.5 bzw. gleichmäßig verteilt),
 *              click = {x,y} Klickpunkt (Default: Mitte des Ausschnitts), false = kein Cursor.
 *   highlight  "box" (Default) | "spotlight" | "none"
 *   cursor     true (Default) | false
 *   zoom       maximale Vergrößerung (Default 2.2; 1 = keine Kamerafahrt)
 *   step/steps Schritt-Badge „2/5“ – oder badge: "Freier Text"
 *   headline   Bauchbinde (Default: onScreenText[0]); focus[i].label ersetzt sie ab diesem Fokus
 *   framed     true (Default): Screenshot mit Rand/Schatten auf Palettenhintergrund;
 *              false: bildfüllend (Seitenverhältnis muss zum Videoformat passen)
 */
type Rect = { x: number; y: number; w: number; h: number };
type Focus = Rect & { at?: number; label?: string; zoom?: number; click?: { x: number; y: number } | false };
type Props = {
  focus?: Focus | Focus[];
  highlight?: "box" | "spotlight" | "none";
  cursor?: boolean;
  zoom?: number;
  step?: number;
  steps?: number;
  badge?: string;
  headline?: string;
  framed?: boolean;
};

const MOVE = 0.9; // s Kamerafahrt
const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);
const ease = Easing.inOut(Easing.cubic);

/**
 * Kamera für einen Fokus: Vergrößerung und Bildpunkt, der in die Mitte rückt.
 * cover = Anteil des Frames, den das (ungezoomte) Bild füllt – der Bildausschnitt
 * wird so begrenzt, dass beim Zoom kein leerer Rand neben dem Screenshot erscheint.
 */
const cameraFor = (f: Focus, maxZoom: number, cover: number, margin = 0) => {
  const s = clamp(f.zoom ?? 0.5 / Math.max(f.w, f.h, 0.01), 1, maxZoom);
  const half = 0.5 / (s * cover); // halbe sichtbare Breite in Bildanteilen
  // margin: gerahmt darf die Kamera etwas über die Bildkante hinaus, damit Elemente am Rand
  // (z. B. Buttons ganz rechts) nicht angeschnitten werden.
  const pos = (c: number) => (half >= 0.5 ? 0.5 : clamp(c, half - margin, 1 - half + margin));
  return { s, cx: pos(f.x + f.w / 2), cy: pos(f.y + f.h / 2) };
};

export const ScreenshotFocus: React.FC<SceneProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const src = p.scene.assets?.image;
  if (!src) return <TitleCard {...p} />; // Platzhalter, solange der Screenshot fehlt

  const props = (p.scene.visual.props ?? {}) as Props;
  const framed = props.framed ?? true;
  const maxZoom = props.zoom ?? 2.2;
  const highlight = props.highlight ?? "box";
  const sceneSec = durationInFrames / fps;
  const t = frame / fps;

  const raw = props.focus ? (Array.isArray(props.focus) ? props.focus : [props.focus]) : [];
  const foci = raw.map((f, i) => ({
    ...f,
    at: f.at ?? (raw.length === 1 ? 0.5 : 0.4 + (i * (sceneSec - 0.8)) / raw.length),
  }));

  // aktueller Fokus + Kamera (Übergang vom vorherigen Zustand)
  let idx = -1;
  foci.forEach((f, i) => {
    if (t >= f.at) idx = i;
  });
  // gerahmt füllt ein Screenshot im Videoformat ~84 % des Frames (maxH = 0.84 · Höhe)
  const cover = framed ? 0.84 : 1;
  const edge = framed ? 0.04 : 0;
  const prevCam = idx <= 0 ? { s: 1, cx: 0.5, cy: 0.5 } : cameraFor(foci[idx - 1], maxZoom, cover, edge);
  const cam = idx < 0 ? prevCam : (() => {
    const target = cameraFor(foci[idx], maxZoom, cover, edge);
    const k = ease(clamp((t - foci[idx].at) / MOVE, 0, 1));
    return {
      s: prevCam.s + (target.s - prevCam.s) * k,
      cx: prevCam.cx + (target.cx - prevCam.cx) * k,
      cy: prevCam.cy + (target.cy - prevCam.cy) * k,
    };
  })();
  const cur = idx >= 0 ? foci[idx] : null;
  const since = cur ? t - cur.at : 0;

  // Markierung erscheint, wenn die Kamera fast angekommen ist
  const hl = cur ? interpolate(since, [MOVE * 0.7, MOVE + 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;

  // Cursor: gleitet vom vorherigen Klickpunkt (bzw. Bildmitte) zum Klickpunkt, Klick danach
  const clickOf = (f: Focus | null) =>
    f && f.click !== false ? f.click ?? { x: f.x + f.w / 2, y: f.y + f.h / 2 } : null;
  const showCursor = (props.cursor ?? true) && cur && cur.click !== false;
  const to = clickOf(cur);
  const from = clickOf(idx > 0 ? foci[idx - 1] : null) ?? { x: 0.5, y: 0.62 };
  const ck = ease(clamp((since - 0.2) / (MOVE + 0.1), 0, 1));
  const cursorPos = to ? { x: from.x + (to.x - from.x) * ck, y: from.y + (to.y - from.y) * ck } : null;
  const clickT = since - (MOVE + 0.35);
  const press = clickT > 0 && clickT < 0.18 ? 0.85 : 1;
  const ripple = clamp(clickT / 0.5, 0, 1);

  const caption = cur?.label ?? props.headline ?? p.scene.onScreenText?.[0];
  const badge = props.badge ?? (props.step ? `${props.step}${props.steps ? `/${props.steps}` : ""}` : undefined);
  const enter = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  const maxW = framed ? width * 0.88 : width;
  const maxH = framed ? height * 0.84 : height;
  const inv = 1 / cam.s; // Strichstärken/Cursor gegen den Zoom ausgleichen

  return (
    <AbsoluteFill style={{ background: p.palette.background, overflow: "hidden" }}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            position: "relative",
            lineHeight: 0,
            transformOrigin: "50% 50%",
            transform: `scale(${cam.s * interpolate(enter, [0, 1], [0.97, 1])}) translate(${(0.5 - cam.cx) * 100}%, ${(0.5 - cam.cy) * 100}%)`,
            opacity: enter,
            borderRadius: framed ? 14 : 0,
            boxShadow: framed ? "0 30px 80px rgba(0,0,0,0.45)" : undefined,
            overflow: highlight === "spotlight" ? "hidden" : "visible",
          }}
        >
          <Img
            src={staticFile(src)}
            style={{ display: "block", maxWidth: maxW, maxHeight: maxH, borderRadius: framed ? 14 : 0 }}
          />
          {cur && highlight !== "none" ? (
            <div
              style={{
                position: "absolute",
                left: `${cur.x * 100}%`,
                top: `${cur.y * 100}%`,
                width: `${cur.w * 100}%`,
                height: `${cur.h * 100}%`,
                borderRadius: 10 * inv,
                opacity: hl,
                ...(highlight === "spotlight"
                  ? { boxShadow: `0 0 0 ${Math.max(width, height) * 2}px rgba(0,0,0,${0.55 * hl})` }
                  : {
                      border: `${5 * inv}px solid ${p.palette.accent}`,
                      boxShadow: `0 0 ${24 * inv}px ${p.palette.accent}99`,
                      transform: `scale(${interpolate(hl, [0, 1], [1.12, 1])})`,
                    }),
              }}
            />
          ) : null}
          {showCursor && cursorPos ? (
            <Cursor x={cursorPos.x} y={cursorPos.y} size={34 * inv} press={press} ripple={ripple} palette={p.palette}
              visible={clamp((since - 0.1) / 0.25, 0, 1)} />
          ) : null}
        </div>
      </AbsoluteFill>
      {badge ? <StepBadge text={badge} palette={p.palette} /> : null}
      {caption ? <Caption key={caption} text={caption} palette={p.palette} /> : null}
    </AbsoluteFill>
  );
};

const Cursor: React.FC<{ x: number; y: number; size: number; press: number; ripple: number; visible: number; palette: Palette }> = ({
  x, y, size, press, ripple, visible, palette,
}) => (
  <div style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, opacity: visible, lineHeight: 0 }}>
    {ripple > 0 && ripple < 1 ? (
      <div
        style={{
          position: "absolute",
          left: -size * 1.2 * ripple,
          top: -size * 1.2 * ripple,
          width: size * 2.4 * ripple,
          height: size * 2.4 * ripple,
          borderRadius: "50%",
          border: `${size * 0.12}px solid ${palette.accent}`,
          opacity: 1 - ripple,
        }}
      />
    ) : null}
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ transform: `scale(${press})`, transformOrigin: "0 0", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.5))" }}>
      <path d="M2 1 L2 20 L7 15.5 L10.5 23 L14 21.5 L10.5 14 L17 14 Z" fill="white" stroke="black" strokeWidth={1.4} strokeLinejoin="round" />
    </svg>
  </div>
);

const StepBadge: React.FC<{ text: string; palette: Palette }> = ({ text, palette }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const o = interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        top: width * 0.04,
        left: width * 0.05,
        padding: `${width * 0.006}px ${width * 0.016}px`,
        borderRadius: 999,
        background: palette.accent,
        color: palette.background,
        fontSize: Math.round(width * 0.024),
        fontWeight: 800,
        fontVariantNumeric: "tabular-nums",
        opacity: o,
      }}
    >
      {text}
    </div>
  );
};
