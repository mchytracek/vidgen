import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Palette } from "../types";

/** Untertitel-/Headline-Band im unteren Drittel. */
export const Caption: React.FC<{ text: string; palette: Palette; delay?: number }> = ({ text, palette, delay = 8 }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        position: "absolute",
        left: width * 0.06,
        bottom: width * 0.05,
        maxWidth: "70%",
        padding: "18px 30px",
        background: palette.background + "E6",
        color: palette.foreground,
        borderLeft: `8px solid ${palette.accent}`,
        fontSize: Math.round(width * 0.03),
        fontWeight: 700,
        lineHeight: 1.2,
        opacity: enter,
        transform: `translateY(${interpolate(enter, [0, 1], [30, 0])}px)`,
      }}
    >
      {text}
    </div>
  );
};
