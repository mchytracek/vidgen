import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Palette, SceneProps } from "../types";
import { Caption } from "./Caption";

/**
 * Dokument-Eingang als Code-Grafik (kein generiertes Bild).
 *
 * visual.props:
 *   variant   "question" (Default): PDF-Karte erscheint, Fragezeichen pulsiert einmal
 *             "mail": PDF wandert in einen Umschlag, der ins Postfach fliegt (+1)
 *   fileName  Dateiname unter der PDF-Karte
 *   inboxLabel Beschriftung des Postfachs (Default "Import-Postfach")
 *   headline  Bauchbinde (Default: onScreenText[0])
 */
type Props = { variant?: "question" | "mail"; fileName?: string; inboxLabel?: string; headline?: string };

const PDF_RED = "#D9364F";
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.inOut(Easing.cubic);

export const PdfCard: React.FC<{ palette: Palette; scale: number; fileName?: string; showName: number }> = ({
  palette,
  scale,
  fileName,
  showName,
}) => {
  const w = 220 * scale;
  const h = 290 * scale;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width={w} height={h} viewBox="0 0 220 290">
        <defs>
          <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="8" stdDeviation="10" floodColor="#1D2D3E" floodOpacity="0.18" />
          </filter>
        </defs>
        <path d="M10 10 H160 L210 60 V280 H10 Z" fill="#FFFFFF" filter="url(#sh)" />
        <path d="M160 10 V60 H210" fill="#E4E8EC" />
        {[90, 115, 140, 165, 190].map((y, i) => (
          <rect key={y} x={34} y={y} width={i === 4 ? 90 : 150} height={10} rx={5} fill="#DDE3E9" />
        ))}
        <rect x={34} y={215} width={86} height={44} rx={8} fill={PDF_RED} />
        <text x={77} y={246} textAnchor="middle" fontSize={26} fontWeight={800} fill="#FFFFFF" fontFamily="Inter, sans-serif">
          PDF
        </text>
      </svg>
      {fileName ? (
        <div
          style={{
            marginTop: 18 * scale,
            fontSize: 30 * scale,
            fontWeight: 600,
            color: palette.foreground,
            opacity: showName,
            whiteSpace: "nowrap",
          }}
        >
          {fileName}
        </div>
      ) : null}
    </div>
  );
};

const Envelope: React.FC<{ palette: Palette; size: number; flap: number }> = ({ palette, size, flap }) => (
  <svg width={size} height={size * 0.68} viewBox="0 0 300 204" style={{ overflow: "visible" }}>
    <rect x={4} y={4} width={292} height={196} rx={14} fill="#FFFFFF" stroke={palette.accent} strokeWidth={8} />
    <path d="M10 196 L130 104 M290 196 L170 104" stroke={palette.accent} strokeWidth={6} fill="none" opacity={0.5} />
    {/* Klappe: flap 0 = offen (nach oben), 1 = geschlossen */}
    <g style={{ transformOrigin: "150px 6px", transform: `scaleY(${interpolate(flap, [0, 1], [-1, 1])})` }}>
      <path d="M6 6 L150 120 L294 6 Z" fill="#EAF3FC" stroke={palette.accent} strokeWidth={8} strokeLinejoin="round" />
    </g>
  </svg>
);

export const Inbox: React.FC<{ palette: Palette; size: number; label: string; badge: number; bump: number }> = ({
  palette,
  size,
  label,
  badge,
  bump,
}) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${1 + 0.06 * bump})` }}>
    <div style={{ position: "relative" }}>
      <svg width={size} height={size * 0.8} viewBox="0 0 300 240">
        <path d="M20 110 L70 20 H230 L280 110 V220 H20 Z" fill="#FFFFFF" stroke={palette.foreground} strokeWidth={8} strokeLinejoin="round" />
        <path d="M20 110 H100 L120 150 H180 L200 110 H280" fill="none" stroke={palette.foreground} strokeWidth={8} strokeLinejoin="round" />
      </svg>
      <div
        style={{
          position: "absolute",
          right: -size * 0.06,
          top: -size * 0.06,
          width: size * 0.26,
          height: size * 0.26,
          borderRadius: "50%",
          background: palette.accent,
          color: "#FFFFFF",
          fontWeight: 800,
          fontSize: size * 0.12,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${badge})`,
        }}
      >
        +1
      </div>
    </div>
    <div style={{ marginTop: size * 0.08, fontSize: size * 0.11, fontWeight: 700, color: palette.foreground }}>{label}</div>
  </div>
);

