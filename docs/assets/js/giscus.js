const giscusPlugin = (hook, vm) => {
  hook.ready(() => {
    // Move giscus container to content area.
    const content = document.querySelector('.content')
    const giscusContainer = document.querySelector(`.giscus`)
    if (content && giscusContainer) {
      content.appendChild(giscusContainer)
    }
    // Add theme toggle event.
    const themeToggle = document.getElementById('docsify-darklight-theme')
    if (themeToggle) {
      themeToggle.addEventListener('click', () => toggleGiscusTheme(themeToggle))
      toggleGiscusTheme(themeToggle)
    }
  })
}

const toggleGiscusTheme = (toggle) => {
  const iframe = document.querySelector('.giscus-frame')
  if (iframe) {
    // Check if dark mode is enabled.
    const isDark = toggle.getAttribute('data-link-title') === 'dark'
    const theme = isDark ? 'dark_dimmed' : 'light'
    // Replace `theme` parameter in iframe src.
    const src = iframe.getAttribute('src')
    const newSrc = src.replace(
      /theme=[^&]*/,
      `theme=${theme}`
    )
    iframe.setAttribute('src', newSrc)
  }
}

$docsify.plugins.push(giscusPlugin)
