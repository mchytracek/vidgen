import { CalculateMetadataFunction, Composition, staticFile } from "remotion";
import { Explainer, ExplainerProps } from "./Explainer";
import { sceneSeconds, Storyboard } from "./types";

// storyboard.json wird von `python3 tools/storyboard.py sync` nach assets/ kopiert.
const calculateMetadata: CalculateMetadataFunction<ExplainerProps> = async () => {
  const res = await fetch(staticFile("storyboard.json"));
  const storyboard = (await res.json()) as Storyboard;
  const { fps, width, height } = storyboard.format;
  const seconds = storyboard.scenes.reduce((sum, s) => sum + sceneSeconds(s), 0);
  return {
    durationInFrames: Math.max(1, Math.round(seconds * fps)),
    fps,
    width,
    height,
    props: { storyboard },
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Explainer"
    component={Explainer}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ storyboard: null }}
    calculateMetadata={calculateMetadata}
  />
);