export const DocumentIntake: React.FC<SceneProps> = ({ scene, palette }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const props = (scene.visual.props ?? {}) as Props;
  const headline = props.headline ?? scene.onScreenText?.[0];
  const t = frame / fps;
  const k = width / 1920;

  if ((props.variant ?? "question") === "question") {
    const enter = spring({ frame, fps, config: { damping: 14, mass: 0.8 } });
    const q = spring({ frame: frame - Math.round(1.4 * fps), fps, config: { damping: 9 } });
    const float = Math.sin(t * 2) * 6 * k;
    return (
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: height * 0.12 }}>
        <div style={{ position: "relative", transform: `translateY(${interpolate(enter, [0, 1], [80 * k, 0]) + float}px) scale(${interpolate(enter, [0, 1], [0.85, 1])})`, opacity: enter }}>
          <PdfCard palette={palette} scale={1.25 * k} fileName={props.fileName} showName={interpolate(t, [0.5, 1.0], [0, 1], clamp)} />
          <div
            style={{
              position: "absolute",
              right: -110 * k,
              top: -60 * k,
              fontSize: 190 * k,
              fontWeight: 800,
              color: palette.accent,
              opacity: interpolate(q, [0, 0.3], [0, 1], clamp),
              transform: `scale(${q}) rotate(${interpolate(q, [0, 1], [-20, 8])}deg)`,
            }}
          >
            ?
          </div>
        </div>
        {headline ? <Caption text={headline} palette={palette} delay={Math.round(0.6 * fps)} /> : null}
      </AbsoluteFill>
    );
  }

  // variant "mail" – Zeitplan in Sekunden, passend zu ~3 s Sprechtext
  const into = interpolate(t, [0.05, 0.55], [0, 1], { ...clamp, easing: ease }); // PDF sinkt in Umschlag
  const flap = interpolate(t, [0.55, 0.8], [0, 1], { ...clamp, easing: ease });
  const fly = interpolate(t, [0.85, 1.5], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const landed = Math.max(0, t - 1.5);
  const bump = landed > 0 ? Math.exp(-landed * 6) * Math.sin(landed * 30) : 0;
  const badge = spring({ frame: frame - Math.round(1.5 * fps), fps, config: { damping: 10 } });

  const envX = -width * 0.18; // relativ zur Mitte
  const inboxX = width * 0.24;
  const ex = interpolate(fly, [0, 1], [envX, inboxX]);
  const ey = -Math.sin(fly * Math.PI) * height * 0.12 + interpolate(fly, [0, 1], [0, -height * 0.02]);
  const es = interpolate(fly, [0, 1], [1, 0.35]);
  const envOpacity = interpolate(fly, [0.85, 1], [1, 0], clamp);
  const envSize = 360 * k;
  const pdfH = 290 * 0.9 * k;
  const pdfTop = interpolate(into, [0, 1], [-300 * k, 6 * k]);
  const clampPct = (v: number) => Math.min(100, Math.max(0, v));

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: height * 0.1 }}>
      {/* Postfach rechts */}
      <div style={{ position: "absolute", left: width / 2 + inboxX - 130 * k, top: height * 0.5 - 170 * k, opacity: interpolate(t, [0, 0.4], [0, 1], clamp) }}>
        <Inbox palette={palette} size={260 * k} label={props.inboxLabel ?? "Import-Postfach"} badge={badge} bump={bump} />
      </div>
      {/* Umschlag + PDF links */}
      <div
        style={{
          position: "absolute",
          left: width / 2 + ex - envSize / 2,
          top: height * 0.5 - 40 * k + ey,
          width: envSize,
          transform: `scale(${es}) rotate(${interpolate(fly, [0, 0.5, 1], [0, -8, 4])}deg)`,
          opacity: envOpacity,
        }}
      >
        <div style={{ position: "relative" }}>
          <Envelope palette={palette} size={envSize} flap={flap} />
        </div>
        {/* PDF vor dem Umschlag, unterhalb der Oberkante abgeschnitten: rutscht hinein */}
        <div
          style={{
            position: "absolute",
            left: envSize / 2 - 110 * 0.9 * k,
            top: pdfTop,
            
            zIndex: 2,
            clipPath: `inset(0 0 ${clampPct(((pdfH - Math.max(0, -pdfTop)) / pdfH) * 100)}% 0)`,
          }}
        >
          <PdfCard palette={palette} scale={0.9 * k} showName={0} />
        </div>
      </div>
      {headline ? <Caption text={headline} palette={palette} delay={Math.round(0.3 * fps)} /> : null}
    </AbsoluteFill>
  );
};
