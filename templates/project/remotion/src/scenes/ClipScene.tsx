import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { SceneProps } from "../types";
import { Caption } from "./Caption";
import { ImageKenBurns } from "./ImageKenBurns";

/**
 * LTX-Clip oder vorgerenderte Hyperframes-/Tesseract-Szene, stumm (Sprache liegt drüber).
 * props.playbackRate (< 1) setzt tools/comfy_assets.py, wenn die Szene länger ist als der
 * nutzbare Teil des Clips – LTX-2.3 blendet die letzten ~2 s nach Schwarz ab.
 */
export const ClipScene: React.FC<SceneProps> = (p) => {
  const src = p.scene.assets?.render ?? p.scene.assets?.clip;
  if (!src) return <ImageKenBurns {...p} />; // Fallback: Startbild, solange der Clip fehlt
  const props = (p.scene.visual.props ?? {}) as { headline?: string; playbackRate?: number };
  const caption = props.headline ?? p.scene.onScreenText?.[0];
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(src)}
        muted
        playbackRate={props.playbackRate ?? 1}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      {caption ? <Caption text={caption} palette={p.palette} /> : null}
    </AbsoluteFill>
  );
};
