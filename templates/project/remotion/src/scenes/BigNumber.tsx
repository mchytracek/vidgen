import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneProps } from "../types";

/** Große Zahl, die hochzählt – für Kennzahlen und Größenordnungen. */
export const BigNumber: React.FC<SceneProps> = ({ scene, palette }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const p = (scene.visual.props ?? {}) as { value?: number; prefix?: string; suffix?: string; label?: string; decimals?: number };
  const value = p.value ?? 0;
  const t = interpolate(frame, [0, fps * 1.2], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const shown = (value * t).toFixed(p.decimals ?? 0);
  const labelOpacity = interpolate(frame, [fps * 0.8, fps * 1.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: palette.foreground }}>
      <div style={{ fontSize: Math.round(width * 0.14), fontWeight: 900, color: palette.accent, fontVariantNumeric: "tabular-nums" }}>
        {p.prefix ?? ""}
        {shown}
        {p.suffix ?? ""}
      </div>
      {p.label ? (
        <div style={{ fontSize: Math.round(width * 0.03), color: palette.muted, opacity: labelOpacity }}>{p.label}</div>
      ) : null}
    </AbsoluteFill>
  );
};
