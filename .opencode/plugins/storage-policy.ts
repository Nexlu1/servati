import type { Plugin } from "@opencode-ai/plugin"

const root = String.raw`F:\RIG_LAB\10_TEMP\USER\opencode\servati-codex`
const temp = String.raw`${root}\temp`
const cache = String.raw`${root}\cache`
const build = String.raw`${root}\build`
const logs = String.raw`${root}\logs`

export default (async () => ({
  "shell.env": async (_input, output) => {
    Object.assign(output.env, {
      TEMP: temp,
      TMP: temp,
      TMPDIR: temp,
      XDG_CACHE_HOME: cache,
      NPM_CONFIG_CACHE: String.raw`${cache}\npm`,
      YARN_CACHE_FOLDER: String.raw`${cache}\yarn`,
      BUN_INSTALL_CACHE_DIR: String.raw`${cache}\bun`,
      PIP_CACHE_DIR: String.raw`${cache}\pip`,
      UV_CACHE_DIR: String.raw`${cache}\uv`,
      PYTHONPYCACHEPREFIX: String.raw`${cache}\python-bytecode`,
      CARGO_HOME: String.raw`${cache}\cargo`,
      CARGO_TARGET_DIR: String.raw`${build}\cargo-target`,
      SCCACHE_DIR: String.raw`${cache}\sccache`,
      GOCACHE: String.raw`${cache}\go-build`,
      GOMODCACHE: String.raw`${cache}\go-mod`,
      GRADLE_USER_HOME: String.raw`${cache}\gradle`,
      NUGET_PACKAGES: String.raw`${cache}\nuget`,
      HF_HOME: String.raw`${cache}\huggingface`,
      HUGGINGFACE_HUB_CACHE: String.raw`${cache}\huggingface\hub`,
      TRANSFORMERS_CACHE: String.raw`${cache}\huggingface\transformers`,
      TORCH_HOME: String.raw`${cache}\torch`,
      PLAYWRIGHT_BROWSERS_PATH: String.raw`${cache}\playwright`,
      CYPRESS_CACHE_FOLDER: String.raw`${cache}\cypress`,
      SERVATI_BUILD_ROOT: build,
      SERVATI_LOG_DIR: logs,
      SERVATI_TEMP_ROOT: temp,
    })
  },
})) satisfies Plugin
