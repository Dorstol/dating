import { ref } from 'vue'

export function useTelegram() {
  const webApp = window.Telegram?.WebApp
  const isTelegram = ref(!!webApp)

  function getInitData() {
    return webApp?.initData || ''
  }

  function ready() {
    webApp?.ready()
  }

  function expand() {
    webApp?.expand()
  }

  function close() {
    webApp?.close()
  }

  function setHeaderColor(color) {
    webApp?.setHeaderColor(color)
  }

  return {
    webApp,
    isTelegram,
    getInitData,
    ready,
    expand,
    close,
    setHeaderColor,
  }
}
