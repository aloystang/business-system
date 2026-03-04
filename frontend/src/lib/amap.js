export const DEFAULT_AMAP_CENTER = [106.5516, 29.563]

export function loadAmapSdk(key) {
  if (!key) {
    return Promise.reject(new Error('未配置高德地图 Key'))
  }
  if (window.AMap) {
    return Promise.resolve(window.AMap)
  }
  return new Promise((resolve, reject) => {
    const securityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE
    if (securityJsCode) {
      window._AMapSecurityConfig = { securityJsCode }
    }
    const existed = document.querySelector('script[data-amap-sdk="1"]')
    if (existed) {
      existed.addEventListener('load', () => resolve(window.AMap))
      existed.addEventListener('error', () => reject(new Error('高德地图 SDK 加载失败')))
      return
    }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(
      key
    )}&plugin=AMap.Scale,AMap.MarkerClusterer,AMap.Geocoder`
    script.async = true
    script.dataset.amapSdk = '1'
    script.onload = () => {
      if (window.AMap) resolve(window.AMap)
      else reject(new Error('高德地图 SDK 初始化失败'))
    }
    script.onerror = () => reject(new Error('高德地图 SDK 加载失败'))
    document.body.appendChild(script)
  })
}
