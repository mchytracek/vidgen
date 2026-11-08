import { Config } from "@remotion/cli/config";

// Assets (Bilder, Clips, Audio, storyboard.json) liegen eine Ebene höher in assets/.
Config.setPublicDir("../assets");
Config.setEntryPoint("src/index.ts");
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
