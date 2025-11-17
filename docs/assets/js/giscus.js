const giscusPlugin = (hook, vm) => {
  hook.ready(() => {
    // Move Giscus container to content area.
    const content = document.querySelector('.content')
    const giscusContainer = document.querySelector(`.giscus`)
    if (content && giscusContainer) {
      content.appendChild(giscusContainer)
    }
    // Initial theme setup.
    const iframe = document.querySelector('.giscus-frame')
    const themeToggle = document.getElementById('docsify-darklight-theme')
    if (iframe && themeToggle) {
      toggleGiscusTheme(themeToggle, iframe)
    }
  })
  hook.doneEach(() => {
    // Update `term` parameter.
    const iframe = document.querySelector('.giscus-frame')
    if (iframe) {
      setupGiscusTerm(iframe)
      // Add theme toggle event.
      const themeToggle = document.getElementById('docsify-darklight-theme')
      if (themeToggle) {
        themeToggle.addEventListener('click', () => toggleGiscusTheme(themeToggle, iframe))
      }
    }
  })
}

const setupGiscusTerm = (iframe) => {
  // Replace `term` parameter in iframe src.
  const src = iframe.getAttribute('src')
  let term = decodeURIComponent(location.hash).replace('#', '')
  if (!term) term = '/'
  const newSrc = src.replace(/term=[^&]*/, `term=${encodeURIComponent(term)}`)
  iframe.setAttribute('src', newSrc)
}

const toggleGiscusTheme = (toggle, iframe) => {
  // Check if dark mode is enabled.
  const isDark = toggle.getAttribute('data-link-title') === 'dark'
  const theme = isDark ? 'dark_dimmed' : 'light'
  // Replace `theme` parameter in iframe src.
  const src = iframe.getAttribute('src')
  const newSrc = src.replace(/theme=[^&]*/, `theme=${theme}`)
  iframe.setAttribute('src', newSrc)
}

$docsify.plugins.push(giscusPlugin)
