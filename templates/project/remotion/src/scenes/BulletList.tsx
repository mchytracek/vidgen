import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneProps } from "../types";

/** Punkte erscheinen nacheinander, gleichmäßig über die Sprechdauer verteilt. */
export const BulletList: React.FC<SceneProps> = ({ scene, palette }) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const items = scene.onScreenText ?? [];
  const speech = Math.round((scene.audioDuration ?? durationInFrames / fps) * fps);
  const step = items.length ? speech / (items.length + 0.2) : 0;

  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: width * 0.1, gap: 36, color: palette.foreground }}>
      {items.map((text, i) => {
        const s = spring({ frame: frame - (4 + Math.round(step * i)), fps, config: { damping: 200 } });
        return (
          <div
            key={text}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 32,
              fontSize: Math.round(width * 0.04),
              fontWeight: 700,
              opacity: s,
              transform: `translateX(${interpolate(s, [0, 1], [-60, 0])}px)`,
            }}
          >
            <span
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                background: palette.accent,
                color: palette.background,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 34,
              }}
            >
              {i + 1}
            </span>
            {text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
