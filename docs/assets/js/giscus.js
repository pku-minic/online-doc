const giscusPlugin = (hook, vm) => {
  hook.ready(() => {
    const content = document.querySelector('.content')
    const giscusContainer = document.querySelector(`.giscus`)
    if (content && giscusContainer) {
      content.appendChild(giscusContainer)
    }
  })
}

$docsify.plugins.push(giscusPlugin)
