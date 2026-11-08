import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { resolveScene } from "./scenes";
import { DEFAULT_PALETTE, Palette, sceneSeconds, Storyboard } from "./types";

export type ExplainerProps = { storyboard: Storyboard | null };

const FADE = 10; // Frames Überblendung am Szenenanfang

const SceneShell: React.FC<{ children: React.ReactNode; fade: boolean }> = ({ children, fade }) => {
  const frame = useCurrentFrame();
  const opacity = fade ? interpolate(frame, [0, FADE], [0, 1], { extrapolateRight: "clamp" }) : 1;
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

export const Explainer: React.FC<ExplainerProps> = ({ storyboard }) => {
  const { fps, durationInFrames } = useVideoConfig();
  if (!storyboard) return <AbsoluteFill style={{ background: "black" }} />;

  const palette: Palette = { ...DEFAULT_PALETTE, ...storyboard.style.palette };
  const font = storyboard.style.font ?? "Inter";
  const music = storyboard.music;

  let from = 0;
  return (
    <AbsoluteFill style={{ background: palette.background, fontFamily: `${font}, Helvetica, Arial, sans-serif` }}>
      {storyboard.scenes.map((scene) => {
        const frames = Math.round(sceneSeconds(scene) * fps);
        const start = from;
        from += frames;
        const Component = resolveScene(scene);
        return (
          <Sequence key={scene.id} from={start} durationInFrames={frames} name={`${scene.id} ${scene.beat ?? ""}`}>
            <SceneShell fade={scene.transition !== "cut"}>
              <Component scene={scene} palette={palette} font={font} />
            </SceneShell>
            {scene.assets?.audio ? <Audio src={staticFile(scene.assets.audio)} /> : null}
          </Sequence>
        );
      })}
      {music?.enabled && music.file ? (
        <Audio
          src={staticFile(music.file)}
          loop
          volume={(f) =>
            (music.volume ?? 0.14) *
            interpolate(f, [0, fps, durationInFrames - fps, durationInFrames], [0, 1, 1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}
    </AbsoluteFill>
  );
};
