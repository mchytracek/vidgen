import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneProps } from "../types";
import { Caption } from "./Caption";
import { TitleCard } from "./TitleCard";

/** ComfyUI-Standbild mit langsamem Zoom (1.0 → 1.08) und optionaler Headline. */
export const ImageKenBurns: React.FC<SceneProps> = (p) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const src = p.scene.assets?.image;
  if (!src) return <TitleCard {...p} />; // Platzhalter, solange das Bild fehlt

  const props = (p.scene.visual.props ?? {}) as { headline?: string; zoomFrom?: number; zoomTo?: number };
  const scale = interpolate(frame, [0, durationInFrames], [props.zoomFrom ?? 1, props.zoomTo ?? 1.08]);
  const caption = props.headline ?? p.scene.onScreenText?.[0];

  return (
    <AbsoluteFill>
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }} />
      {caption ? <Caption text={caption} palette={p.palette} /> : null}
    </AbsoluteFill>
  );
};
