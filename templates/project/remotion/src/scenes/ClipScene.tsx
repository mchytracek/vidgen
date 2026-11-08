import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { SceneProps } from "../types";
import { Caption } from "./Caption";
import { ImageKenBurns } from "./ImageKenBurns";

/** LTX-Clip oder vorgerenderte Hyperframes-/Tesseract-Szene, stumm (Sprache liegt drüber). */
export const ClipScene: React.FC<SceneProps> = (p) => {
  const src = p.scene.assets?.render ?? p.scene.assets?.clip;
  if (!src) return <ImageKenBurns {...p} />; // Fallback: Startbild, solange der Clip fehlt
  const caption = (p.scene.visual.props as { headline?: string } | undefined)?.headline ?? p.scene.onScreenText?.[0];
  return (
    <AbsoluteFill>
      <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      {caption ? <Caption text={caption} palette={p.palette} /> : null}
    </AbsoluteFill>
  );
};
