import { Scene, SceneProps } from "../types";
import { BigNumber } from "./BigNumber";
import { BulletList } from "./BulletList";
import { ClipScene } from "./ClipScene";
import { ImageKenBurns } from "./ImageKenBurns";
import { ScreenshotFocus } from "./ScreenshotFocus";
import { TitleCard } from "./TitleCard";

/** Registry: visual.component → Komponente. Neue Szenentypen hier eintragen. */
export const SCENES: Record<string, React.FC<SceneProps>> = {
  TitleCard,
  ImageKenBurns,
  ImageWithCaption: ImageKenBurns,
  ClipScene,
  BulletList,
  BigNumber,
  ScreenshotFocus,
};

export const resolveScene = (scene: Scene): React.FC<SceneProps> => {
  const named = scene.visual.component && SCENES[scene.visual.component];
  if (named) return named;
  switch (scene.visual.kind) {
    case "clip":
    case "hyperframes":
    case "tesseract":
      return ClipScene;
    case "image":
      return ImageKenBurns;
    default:
      return TitleCard;
  }
};
