// Reference: https://github.com/iPeng6/docsify-sidebar-collapse
// Modified by MaxXing.

const scrollBarSyncPlugin = (hook, vm) => {
  hook.doneEach(() => {
    const activeNode = getActiveNode()
    syncScrollTop(activeNode)
  })
}

const syncScrollTop = (activeNode) => {
  if (activeNode) {
    const curTop = activeNode.getBoundingClientRect().top
    if (curTop > window.innerHeight) {
      activeNode.scrollIntoView()
    }
  }
}

const getActiveNode = () => {
  let node = document.querySelector('.sidebar-nav .active')
  if (!node) {
    const curLink = document.querySelector(
      `.sidebar-nav a[href="${decodeURIComponent(location.hash).replace(
        / /gi,
        '%20'
      )}"]`
    )
    node = findTagParent(curLink, 'LI', 2)
    if (node) {
      node.classList.add('active')
    }
  }
  return node
}

const findTagParent = (curNode, tagName, level) => {
  if (curNode && curNode.tagName === tagName) return curNode
  let l = 0
  while (curNode) {
    l++
    if (l > level) return
    if (curNode.parentNode.tagName === tagName) {
      return curNode.parentNode
    }
    curNode = curNode.parentNode
  }
}

const registerPlugin = () => {
  $docsify.plugins.push(scrollBarSyncPlugin)
}

registerPlugin()
