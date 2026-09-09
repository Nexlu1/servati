(() => {
  const setup = async () => {
    const panel = document.querySelector(".codex-random-modes")
    if (!panel || panel.dataset.ready === "true") return
    panel.dataset.ready = "true"

    const index = await fetchData
    const records = Object.values(index).filter((page) => {
      const tags = Array.isArray(page.tags) ? page.tags : []
      return page.slug && !tags.includes("navigation")
    })
    const visitRandom = (requiredTag) => {
      const candidates = requiredTag
        ? records.filter((page) => page.tags.includes(requiredTag))
        : records
      if (candidates.length === 0) return
      const target = candidates[Math.floor(Math.random() * candidates.length)]
      const base = panel.dataset.basePath || "/"
      window.location.assign(`${window.location.origin}${base}${target.slug}.html`)
    }

    panel.querySelectorAll("button[data-random-tag]").forEach((button) => {
      button.addEventListener("click", () => visitRandom(button.dataset.randomTag))
    })
    panel.querySelectorAll("button[data-random-select]").forEach((button) => {
      button.addEventListener("click", () => {
        const select = panel.querySelector(button.dataset.randomSelect)
        if (select) visitRandom(select.value)
      })
    })
  }

  setup()
  document.addEventListener("nav", setup)
  document.addEventListener("render", setup)
})()
