import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneProps } from "../types";

export const TitleCard: React.FC<SceneProps> = ({ scene, palette }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const props = (scene.visual.props ?? {}) as { headline?: string; subline?: string };
  const headline = props.headline ?? scene.onScreenText?.[0] ?? "";
  const subline = props.subline ?? scene.onScreenText?.[1];
  const a = spring({ frame, fps, config: { damping: 200 } });
  const b = spring({ frame: frame - 12, fps, config: { damping: 200 } });
  const bar = interpolate(frame, [6, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: width * 0.08, color: palette.foreground }}>
      <div style={{ width: 160 * bar, height: 10, background: palette.accent, marginBottom: 36 }} />
      <div
        style={{
          fontSize: Math.round(width * 0.058),
          fontWeight: 800,
          lineHeight: 1.05,
          opacity: a,
          transform: `translateY(${interpolate(a, [0, 1], [40, 0])}px)`,
        }}
      >
        {headline}
      </div>
      {subline ? (
        <div style={{ marginTop: 28, fontSize: Math.round(width * 0.026), color: palette.muted, opacity: b }}>
          {subline}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
