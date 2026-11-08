export type Palette = {
  background: string;
  foreground: string;
  accent: string;
  muted: string;
};

export type Scene = {
  id: string;
  beat?: string;
  narration: string;
  visual: {
    kind: "image" | "clip" | "code" | "hyperframes" | "tesseract";
    prompt?: string | null;
    motionPrompt?: string | null;
    component?: string;
    props?: Record<string, unknown>;
  };
  onScreenText?: string[];
  transition?: "cut" | "fade" | "slide" | "wipe";
  duration?: number;
  audioDuration?: number;
  assets?: { image?: string; clip?: string; audio?: string; render?: string };
};

export type Storyboard = {
  title: string;
  format: { width: number; height: number; fps: number };
  style: { palette?: Partial<Palette>; font?: string };
  music?: { enabled?: boolean; volume?: number; file?: string | null };
  scenes: Scene[];
};

export type SceneProps = {
  scene: Scene;
  palette: Palette;
  font: string;
};

export const DEFAULT_PALETTE: Palette = {
  background: "#14213D",
  foreground: "#F7F3E9",
  accent: "#FF6B5E",
  muted: "#8A94A6",
};

/** Szenendauer in Sekunden; Fallback-Schätzung aus der Wortzahl, solange kein Audio existiert. */
export const sceneSeconds = (s: Scene): number =>
  s.duration ?? Math.max(2.5, s.narration.split(/\s+/).length / 2.3 + 0.4);
